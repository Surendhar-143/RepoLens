import uuid
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.database.models import User, Repository, Conversation, ConversationMessage, AISetting
from app.core.exceptions import NotFoundError
from app.core.config import settings

from repolens.embeddings.providers import OpenAIEmbeddingProvider, SentenceTransformersProvider
from repolens.search.hybrid_searcher import HybridSearcher
from repolens.ai.providers import OpenAIProvider, OllamaProvider, LocalMockAIProvider
from repolens.ai.prompt_builder import RAGPromptBuilder

router = APIRouter(prefix="/ai", tags=["Grounded AI Repository Assistant"])
logger = logging.getLogger("repolens.routes.ai")

# Setup default retrieval tools (hybrid searcher)
openai_key = settings.OPENAI_API_KEY if hasattr(settings, "OPENAI_API_KEY") else None
search_embed = OpenAIEmbeddingProvider(api_key=openai_key) if openai_key else SentenceTransformersProvider()
searcher = HybridSearcher(
    qdrant_host=settings.QDRANT_HOST,
    qdrant_port=settings.QDRANT_PORT,
    qdrant_api_key=settings.QDRANT_API_KEY,
    embedding_provider=search_embed
)


class ChatRequest(BaseModel := object):
    pass # To avoid typing schemas conflicts, we read fields from Body direct


@router.post("/chat", status_code=status.HTTP_200_OK)
async def perform_rag_chat(
    repository_id: uuid.UUID = Body(...),
    conversation_id: Optional[uuid.UUID] = Body(None),
    message: str = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grounded codebase Q&A assistant streaming tokens completions in Server-Sent Events (SSE) format"""
    # Verify ownership
    repo_query = await db.execute(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == current_user.id,
            Repository.is_deleted == False
        )
    )
    repo = repo_query.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository")

    # Load or create conversation session
    if not conversation_id:
        conversation = Conversation(
            repository_id=repository_id,
            user_id=current_user.id,
            title=message[:40] + "..."
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conv_id = conversation.id
    else:
        conv_query = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        )
        conversation = conv_query.scalar_one_or_none()
        if not conversation:
            raise NotFoundError("Conversation")
        conv_id = conversation.id

    # Record User Message
    user_msg = ConversationMessage(
        conversation_id=conv_id,
        role="user",
        content=message,
        citations_json=[]
    )
    db.add(user_msg)
    await db.commit()

    # Load user AI settings
    settings_query = await db.execute(
        select(AISetting).where(AISetting.user_id == current_user.id)
    )
    user_settings = settings_query.scalar_one_or_none()
    provider_name = user_settings.provider if user_settings else "openai"
    temp = user_settings.temperature if user_settings else 0.2
    max_tok = user_settings.max_tokens if user_settings else 2048

    # Initialize Provider
    if provider_name == "openai" and openai_key:
        provider = OpenAIProvider(api_key=openai_key)
    elif provider_name == "ollama":
        provider = OllamaProvider()
    else:
        provider = LocalMockAIProvider()

    # Fetch Grounded Context
    context_hits = await RAGPromptBuilder.build_rag_context(db, str(repository_id), message, searcher)

    # Load conversation message history
    history_query = await db.execute(
        select(ConversationMessage.role, ConversationMessage.content)
        .where(ConversationMessage.conversation_id == conv_id)
        .order_by(ConversationMessage.created_at.asc())
    )
    conv_history = [{"role": row.role, "content": row.content} for row in history_query.fetchall()]

    # Construct Grounded Prompt
    prompt = RAGPromptBuilder.build_prompt(message, context_hits, conv_history)

    async def sse_generator():
        assistant_content = []
        try:
            # Stream tokens completions
            async for token in provider.generate_stream(
                prompt=prompt,
                system_prompt=RAGPromptBuilder.SYSTEM_INSTRUCTIONS,
                temperature=temp,
                max_tokens=max_tok
            ):
                assistant_content.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"
                
            # Compile citations from context hits
            citations = []
            for hit in context_hits:
                meta = hit.get("metadata", {})
                citations.append({
                    "title": hit["title"],
                    "file_id": hit["file_id"],
                    "file_path": hit["file_path"],
                    "type": hit["type"],
                    "score": hit["score"],
                    "line_start": meta.get("line_start"),
                    "line_end": meta.get("line_end")
                })
                
            # Save Assistant Response to DB
            full_response = "".join(assistant_content)
            assistant_msg = ConversationMessage(
                conversation_id=conv_id,
                role="assistant",
                content=full_response,
                citations_json=citations
            )
            
            # Setup session in generator thread context
            # We fetch a new DB connection since generator executes after main request returns
            from app.core.database import SessionLocal
            async with SessionLocal() as gen_db:
                gen_db.add(assistant_msg)
                await gen_db.commit()

            yield f"data: {json.dumps({'citations': citations, 'conversation_id': str(conv_id)})}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"SSE Chat streaming failed: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@router.get("/conversations", status_code=status.HTTP_200_OK)
async def list_conversations(
    repository_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List Q&A conversations for a repository"""
    query = (
        select(Conversation)
        .where(Conversation.repository_id == repository_id, Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
    )
    res = await db.execute(query)
    conversations = []
    for c in res.scalars().all():
        conversations.append({
            "id": str(c.id),
            "title": c.title,
            "created_at": c.created_at
        })
    return conversations


@router.get("/conversations/{id}", status_code=status.HTTP_200_OK)
async def get_conversation_messages(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve full messages history list and citations for a conversation"""
    conv_query = await db.execute(
        select(Conversation).where(Conversation.id == id, Conversation.user_id == current_user.id)
    )
    conv = conv_query.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation")

    msg_query = (
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == id)
        .order_by(ConversationMessage.created_at.asc())
    )
    res = await db.execute(msg_query)
    messages = []
    for msg in res.scalars().all():
        messages.append({
            "id": str(msg.id),
            "role": msg.role,
            "content": msg.content,
            "citations": msg.citations_json,
            "created_at": msg.created_at
        })
    return messages


@router.delete("/conversations/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Purge a conversation session and messages"""
    conv_query = await db.execute(
        select(Conversation).where(Conversation.id == id, Conversation.user_id == current_user.id)
    )
    conv = conv_query.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation")

    await db.execute(delete(ConversationMessage).where(ConversationMessage.conversation_id == id))
    await db.execute(delete(Conversation).where(Conversation.id == id))
    await db.commit()


@router.get("/providers", status_code=status.HTTP_200_OK)
async def list_available_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List LLM providers details"""
    settings_query = await db.execute(
        select(AISetting).where(AISetting.user_id == current_user.id)
    )
    user_settings = settings_query.scalar_one_or_none()
    active_provider = user_settings.provider if user_settings else "openai"
    temp = user_settings.temperature if user_settings else 0.2

    return {
        "active_provider": active_provider,
        "temperature": temp,
        "providers": [
            {"id": "openai", "name": "OpenAI GPT models (GPT-4o)", "configured": bool(openai_key)},
            {"id": "ollama", "name": "Ollama Local Service (llama3)", "configured": True},
            {"id": "mock", "name": "Local Hashed Grounded Mock Engine (Offline-ready)", "configured": True}
        ]
    }


@router.patch("/providers", status_code=status.HTTP_200_OK)
async def update_active_provider(
    provider: str = Body(...),
    temperature: float = Body(0.2),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Modify user active LLM provider configurations"""
    settings_query = await db.execute(
        select(AISetting).where(AISetting.user_id == current_user.id)
    )
    user_settings = settings_query.scalar_one_or_none()
    
    if user_settings:
        user_settings.provider = provider
        user_settings.temperature = temperature
    else:
        user_settings = AISetting(
            user_id=current_user.id,
            provider=provider,
            temperature=temperature
        )
        db.add(user_settings)

    await db.commit()
    return {"success": True, "provider": provider, "temperature": temperature}

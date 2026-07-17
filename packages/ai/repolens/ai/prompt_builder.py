from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from repolens.search.hybrid_searcher import HybridSearcher


class RAGPromptBuilder:
    SYSTEM_INSTRUCTIONS = """
You are RepoLens Assistant, an expert AI agent specializing in codebase intelligence and architecture explanations.

Your objective is to answer questions about this repository using ONLY the provided code chunks and knowledge graph metadata.

CRITICAL RULES:
1. Grounding: Rely strictly on the retrieved source code and architectural relationships. Do not speculate or invent files/symbols/APIs that are not in the context.
2. Insufficient Evidence: If the provided codebase context does not contain the answer, state: "I cannot find sufficient evidence in the codebase to answer this." Do not try to answer using prior training data.
3. Code Citations: When explaining code or referencing files/symbols, always cite the file path.
4. Response Format: Present your answer in clear, developer-friendly Markdown. Feel free to use tables or bullet lists.
5. No general knowledge: You should not answer generic questions unrelated to this codebase.
"""

    @classmethod
    async def build_rag_context(
        cls,
        db: AsyncSession,
        repository_id: str,
        query: str,
        searcher: HybridSearcher
    ) -> List[Dict[str, Any]]:
        """
        Use HybridSearcher to load the most relevant code and symbol segments.
        """
        return await searcher.search(db, repository_id, query, limit=5)

    @classmethod
    def build_prompt(
        cls,
        query: str,
        context_items: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Assemble the final prompt payload.
        """
        # Format Codebase Evidence Section
        evidence_blocks = []
        for idx, item in enumerate(context_items):
            meta = item.get("metadata", {})
            lines_info = f" (Lines {meta.get('line_start')}-{meta.get('line_end')})" if meta.get("line_start") else ""
            block = (
                f"--- EVIDENCE BLOCK {idx + 1} ---\n"
                f"File Path: {item['file_path']}{lines_info}\n"
                f"Entity Type: {item['type']}\n"
                f"Entity Name: {item['title']}\n"
                f"Source Content:\n{item['content_preview']}\n"
            )
            evidence_blocks.append(block)
            
        evidence_text = "\n".join(evidence_blocks) if evidence_blocks else "No relevant codebase context retrieved."

        # Format Conversation History (limit to last 6 messages to avoid context blowup)
        history_text = ""
        if conversation_history:
            history_blocks = []
            for msg in conversation_history[-6:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                history_blocks.append(f"{role}: {msg['content']}")
            history_text = "\n".join(history_blocks)
            
        prompt = (
            f"Codebase Evidence:\n"
            f"{evidence_text}\n\n"
        )
        
        if history_text:
            prompt += (
                f"Recent Conversation History:\n"
                f"{history_text}\n\n"
            )
            
        prompt += (
            f"User query: {query}\n"
            f"Grounded Response:"
        )
        return prompt

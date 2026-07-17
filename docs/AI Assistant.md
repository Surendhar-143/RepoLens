# AI Assistant & Grounded RAG Manual

This document specifies the AI Provider Layer, RAG Context Builder, Prompt Assembly, and navigable citations in RepoLens.

---

## 1. Provider Abstractions
RepoLens implements `LLMProviderInterface` in the `packages/ai` workspace:
* **OpenAI GPT Adapter**: Connects using Bearer tokens for GPT-4o-mini completions.
* **Ollama Local Adapter**: Pulls completions from local services on port `11434`.
* **Local Mock Adapter**: Scans RAG code files and creates structured, offline citations answers.

---

## 2. Grounded RAG Pipeline
To prevent hallucinations, RepoLens executes a strict retrieval step before sending requests to the LLM:
1. **User Question**: Input from chat interface.
2. **Hybrid Retrieval**: Runs Qdrant semantic search + PostgreSQL text index search.
3. **Graph CENTRALITY Enrichment**: Fetches degree weights from the knowledge graph.
4. **Context Construction**: Formats the top 5 chunks into structured markdown blocks.
5. **System Instructions**: Instructs models to output "I cannot find sufficient evidence in the codebase to answer this" if the chunks do not contain relevant facts.

---

## 3. SSE Streaming Completions
* Endpoints: `POST /api/v1/ai/chat`
* Payload structure yields Server-Sent Events:
  * Chunk token: `data: {"token": "..."}`
  * Citations map: `data: {"citations": [{"title": "...", "file_path": "..."}]}`
  * Terminal signal: `data: [DONE]`

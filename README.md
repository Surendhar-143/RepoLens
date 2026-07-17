# RepoLens

RepoLens is an AI-powered Codebase Intelligence Platform that transforms complex software repositories into interactive, searchable, and understandable knowledge. By combining deterministic static analysis (Abstract Syntax Trees, Knowledge Graphs) with LLM reasoning, RepoLens helps developers comprehend large codebases in minutes.

## Phase 0 Status: Foundation & Project Setup
This repository contains the foundation project setup including:
* **Apps Workspace**: FastAPI API backend (`apps/api`), ARQ background worker (`apps/worker`), and Vite + React 19 web frontend (`apps/web`).
* **Shared Packages**: Skeletal packages inside `/packages` (common, sdk, ai, analyzer, graph, search, documentation, embeddings, parsers).
* **Databases & Local Dev**: PostgreSQL, Redis, and Qdrant vector database container setups.
* **Orchestration**: Fully functional Docker Compose setup running the complete ecosystem.

---

## Architecture Overview

```text
                               ┌──────────────────────────┐
                               │      React Frontend      │
                               │        (Port 3000)       │
                               └─────────────┬────────────┘
                                             │
                                             ▼
                               ┌──────────────────────────┐
                               │      FastAPI Backend     │
                               │        (Port 8000)       │
                               └──────┬────────────┬──────┘
                                      │            │
                         ┌────────────┘            └────────────┐
                         ▼                                      ▼
               Relational Metadata                        Vector Storage
                (Postgres:5432)                           (Qdrant:6333)
                         │                                      │
                         └────────────┐            ┌────────────┘
                                      ▼            ▼
                                 Background Job Queue
                                     (Redis:6379)
                                          │
                                          ▼
                               ┌──────────────────────────┐
                               │        ARQ Worker        │
                               └──────────────────────────┘
```

---

## Quick Start

### Prerequisites
* Docker and Docker Compose installed.

### Launch local workspace
Run the following command in the project root to build and boot PostgreSQL, Redis, Qdrant, FastAPI backend, ARQ worker, and React frontend:

```bash
docker compose up --build
```

Once running:
* **Frontend Panel**: [http://localhost:3000](http://localhost:3000)
* **Backend API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Qdrant Dashboard Panel**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### Verify API Health Check
```bash
curl http://localhost:8000/health
```
Response:
```json
{
  "status": "healthy"
}
```

---

## Next Phases Roadmap
1. **Phase 1**: GitHub import, local directory parser, repository dashboards, language/framework detection, search.
2. **Phase 2**: React Flow interactive graphs, dependency mapping, call tree traces, API/DB explorers.
3. **Phase 3**: RAG Context building, semantic vector queries, localized file explanations.
4. **Phase 4**: Documentation generator, duplicate logic, circular dependency, technical debt reporting.
5. **Phase 5**: PR diff analytics, git history tracking, pluggable custom analyzers.

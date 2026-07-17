# Monorepo Folder Structure

RepoLens follows a monorepo workspace design pattern separating execution applications from core library logic.

```text
repolens/
├── .github/
│   └── workflows/              # GitHub CI/CD configuration files
├── apps/
│   ├── api/                    # FastAPI python app
│   │   ├── app/                # Main clean architecture app layers
│   │   ├── migrations/         # Alembic database migrations
│   │   └── pyproject.toml      # Tool parameters for Ruff/Black
│   ├── worker/                 # ARQ background task runner
│   └── web/                    # React 19 + Vite client frontend
├── docs/                       # Project manuals & guides
├── packages/                   # Reusable packages (skeletons in Phase 0)
│   ├── ai/                     # LiteLLM integrations
│   ├── analyzer/               # AST traversal orchestrator
│   ├── common/                 # Common Python classes & helpers
│   ├── documentation/          # Auto docs compiler
│   ├── embeddings/             # Embedding builders
│   ├── graph/                  # NetworkX nodes assembler
│   ├── parsers/                # Language syntax parsing rules
│   ├── sdk/                    # Type-safe TypeScript client API
│   └── search/                 # Semantic & Postgres text search services
└── docker-compose.yml          # Container configuration for Postgres, Redis, Qdrant
```

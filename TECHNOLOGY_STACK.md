# RepoLens — Technology Stack (Version 1.0)

## Overview

RepoLens is built as a modern, AI-native full-stack application that combines deterministic static code analysis with AI-powered reasoning. The technology stack is selected based on five principles:

* **Performance** — Fast analysis of large repositories.
* **Scalability** — Designed to grow from MVP to enterprise.
* **Developer Experience** — Modern tools that encourage open-source contributions.
* **Extensibility** — Modular analyzers and provider-agnostic AI.
* **Reliability** — Deterministic code analysis before AI reasoning.

---

# Frontend

The frontend provides an interactive dashboard for exploring repositories, visualizing architecture, chatting with AI, and browsing analysis results.

| Technology          | Purpose                                        |
| ------------------- | ---------------------------------------------- |
| **React 19**        | Frontend Framework                             |
| **TypeScript**      | Type-safe development                          |
| **Vite**            | Development server & build tool                |
| **Tailwind CSS v4** | Utility-first styling                          |
| **shadcn/ui**       | Modern UI component library                    |
| **React Router v7** | Client-side routing                            |
| **TanStack Query**  | Server state management                        |
| **Zustand**         | Client-side state management                   |
| **React Flow**      | Interactive architecture and dependency graphs |
| **Monaco Editor**   | Embedded code viewer                           |
| **Framer Motion**   | UI animations and transitions                  |
| **Lucide React**    | Icon library                                   |
| **Recharts**        | Dashboards and analytics charts                |

---

# Backend

The backend powers repository management, analysis pipelines, AI orchestration, authentication, and APIs.

| Technology         | Purpose                             |
| ------------------ | ----------------------------------- |
| **Python 3.13**    | Primary programming language        |
| **FastAPI**        | High-performance API framework      |
| **Uvicorn**        | ASGI server                         |
| **SQLAlchemy 2.x** | ORM                                 |
| **Alembic**        | Database migrations                 |
| **Pydantic v2**    | Validation & serialization          |
| **HTTPX**          | Async HTTP client                   |
| **GitPython**      | Git repository operations           |
| **orjson**         | High-performance JSON serialization |

---

# Database Layer

RepoLens uses a hybrid storage strategy optimized for structured data and semantic search.

| Technology     | Purpose                                    |
| -------------- | ------------------------------------------ |
| **PostgreSQL** | Primary relational database                |
| **Qdrant**     | Vector database for semantic search        |
| **Redis**      | Cache, sessions, and background job broker |

---

# AI & Machine Learning

RepoLens separates AI orchestration from code analysis, making it easy to switch between providers.

| Technology                | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| **LiteLLM**               | Unified interface for multiple LLM providers |
| **Sentence Transformers** | Code and documentation embeddings            |
| **Ollama**                | Local model execution during development     |
| **OpenAI API**            | Cloud LLM support                            |
| **Anthropic Claude API**  | Optional enterprise AI provider              |
| **Google Gemini API**     | Optional AI provider                         |
| **OpenRouter**            | Multi-model gateway                          |
| **Groq API**              | High-speed inference support                 |

---

# Static Code Analysis

Static analysis is the core intelligence layer of RepoLens.

## Universal Analysis

| Technology      | Purpose                                   |
| --------------- | ----------------------------------------- |
| **Tree-sitter** | Multi-language syntax parsing             |
| **NetworkX**    | Dependency and knowledge graph generation |

## Python Analysis

| Technology     | Purpose                              |
| -------------- | ------------------------------------ |
| **Python AST** | Native syntax analysis               |
| **LibCST**     | Concrete syntax tree transformations |
| **Jedi**       | Symbol resolution and navigation     |

## JavaScript / TypeScript

| Technology                 | Purpose            |
| -------------------------- | ------------------ |
| **Tree-sitter JavaScript** | Parsing JavaScript |
| **Tree-sitter TypeScript** | Parsing TypeScript |

## Future Language Support

* Java
* Go
* Rust
* C#
* PHP
* Kotlin
* Swift

Each language analyzer is implemented as an independent module.

---

# Search Engine

RepoLens provides both lexical and semantic search.

## Lexical Search

| Technology                      | Purpose             |
| ------------------------------- | ------------------- |
| **PostgreSQL Full-Text Search** | Fast keyword search |

## Semantic Search

| Technology                | Purpose                  |
| ------------------------- | ------------------------ |
| **Qdrant**                | Vector similarity search |
| **Sentence Transformers** | Embedding generation     |

---

# Graph Processing

The graph engine powers architecture visualization and dependency exploration.

| Technology              | Purpose                         |
| ----------------------- | ------------------------------- |
| **NetworkX**            | Dependency graph construction   |
| **React Flow**          | Interactive graph visualization |
| **Mermaid**             | Documentation diagrams          |
| **Graphviz** *(Future)* | Static graph rendering          |

---

# Background Processing

Repository analysis is asynchronous to keep the UI responsive.

| Technology | Purpose                         |
| ---------- | ------------------------------- |
| **ARQ**    | Async background job processing |
| **Redis**  | Job queue backend               |

Typical background tasks include:

* Repository cloning
* Static analysis
* Embedding generation
* Documentation generation
* AI summarization
* Dependency analysis

---

# Authentication & Security

| Technology               | Purpose                                   |
| ------------------------ | ----------------------------------------- |
| **GitHub OAuth**         | User authentication                       |
| **JWT**                  | API authentication                        |
| **Passlib** *(Optional)* | Password hashing (if local auth is added) |
| **Python Cryptography**  | Encryption utilities                      |

---

# File Storage

| Technology                               | Purpose                          |
| ---------------------------------------- | -------------------------------- |
| **Local Workspace**                      | Repository cache during analysis |
| **Amazon S3 / Cloudflare R2** *(Future)* | Report and artifact storage      |

---

# Development Tools

| Technology         | Purpose                        |
| ------------------ | ------------------------------ |
| **Docker**         | Local development & deployment |
| **Docker Compose** | Multi-service orchestration    |
| **GitHub Actions** | CI/CD                          |
| **Ruff**           | Python linting                 |
| **Black**          | Python formatting              |
| **Pytest**         | Backend testing                |
| **ESLint**         | Frontend linting               |
| **Prettier**       | Frontend formatting            |
| **Playwright**     | End-to-end testing             |

---

# Deployment

## Frontend

* Vercel

## Backend

* Railway or Fly.io

## Database

* Supabase PostgreSQL

## Vector Database

* Qdrant Cloud

## Cache & Queue

* Upstash Redis

---

# Monitoring & Observability

| Technology                   | Purpose                   |
| ---------------------------- | ------------------------- |
| **Sentry**                   | Error tracking            |
| **OpenTelemetry** *(Future)* | Distributed tracing       |
| **Prometheus** *(Future)*    | Metrics collection        |
| **Grafana** *(Future)*       | Infrastructure dashboards |

---

# Recommended Project Structure

```text
repolens/
│
├── apps/
│   ├── api/                    # FastAPI application
│   ├── worker/                 # Background workers
│   └── web/                    # React frontend
│
├── packages/
│   ├── analyzer/               # Static analysis engine
│   ├── parsers/                # Language parsers
│   ├── graph/                  # Knowledge graph engine
│   ├── embeddings/             # Embedding generation
│   ├── ai/                     # AI orchestration
│   ├── search/                 # Search services
│   ├── documentation/          # Documentation generator
│   ├── common/                 # Shared utilities
│   └── sdk/                    # Public SDK
│
├── docs/
├── docker/
├── scripts/
├── tests/
└── examples/
```

---

# Technology Summary

| Layer               | Technologies                                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Frontend**        | React 19, TypeScript, Vite, Tailwind CSS v4, shadcn/ui, React Router v7, TanStack Query, Zustand, React Flow, Monaco Editor, Framer Motion |
| **Backend**         | Python 3.13, FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic, HTTPX, GitPython                                                             |
| **Database**        | PostgreSQL, Qdrant, Redis                                                                                                                  |
| **AI**              | LiteLLM, Sentence Transformers, Ollama, OpenAI, Claude, Gemini, OpenRouter, Groq                                                           |
| **Static Analysis** | Tree-sitter, Python AST, LibCST, Jedi, NetworkX                                                                                            |
| **Search**          | PostgreSQL Full-Text Search, Qdrant                                                                                                        |
| **Graphs**          | NetworkX, React Flow, Mermaid                                                                                                              |
| **Jobs**            | ARQ, Redis                                                                                                                                 |
| **Authentication**  | GitHub OAuth, JWT                                                                                                                          |
| **DevOps**          | Docker, Docker Compose, GitHub Actions                                                                                                     |
| **Testing**         | Pytest, Playwright                                                                                                                         |
| **Deployment**      | Vercel, Railway/Fly.io, Supabase PostgreSQL, Qdrant Cloud, Upstash Redis                                                                   |
| **Monitoring**      | Sentry, OpenTelemetry (Future), Prometheus (Future), Grafana (Future)                                                                      |
| ---

# Design Philosophy

RepoLens is designed around a **hybrid intelligence architecture**. Deterministic static analysis produces an accurate structural understanding of a repository, while AI enriches that understanding with explanations, summaries, and natural language interaction. This separation ensures that architectural insights remain explainable, reproducible, and grounded in the actual source code while leveraging modern language models for developer-friendly exploration.

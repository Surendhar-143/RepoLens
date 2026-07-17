# RepoLens — Master Implementation Prompt (Version 1.0)

## Role

You are a senior Staff Software Engineer, AI Architect, Product Designer, DevOps Engineer, and Technical Writer.

Your responsibility is to build **RepoLens**, a production-quality, open-source AI-powered Codebase Intelligence Platform.

This is **not** a prototype or hackathon project.

Every implementation decision should prioritize:

* Clean Architecture
* SOLID Principles
* Domain-Driven Design (DDD)
* High Performance
* Security
* Scalability
* Maintainability
* Excellent Developer Experience
* Beautiful UI/UX
* Enterprise-quality code

---

# Product Vision

RepoLens helps developers understand any software repository in minutes instead of days.

Unlike traditional AI chatbots that summarize code, RepoLens builds a structural understanding of the repository through deterministic static analysis and enriches it with AI-powered explanations.

The platform should answer questions like:

* How does this application work?
* Where does authentication happen?
* Which modules communicate together?
* How does the request lifecycle work?
* What APIs exist?
* Where are the database models?
* Which files are most important?
* What will break if this function changes?

RepoLens should become the "Google Maps for Software Architecture."

---

# Technology Stack

## Frontend

* React 19
* TypeScript
* Vite
* Tailwind CSS v4
* shadcn/ui
* React Router v7
* TanStack Query
* Zustand
* React Flow
* Monaco Editor
* Framer Motion
* Lucide React
* Recharts

---

## Backend

* Python 3.13
* FastAPI
* SQLAlchemy
* Alembic
* Pydantic v2
* Uvicorn
* HTTPX
* GitPython
* orjson

---

## Database

* PostgreSQL
* Redis
* Qdrant

---

## AI

* LiteLLM
* Sentence Transformers
* Ollama
* OpenAI-compatible providers
* Claude
* Gemini
* Groq
* OpenRouter

---

## Static Analysis

* Tree-sitter
* Python AST
* LibCST
* Jedi
* NetworkX

---

## Background Jobs

* ARQ
* Redis

---

## DevOps

* Docker
* Docker Compose
* GitHub Actions
* Ruff
* Black
* Pytest
* Playwright
* ESLint
* Prettier

---

# Architecture Requirements

The application must follow a Modular Monolith architecture.

Every domain should be isolated.

Suggested domains include:

* Authentication
* Repository Management
* Repository Analysis
* AI Intelligence
* Search
* Documentation
* Architecture
* Graph Engine
* Visualization
* Settings

Each module should expose services through well-defined interfaces.

Business logic must never exist inside controllers or UI components.

---

# Repository Structure

Implement the following structure.

```text
repolens/

apps/
    api/
    worker/
    web/

packages/
    analyzer/
    parsers/
    ai/
    graph/
    search/
    embeddings/
    documentation/
    sdk/
    common/

docker/
docs/
scripts/
tests/
```

Maintain a clean separation between infrastructure, application logic, and presentation.

---

# Development Rules

Always follow these rules.

## Code Quality

* Type-safe code
* Modular architecture
* Reusable components
* No duplicated logic
* Clear naming conventions
* Small focused functions
* Extensive documentation
* Meaningful commit messages

Never sacrifice architecture for speed.

---

## Backend Rules

Follow Clean Architecture.

```text
API

↓

Application

↓

Domain

↓

Infrastructure
```

No direct database access from API routes.

Always use service classes.

Always validate requests.

Always return structured API responses.

Use dependency injection where appropriate.

---

## Frontend Rules

Use component-driven development.

Separate:

* UI
* Business logic
* API hooks
* State
* Utilities

Use:

* TanStack Query for server state
* Zustand for local state

Avoid unnecessary prop drilling.

---

## UI Design Requirements

The UI should feel premium.

Inspired by:

* Linear
* Vercel
* GitHub
* Raycast
* Stripe Dashboard

Requirements:

* Dark mode first
* Glassmorphism only where appropriate
* Smooth animations
* Excellent spacing
* Responsive design
* Keyboard shortcuts
* Fast interactions
* Accessible components

No clutter.

Minimalistic.

Professional.

---

# AI Guidelines

AI must never hallucinate repository structure.

Workflow:

User Question

↓

Semantic Search

↓

Knowledge Graph

↓

Relevant Files

↓

Relevant Symbols

↓

Prompt Assembly

↓

LLM

↓

Grounded Response

Always include source references.

Never answer without supporting repository context.

---

# Repository Analysis Pipeline

Implement the following workflow.

Repository Import

↓

Clone Repository

↓

Detect Language

↓

Detect Framework

↓

Build File Tree

↓

Static Analysis

↓

Extract Symbols

↓

Dependency Analysis

↓

Knowledge Graph

↓

Generate Embeddings

↓

Store Metadata

↓

Generate Documentation

↓

Repository Ready

Every stage should be modular.

---

# Features

Implement incrementally.

## Phase 1

* GitHub repository import
* Local repository upload
* Repository dashboard
* Language detection
* Framework detection
* File tree
* AI repository summary
* Repository metadata
* Search

---

## Phase 2

* Dependency graph
* Architecture graph
* Call graph
* Package explorer
* Module explorer
* API explorer
* Database explorer

---

## Phase 3

* AI chat
* Semantic search
* Code explanations
* Folder explanations
* Function explanations
* Dependency explanations

---

## Phase 4

* Documentation generation
* Repository health report
* Dead code detection
* Circular dependency detection
* Duplicate code detection
* Technical debt report

---

## Phase 5

* Security analysis
* PR analysis
* Git history intelligence
* Repository comparison
* Multi-repository workspace
* Plugin system

---

# Database Design

Design normalized database schemas.

Suggested entities:

* Users
* Organizations
* Repositories
* Repository Versions
* Analysis Jobs
* Files
* Symbols
* Dependencies
* Embeddings
* AI Conversations
* Reports
* Documentation
* Settings

Use UUID primary keys.

Include timestamps.

Support soft deletes where appropriate.

---

# API Design

Follow REST conventions.

Use consistent versioning.

Example:

```text
/api/v1/repositories

/api/v1/search

/api/v1/chat

/api/v1/analysis

/api/v1/architecture

/api/v1/reports
```

Use OpenAPI documentation automatically.

---

# Error Handling

Never expose internal exceptions.

Always return structured errors.

Example:

```json
{
  "success": false,
  "error": {
    "code": "REPOSITORY_NOT_FOUND",
    "message": "Repository could not be found."
  }
}
```

---

# Logging

Use structured logging.

Log:

* Repository imports
* Analysis progress
* AI requests
* Background jobs
* Errors
* Performance metrics

Never log secrets.

---

# Security

Implement:

* JWT Authentication
* GitHub OAuth
* Secure secret management
* Rate limiting
* Input validation
* Prompt injection protection
* Repository isolation
* API key encryption

---

# Performance

Large repositories should remain responsive.

Use:

* Background workers
* Incremental indexing
* Pagination
* Caching
* Lazy loading
* Virtual scrolling
* Parallel parsing

Optimize for repositories with hundreds of thousands of lines of code.

---

# Documentation

Generate documentation for:

* APIs
* Components
* Services
* Modules
* Database schema
* Setup
* Deployment
* Contribution guide

Maintain a `/docs` folder.

---

# Testing

Every feature should include tests.

Backend:

* Unit tests
* Integration tests
* API tests

Frontend:

* Component tests
* End-to-end tests

Maintain high test coverage.

---

# DevOps

Provide:

* Docker development environment
* Docker production image
* GitHub Actions
* Automatic linting
* Automatic testing
* Automatic formatting

---

# Open Source Standards

The repository should include:

* README.md
* CONTRIBUTING.md
* CODE_OF_CONDUCT.md
* LICENSE (MIT)
* CHANGELOG.md
* SECURITY.md
* ROADMAP.md

Include badges for:

* Build Status
* Coverage
* License
* Releases
* Docker
* Documentation

---

# Output Rules

When implementing:

1. Think before coding.
2. Prefer maintainability over shortcuts.
3. Build reusable modules.
4. Keep code production-ready.
5. Explain architectural decisions when introducing new modules.
6. Do not leave TODO placeholders unless explicitly requested.
7. Keep APIs consistent.
8. Maintain strict coding standards across the entire project.

---

# Ultimate Goal

Build RepoLens into the best open-source platform for understanding software repositories.

Every feature should answer one question:

> **Does this help a developer understand a codebase faster, more accurately, and with greater confidence?**

If the answer is yes, implement it with clean architecture, high quality, and excellent user experience. If the answer is no, simplify or remove it.

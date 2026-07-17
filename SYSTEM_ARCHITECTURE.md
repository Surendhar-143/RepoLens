# RepoLens — System Architecture (Version 1.0)

**Version:** 1.0
**Status:** Architecture Specification
**Architecture Style:** Modular Monolith with AI Intelligence Layer
**Primary Goal:** Analyze, understand, visualize, and explain software repositories using deterministic code analysis combined with AI-powered reasoning.

---

# 1. High-Level Architecture

```text
                                      ┌──────────────────────────┐
                                      │      GitHub/GitLab       │
                                      │    Local Repository      │
                                      └─────────────┬────────────┘
                                                    │
                                                    ▼
                                   ┌────────────────────────────────┐
                                   │ Repository Import Service      │
                                   │ Clone • Sync • Cache           │
                                   └────────────────┬───────────────┘
                                                    │
                                                    ▼
                         ┌────────────────────────────────────────────────────┐
                         │             Repository Analysis Engine             │
                         │                                                    │
                         │  Language Detection                                │
                         │  Static Code Analysis                              │
                         │  Dependency Analysis                               │
                         │  Symbol Extraction                                 │
                         │  Framework Detection                               │
                         │  Architecture Discovery                            │
                         └────────────────┬───────────────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              ▼                           ▼                           ▼
     Knowledge Graph             Metadata Store               Vector Index
     (Relationships)              (PostgreSQL)                 (Qdrant)
              │                           │                           │
              └──────────────┬────────────┴────────────┬──────────────┘
                             ▼                         ▼
                     AI Intelligence Layer      Search Engine
                             │                         │
                             └──────────────┬──────────┘
                                            ▼
                                  FastAPI Backend
                                            │
                           REST API • WebSocket • SSE
                                            │
                                            ▼
                                  React Frontend
```

---

# 2. Architectural Principles

RepoLens follows several core architectural principles.

## Modular Monolith

Although the system contains multiple domains, they are deployed as a single application.

Benefits:

* Simpler deployment
* Easier debugging
* Lower infrastructure costs
* Faster development
* Clean separation of domains
* Easy future migration into microservices if required

---

## AI-Augmented Static Analysis

The platform does **not** rely solely on LLMs.

Instead it combines

```
Deterministic Analysis

+

Semantic Understanding

+

AI Reasoning
```

This provides:

* Accurate architecture
* Explainable outputs
* Reduced hallucinations
* Better performance

---

# 3. System Layers

---

## Presentation Layer

Responsible for user interaction.

### Components

* React Application
* Dashboard
* Repository Explorer
* AI Chat
* Architecture Viewer
* Dependency Graph
* API Explorer
* Search Interface
* Settings

Responsibilities

* Display repository insights
* Interactive navigation
* Graph visualization
* Real-time progress updates
* AI conversations

---

## API Layer

Built using FastAPI.

Responsibilities

* Authentication
* Repository management
* Search APIs
* AI APIs
* Architecture APIs
* Documentation APIs
* Analysis APIs

Example endpoints

```
POST /repositories

GET /repositories/{id}

POST /repositories/{id}/analyze

GET /architecture

GET /dependencies

GET /search

POST /chat
```

---

## Domain Layer

The core business logic of RepoLens.

Domains:

```
Repository Domain

Analysis Domain

AI Domain

Search Domain

Visualization Domain

Documentation Domain

Authentication Domain
```

Each domain remains independent and communicates through service interfaces.

---

## Infrastructure Layer

Handles external systems.

Includes:

* Git operations
* PostgreSQL
* Redis
* Qdrant
* File storage
* AI providers
* Background workers

---

# 4. Module Architecture

```
RepoLens

├── Authentication
│
├── Repository Management
│
├── Repository Analysis
│
├── Language Parsers
│
├── Dependency Engine
│
├── Architecture Engine
│
├── Graph Builder
│
├── AI Intelligence
│
├── Semantic Search
│
├── Documentation Generator
│
├── Health Analyzer
│
├── Reporting
│
└── Notification System
```

Each module exposes public services while hiding implementation details.

---

# 5. Repository Analysis Pipeline

Every repository follows the same processing pipeline.

```
Import Repository

↓

Clone

↓

Detect Language

↓

Detect Framework

↓

Build File Tree

↓

Parse Files

↓

Extract Symbols

↓

Build Dependency Graph

↓

Build Knowledge Graph

↓

Generate Embeddings

↓

Store Metadata

↓

Run AI Analysis

↓

Generate Documentation

↓

Repository Ready
```

---

# 6. Language Analysis Layer

Each supported language has its own analyzer.

```
Analyzer

├── Python

├── JavaScript

├── TypeScript

├── Java

├── Go

├── Rust

├── PHP

├── C#

└── Future Languages
```

Each analyzer extracts:

* Imports
* Classes
* Interfaces
* Functions
* Variables
* API routes
* Database models
* Configuration
* Framework conventions

---

# 7. Knowledge Graph

The Knowledge Graph becomes the heart of RepoLens.

Instead of storing only files, RepoLens stores relationships.

Example

```
Repository

↓

Folder

↓

File

↓

Class

↓

Method

↓

Function

↓

API

↓

Database Table

↓

Service

↓

Configuration
```

Relationships

```
Imports

Calls

Uses

Extends

Implements

Depends On

Creates

Reads

Writes

Authenticates

Schedules
```

This graph enables deep repository understanding.

---

# 8. AI Intelligence Layer

The AI layer sits on top of deterministic analysis.

Components

```
Prompt Engine

↓

Context Builder

↓

Vector Search

↓

Knowledge Graph

↓

LLM Provider

↓

Response Generator
```

Workflow

```
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

Grounded Answer
```

This significantly reduces hallucinations.

---

# 9. Search Architecture

RepoLens supports two complementary search mechanisms.

### Keyword Search

Uses PostgreSQL.

Ideal for

* filenames
* functions
* APIs
* symbols

---

### Semantic Search

Uses vector embeddings.

Ideal for

```
"Where is authentication handled?"

"Explain login."

"Show payment flow."

"JWT verification"

"Database initialization"
```

---

# 10. Architecture Engine

Automatically builds

```
Application Architecture

↓

Package Graph

↓

Dependency Graph

↓

Call Graph

↓

Module Graph

↓

Request Flow

↓

Database Flow

↓

Authentication Flow
```

Outputs are visualized interactively.

---

# 11. Documentation Engine

Automatically generates

```
Repository Overview

Folder Documentation

Architecture Guide

API Documentation

Database Documentation

Developer Guide

Onboarding Guide
```

Generated documentation stays synchronized with analysis results.

---

# 12. Background Processing

Long-running tasks execute asynchronously.

Jobs include

```
Clone Repository

Analyze Repository

Generate Embeddings

Refresh Analysis

Update Dependencies

Generate Documentation

AI Summaries
```

This keeps the user interface responsive.

---

# 13. Storage Architecture

### PostgreSQL

Stores

* repositories
* users
* analysis metadata
* settings
* reports
* architecture metadata

---

### Qdrant

Stores

* embeddings
* semantic vectors
* contextual search data

---

### Redis

Stores

* cache
* job queues
* sessions
* temporary analysis state

---

### Local Repository Cache

Stores cloned repositories for analysis.

---

# 14. Frontend Architecture

```
Dashboard

├── Repository Explorer

├── AI Chat

├── Architecture Viewer

├── Search

├── Dependency Explorer

├── API Explorer

├── Database Explorer

├── Reports

└── Settings
```

The frontend communicates exclusively through backend APIs, keeping the UI stateless and making future desktop or CLI clients straightforward to build.

---

# 15. Security Architecture

Authentication

* GitHub OAuth
* JWT
* Refresh Tokens

Authorization

* Repository ownership
* Team permissions
* Organization roles

Secrets

* Encrypted API keys
* Environment isolation
* Secure repository cloning

AI Safety

* Prompt sanitization
* Context validation
* Token limits
* Source-grounded responses

---

# 16. Scalability Strategy

Although RepoLens starts as a Modular Monolith, every module is designed to become an independent service if needed.

Potential future services:

```
Analysis Service

AI Service

Search Service

Repository Service

Documentation Service

Notification Service
```

The separation of domains today minimizes migration effort later.

---

# 17. Technology Stack

### Frontend

* React 19
* TypeScript
* Vite
* Tailwind CSS
* shadcn/ui
* React Flow
* Monaco Editor
* TanStack Query
* Zustand

### Backend

* FastAPI
* Python 3.13
* SQLAlchemy
* Alembic
* Pydantic

### AI

* LiteLLM
* Ollama (Development)
* OpenAI-compatible providers
* Sentence Transformers

### Analysis

* Tree-sitter
* Python AST
* LibCST
* NetworkX

### Data Layer

* PostgreSQL
* Qdrant
* Redis

### Infrastructure

* Docker
* GitHub Actions
* Railway/Fly.io
* Vercel
* Supabase PostgreSQL
* Qdrant Cloud
* Upstash Redis

---

# 18. Future Architecture Evolution

RepoLens is designed as a platform rather than a single application.

Planned extensions include:

* Pull Request Intelligence
* Security Vulnerability Analysis
* Dependency Risk Assessment
* Multi-Repository Workspace
* Architectural Drift Detection
* CI/CD Pipeline Analysis
* Infrastructure-as-Code Analysis
* AI Code Review Assistant
* Enterprise Organization Insights
* Plugin SDK for custom analyzers

By keeping the analysis engine, knowledge graph, AI layer, and visualization modules independent, RepoLens can evolve into a comprehensive software intelligence platform without requiring a complete architectural redesign.

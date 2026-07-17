# Knowledge Graph Specification Manual

The RepoLens Knowledge Graph maps codebase files, AST declarations, database ORM models, and REST endpoints into an interconnected graph.

## Graph Model
* **Nodes**: Represent directory structures, files, code abstractions, and APIs.
* **Edges**: Represent dependencies, call trees, inheritance, and pathways.

---

## Nodes Specifications

### 1. Folder Nodes
* **Type**: `folder`
* **Parent**: Parent folder ID (if subfolder) or `None`.
* **Metadata**: Full path path.

### 2. File Nodes
* **Type**: `file`
* **Parent**: Containing folder ID.
* **Metadata**: File size in bytes, mime headers.

### 3. Symbol Nodes
* **Type**: `class` or `function`
* **Parent**: File ID.
* **Metadata**: Line scope parameters, calculated cyclomatic complexity.

### 4. API Nodes
* **Type**: `api`
* **Parent**: File ID defining route.
* **Metadata**: Endpoint route path, HTTP method.

### 5. ORM Model Nodes
* **Type**: `model`
* **Parent**: File ID.
* **Metadata**: Declared primary keys, fields names.

---

## Edge Relationships

| Edge Type | Source Node | Target Node | Meaning |
|---|---|---|---|
| `BELONGS_TO` | File | Folder | Directory location |
| `DEFINES` | File | Symbol | AST declaration boundary |
| `IMPORTS` | File | File | Import module dependencies |
| `EXTENDS` | Class | Class | Inheritance line |
| `CALLS` | Function | Function | Function invocation path |
| `ROUTES_TO` | API | Function | Endpoint controller method |
| `USES` | Function | Model | Database ORM model interaction |

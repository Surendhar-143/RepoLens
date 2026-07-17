# Static Analysis Engine Manual

RepoLens analyzes codebases deterministically through AST traversal and token scans, storing files tree nodes, imports, symbol details, APIs routing tables, and ORM database models.

## Codebase Scanning Pipeline
1. **Recursion & Pruning**: Walks workspace cache directories recursively. Automatically ignores binary targets, log dumps, and build targets:
   * `node_modules`, `.git`, `vendor`, `dist`, `build`, `__pycache__`, `.venv`, `.next`, `target`.
2. **SHA-256 Hashing**: Generates unique file hash hashes. If a file's hash matches the database value during reanalysis, parsing is skipped (Incremental Reanalysis).
3. **Mime Verification**: Assigns mime headers according to extension profiles.

---

## AST Parsers
* **Python Parser**: Uses Python's native `ast` compiler module. Translates imports (`Import`/`ImportFrom`), class lists (arguments inheritance, decorators, lines scope), and function maps (annotations types, return types).
* **JavaScript / TypeScript Parser**: Scans file text structure to locate ES6 `import` paths, class definitions, parameters list, and functions blocks.

---

## REST API Handlers
* **APIs Scanner**: Detects routes structurally matching web libraries:
  * Python: FastAPI (`@router.get`, `@app.post`)
  * JavaScript/TypeScript: Express (`router.get`, `app.post`) and NestJS decorators (`@Get`, `@Post`).
* **Database Scanner**: Identifies ORM model structures:
  * Django ORM (`models.Model`)
  * SQLAlchemy (`Base` or `mapped_column`)
  * Prisma (`model` schema blocks)
  * TypeORM/Mongoose models

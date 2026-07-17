# Contributing to RepoLens

Thank you for your interest in contributing to RepoLens! We welcome support from the open-source community.

## Code Standards
* **Python**: Type hints are required for all public functions. Code must adhere to Black formatting and pass Ruff check regulations.
* **TypeScript**: Enforce strict type checking. Do not use `any` type variables unless absolutely necessary.
* **Clean Architecture**: Never access databases directly from route endpoints; use service layer commands.

## Pull Request Guidelines
1. Fork the repo and create your branch from `master`.
2. Verify all local tests pass:
   ```bash
   pytest apps/api/tests
   ```
3. Ensure no linting errors are present.
4. Format your commit messages clearly (e.g. `feat(analyzer): add tree-sitter parser`).

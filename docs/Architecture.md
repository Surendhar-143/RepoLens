# Architecture Intelligence Manual

This document details how RepoLens compiles modular coupling/cohesion indexes, detects circular references, and traces request lifecycles.

---

## 1. Coupling Metrics
Coupling represents how interconnected package files are. Low coupling is highly desired because it ensures changes inside one subsystem do not cause cascading failures.
* **Formula**:
  $$\text{Coupling Index} = \frac{\text{Inter-File Imports}}{\text{Total Imports}}$$
* **Scale**:
  * **0 - 30%**: Low coupling (Highly decoupled, excellent modularity).
  * **30 - 60%**: Moderate coupling.
  * **60 - 100%**: High coupling (Tight coupling, refactoring recommended).

---

## 2. Cohesion Metrics
Cohesion measures how focused functions inside a module are on performing a single set of operations. High cohesion is optimal.
* **Formula**:
  $$\text{Cohesion Index} = \frac{\text{Intra-File Calls}}{\text{Total Calls}}$$

---

## 3. Circular Dependency Detection
Circular references prevent incremental compilation and can cause initialization locks.
* **Detection Algorithm**: Performs Depth First Search (DFS) on the `IMPORTS` edge graph.
* **Loop Tracing**: Tracks recursion paths and alerts developers with warning diagrams.

---

## 4. API Request Lifecycle Flow
RepoLens links REST endpoint declarations down to SQL database operations:
1. **API Router**: Scans endpoints configurations (e.g. `@router.get("/users")`).
2. **Controller Function**: Identifies the handler routine via `ROUTES_TO` links.
3. **Calls Hierarchy**: Traces nested function execution calls (`CALLS` links).
4. **Database Table**: Detects model class mentions (SQLAlchemy, Django ORM, Prisma) mapping to `USES` relationships.

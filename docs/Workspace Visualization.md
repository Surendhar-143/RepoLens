# Workspace Visualization & Collaboration Guide

RepoLens builds interactive visual architectures driven directly by knowledge graph node structures.

## 1. Graph Layout Engines
We support dynamic layout rendering on the React Flow canvas:
* **Spiral distribution**: Spreads nodes along spiral offsets.
* **Hierarchical layouts**: Computes topological sort hierarchies, aligning nodes vertically by calling depths/dependency heights.
* **Force circular layouts**: Centers nodes in uniform rings with links.

---

## 2. Annotations & Notes
Annotations let developers pin context to files, symbols, or code lines:
* **Storage model**: Saved in `annotations` table in PostgreSQL.
* **Triggers**: Click any node on the graph canvas to inspect its details and add comments.

---

## 3. Bookmarks & Saved Views
Bookmarks capture layout choices, filter states, and zoom settings:
* Saved views list: `GET /api/v1/workspace/bookmarks/list`
* Add bookmark view state: `POST /api/v1/workspace/bookmarks`

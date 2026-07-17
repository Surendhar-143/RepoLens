# Semantic Search & Retrieval Manual

RepoLens indexes code segments and documentation into Qdrant vectors to support natural language queries.

## Chunker & Code Segmenter
Chunks are divided logically to retain AST properties:
* **Classes / Functions**: Vectorized with their names, parameters signatures, parent file pathways, and full definitions code blocks.
* **Database Models**: Vectorized with fields listings and relationship links.
* **API Routers**: Maps methods and route templates.
* **Markdown READMEs**: Split by paragraph boundaries.

---

## Embedding Provider Abstractions
We implement `EmbeddingProvider` allowing pluggable adapters:
1. **Sentence Transformers**: `bge-small-en-v1.5` mapping text segments to 384-dimensional vectors.
2. **OpenAI Embeddings**: Calls `text-embedding-3-small` (1536 dimensions) when `OPENAI_API_KEY` is configured.
3. **Hashed Mock Provider**: Acts as local fallback for development testing.

---

## Hybrid Search Ranking Formula
Matches combine lexical occurrences and semantic similarities:
* **PostgreSQL Lexical Match**: Scans names and snippets using index queries.
* **Qdrant Vector Similarity**: Finds closest vectors using Cosine similarity.
* **Knowledge Graph Centrality**: Scores are boosted by degree importance:
  $$\text{Boost} = \ln(\text{Degree} + 1) \times 0.1$$

Combined relevance score is computed as:
$$\text{Score} = (\text{Semantic Score} \times 0.6) + (\text{Lexical Score} \times 0.4) + \text{Boost}$$

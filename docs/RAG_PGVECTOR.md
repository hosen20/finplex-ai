# pgvector RAG Retrieval

Finplex AI stores tenant-specific RAG evidence in PostgreSQL and retrieves it with
pgvector cosine similarity. This keeps policy, ERP/CRM context, and invoice
evidence tenant-scoped and auditable.

## What changed

- `rag_chunks.embedding_vector` is a `vector(8)` column managed by the pgvector extension.
- The legacy JSON `embedding` column remains for readability and backwards compatibility.
- The `/rag/search` endpoint searches only the signed-in user's `tenant_id`.
- Seeded RAG documents now populate both JSON embeddings and pgvector embeddings.
- Migration `0003_pgvector_rag_embeddings.py` backfills existing seeded chunks.

## Local embedding strategy

The current local product uses a deterministic hash embedding so tests, seeding,
and CI are reproducible without paid model APIs. This is intentionally wrapped in
`RagService`, so a provider-based embedding model can replace it later without
changing the database schema or the API contract.

## Search contract

`POST /rag/search`

```json
{
  "query": "What evidence is required before sending a follow-up?",
  "limit": 5
}
```

The response returns chunk IDs, document IDs, document titles, source types,
content, and similarity scores. Tenant ID is taken from the JWT, not from the
request body.

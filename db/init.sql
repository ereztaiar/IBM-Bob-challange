-- Bootstrap script executed once when the PostgreSQL container first starts.
-- Enables the pgvector extension required by the RAG service for similarity search.

CREATE EXTENSION IF NOT EXISTS vector;

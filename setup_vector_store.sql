-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-------------------------------------------------------------------------------
-- 1. langchain_docs (ID as text)
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS "langchain_docs";
CREATE TABLE "langchain_docs" (
    id TEXT PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS "langchain_docs_embedding_idx"
    ON "langchain_docs"
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS "langchain_docs_metadata_idx"
    ON "langchain_docs"
    USING GIN (metadata);

CREATE INDEX IF NOT EXISTS "langchain_docs_content_idx"
    ON "langchain_docs"
    USING GIN (to_tsvector('english', COALESCE(content, '')));

-------------------------------------------------------------------------------
-- 2. langchain_example (ID as text)
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS "langchain_example";
CREATE TABLE "langchain_example" (
    id TEXT PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS "langchain_example_embedding_idx"
    ON "langchain_example"
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS "langchain_example_metadata_idx"
    ON "langchain_example"
    USING GIN (metadata);

CREATE INDEX IF NOT EXISTS "langchain_example_content_idx"
    ON "langchain_example"
    USING GIN (to_tsvector('english', COALESCE(content, '')));

-------------------------------------------------------------------------------
-- 3. documents (ID as bigserial - auto increments)
-------------------------------------------------------------------------------
DROP TABLE IF EXISTS "documents";
CREATE TABLE "documents" (
    id BIGSERIAL PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    embedding VECTOR(1536)
);

CREATE INDEX IF NOT EXISTS "documents_embedding_idx"
    ON "documents"
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS "documents_metadata_idx"
    ON "documents"
    USING GIN (metadata);

CREATE INDEX IF NOT EXISTS "documents_content_idx"
    ON "documents"
    USING GIN (to_tsvector('english', COALESCE(content, '')));

-------------------------------------------------------------------------------
-- Functions for langchain_docs
-------------------------------------------------------------------------------

-- Vector-based similarity on langchain_docs
CREATE OR REPLACE FUNCTION match_documents (
    query_embedding VECTOR(1536),
    match_count INT,
    filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        langchain_docs.id,
        langchain_docs.content,
        langchain_docs.metadata,
        1 - (langchain_docs.embedding <=> query_embedding) AS similarity
    FROM langchain_docs
    WHERE metadata @> filter
    ORDER BY langchain_docs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Vector-based similarity on langchain_example
CREATE OR REPLACE FUNCTION match_example_documents (
    query_embedding VECTOR(1536),
    match_count INT,
    filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        langchain_example.id,
        langchain_example.content,
        langchain_example.metadata,
        1 - (langchain_example.embedding <=> query_embedding) AS similarity
    FROM langchain_example
    WHERE metadata @> filter
    ORDER BY langchain_example.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Hybrid search (keyword + vector) on langchain_docs
CREATE OR REPLACE FUNCTION kw_match_documents (
    query_text TEXT,
    query_embedding VECTOR(1536),
    match_count INT,
    filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
    id TEXT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    text_similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        langchain_docs.id,
        langchain_docs.content,
        langchain_docs.metadata,
        1 - (langchain_docs.embedding <=> query_embedding) AS similarity,
        ts_rank(
            to_tsvector('english', COALESCE(langchain_docs.content, '')),
            plainto_tsquery('english', query_text)
        ) AS text_similarity
    FROM langchain_docs
    WHERE metadata @> filter
      AND (
          to_tsvector('english', COALESCE(langchain_docs.content, ''))
          @@ plainto_tsquery('english', query_text)
          OR 1 - (langchain_docs.embedding <=> query_embedding) > 0.7
      )
    ORDER BY 
        (
          (1 - (langchain_docs.embedding <=> query_embedding)) * 0.8
          + ts_rank(
                to_tsvector('english', COALESCE(langchain_docs.content, '')),
                plainto_tsquery('english', query_text)
            ) * 0.2
        ) DESC
    LIMIT match_count;
END;
$$;

-------------------------------------------------------------------------------
-- New Functions for the "documents" table
-------------------------------------------------------------------------------

-- 1) Vector-based similarity on the "documents" table
CREATE OR REPLACE FUNCTION match_main_documents (
    query_embedding VECTOR(1536),
    match_count INT,
    filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE metadata @> filter
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 2) Hybrid search (keyword + vector) on the "documents" table
CREATE OR REPLACE FUNCTION kw_match_main_documents (
    query_text TEXT,
    query_embedding VECTOR(1536),
    match_count INT,
    filter JSONB DEFAULT '{}'
)
RETURNS TABLE (
    id BIGINT,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    text_similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity,
        ts_rank(
            to_tsvector('english', COALESCE(documents.content, '')),
            plainto_tsquery('english', query_text)
        ) AS text_similarity
    FROM documents
    WHERE metadata @> filter
      AND (
          to_tsvector('english', COALESCE(documents.content, ''))
          @@ plainto_tsquery('english', query_text)
          OR 1 - (documents.embedding <=> query_embedding) > 0.7
      )
    ORDER BY 
        (
          (1 - (documents.embedding <=> query_embedding)) * 0.8
          + ts_rank(
                to_tsvector('english', COALESCE(documents.content, '')),
                plainto_tsquery('english', query_text)
            ) * 0.2
        ) DESC
    LIMIT match_count;
END;
$$;

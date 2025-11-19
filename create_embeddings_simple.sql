-- Create embeddings table - Simplified version
-- Enable pgvector first if not already done

CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID,
    chunk_number INTEGER,
    chunk_text TEXT,
    chunk_size INTEGER,
    embedding VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Basic indexes
CREATE INDEX IF NOT EXISTS idx_chunks_document ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Enable RLS
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Simple policy for service role
DROP POLICY IF EXISTS service_role_all_document_chunks ON document_chunks;
CREATE POLICY service_role_all_document_chunks ON document_chunks
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    chunk_text TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.chunk_text,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE document_chunks.embedding IS NOT NULL
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;



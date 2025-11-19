-- Create tables for embeddings in new project
-- Optimized structure based on old project analysis

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table
DROP TABLE IF EXISTS document_chunks CASCADE;

CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_number INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_size INTEGER,
    embedding VECTOR(1536), -- OpenAI ada-002 embeddings
    metadata JSONB, -- Flexible storage for additional data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Indexes for performance
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_chunks_number ON document_chunks(chunk_number);
CREATE INDEX idx_chunks_metadata ON document_chunks USING gin(metadata);

-- Vector similarity search index (IVFFlat for speed)
CREATE INDEX idx_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- RLS Policies
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public document_chunks are viewable by everyone." ON document_chunks
    FOR SELECT USING (true);

CREATE POLICY "Users can insert their own document_chunks." ON document_chunks
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Users can update their own document_chunks." ON document_chunks
    FOR UPDATE USING (auth.uid() IS NOT NULL);

CREATE POLICY "Users can delete their own document_chunks." ON document_chunks
    FOR DELETE USING (auth.uid() IS NOT NULL);

DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'document_chunks' 
        AND policyname = 'service_role_all_document_chunks'
    ) THEN
        CREATE POLICY service_role_all_document_chunks ON document_chunks
            FOR ALL
            TO service_role
            USING (true)
            WITH CHECK (true);
    END IF;
END $$;

-- Function for semantic search
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_text TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.document_id,
        document_chunks.chunk_text,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Stats view
CREATE OR REPLACE VIEW vw_embedding_stats AS
SELECT 
    COUNT(*) as total_chunks,
    COUNT(DISTINCT document_id) as total_documents,
    AVG(chunk_size) as avg_chunk_size,
    SUM(chunk_size) as total_characters,
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) as chunks_with_embedding,
    COUNT(*) FILTER (WHERE embedding IS NULL) as chunks_without_embedding
FROM document_chunks;

COMMENT ON TABLE document_chunks IS 'Text chunks with embeddings for semantic search';
COMMENT ON FUNCTION match_documents IS 'Search for similar documents using cosine similarity';
COMMENT ON VIEW vw_embedding_stats IS 'Statistics about embedded chunks';



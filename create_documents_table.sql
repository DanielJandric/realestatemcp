-- Create documents table to track all imported files
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT UNIQUE NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    category TEXT,
    property_id UUID REFERENCES properties(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    file_size BIGINT,
    file_hash TEXT UNIQUE,
    metadata JSONB
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_documents_property ON documents(property_id);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type);
CREATE INDEX IF NOT EXISTS idx_documents_file_hash ON documents(file_hash);

-- Enable RLS
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- RLS policy
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'documents' 
        AND policyname = 'service_role_all_documents'
    ) THEN
        CREATE POLICY service_role_all_documents ON documents
            FOR ALL TO service_role USING (true) WITH CHECK (true);
    END IF;
END $$;

-- Also add columns to tenants if missing
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS mobile TEXT,
ADD COLUMN IF NOT EXISTS emergency_contact TEXT,
ADD COLUMN IF NOT EXISTS guarantor TEXT;

-- Add helpful view for document stats
CREATE OR REPLACE VIEW vw_document_stats AS
SELECT 
    category,
    file_type,
    COUNT(*) as total_documents,
    SUM(file_size) as total_size_bytes,
    ROUND(SUM(file_size)::NUMERIC / 1024 / 1024, 2) as total_size_mb,
    MIN(created_at) as first_imported,
    MAX(created_at) as last_imported
FROM documents
GROUP BY category, file_type
ORDER BY total_documents DESC;

-- Add view for documents per property
CREATE OR REPLACE VIEW vw_documents_by_property AS
SELECT 
    p.name as property_name,
    d.category,
    COUNT(*) as doc_count
FROM properties p
LEFT JOIN documents d ON d.property_id = p.id
GROUP BY p.name, d.category
ORDER BY p.name, doc_count DESC;

COMMENT ON TABLE documents IS 'Central registry of all imported documents';
COMMENT ON VIEW vw_document_stats IS 'Statistics about imported documents by category and type';
COMMENT ON VIEW vw_documents_by_property IS 'Document count per property and category';



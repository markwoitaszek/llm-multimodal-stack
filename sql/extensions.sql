-- Enhanced PostgreSQL extensions for Supabase-like functionality

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Enable PostgREST API generation
CREATE SCHEMA IF NOT EXISTS api;

-- Create API views for external access
CREATE OR REPLACE VIEW api.documents AS
SELECT 
    id,
    filename,
    file_type,
    file_size,
    mime_type,
    metadata,
    created_at,
    updated_at
FROM documents;

CREATE OR REPLACE VIEW api.search_sessions AS
SELECT 
    id,
    session_name,
    query,
    results_count,
    created_at
FROM search_sessions;

-- Create API functions
CREATE OR REPLACE FUNCTION api.search_documents(
    search_query TEXT,
    file_type_filter TEXT DEFAULT NULL,
    limit_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    filename VARCHAR,
    file_type VARCHAR,
    relevance_score FLOAT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id,
        d.filename,
        d.file_type,
        CASE 
            WHEN d.filename ILIKE '%' || search_query || '%' THEN 1.0
            ELSE 0.5
        END as relevance_score
    FROM documents d
    WHERE 
        (file_type_filter IS NULL OR d.file_type = file_type_filter)
        AND (
            d.filename ILIKE '%' || search_query || '%'
            OR d.metadata::text ILIKE '%' || search_query || '%'
        )
    ORDER BY relevance_score DESC
    LIMIT limit_results;
END;
$$;

-- Create function to get document stats
CREATE OR REPLACE FUNCTION api.get_document_stats()
RETURNS JSON
LANGUAGE plpgsql
AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_documents', COUNT(*),
        'by_type', json_object_agg(file_type, type_count)
    ) INTO result
    FROM (
        SELECT 
            file_type,
            COUNT(*) as type_count
        FROM documents
        GROUP BY file_type
    ) stats;
    
    RETURN result;
END;
$$;

-- Row Level Security (RLS) setup for multi-tenancy
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE text_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_sessions ENABLE ROW LEVEL SECURITY;

-- Create policies (basic example - customize as needed)
CREATE POLICY "Documents are viewable by everyone" ON documents
    FOR SELECT USING (true);

CREATE POLICY "Search sessions are viewable by everyone" ON search_sessions
    FOR SELECT USING (true);

-- Create indexes for better API performance
CREATE INDEX IF NOT EXISTS idx_documents_filename_gin ON documents USING gin(filename gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_documents_created_at_desc ON documents(created_at DESC);

-- Enable trigram extension for better text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;


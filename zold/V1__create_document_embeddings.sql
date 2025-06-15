-- Migration: Create document_embeddings table and vector index
-- Description: Sets up the document_embeddings table with a vector column for storing embeddings
--              and creates an IVFFLAT index for efficient similarity search.

-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the document_embeddings table
CREATE TABLE IF NOT EXISTS document_embeddings (
    id BIGSERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL,
    content TEXT,
    embedding vector(1536),  -- Using 1536 dimensions (standard for OpenAI embeddings)
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Add a constraint to ensure document_id is always set
    CONSTRAINT document_embeddings_document_id_check CHECK (document_id IS NOT NULL)
);

-- Add a comment to describe the table
COMMENT ON TABLE document_embeddings IS 'Stores document embeddings for semantic search and similarity matching';

-- Create an index on document_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_document_embeddings_document_id 
    ON document_embeddings (document_id);

-- Create an IVFFLAT index for approximate nearest neighbor search
-- Note: Consider creating this after loading data for better index quality
CREATE INDEX IF NOT EXISTS idx_document_embeddings_embedding_ivfflat 
    ON document_embeddings USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to automatically update the updated_at column
CREATE TRIGGER update_document_embeddings_updated_at
BEFORE UPDATE ON document_embeddings
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Add a comment about the index
COMMENT ON INDEX idx_document_embeddings_embedding_ivfflat IS 'IVFFLAT index for approximate nearest neighbor search on document embeddings';

-- Example usage (commented out for reference):
-- INSERT INTO document_embeddings (document_id, content, embedding, metadata)
-- VALUES (1, 'Sample document text', '[0.1, 0.2, ...]'::vector, '{"source": "example"}'::jsonb);

-- Example search (commented out for reference):
-- SELECT id, content, embedding <=> '[0.1, 0.2, ...]'::vector as distance
-- FROM document_embeddings
-- ORDER BY distance
-- LIMIT 10;

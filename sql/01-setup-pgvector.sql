-- PostgreSQL pgvector Setup for Customer Matching POC
-- Run this script after deploying the infrastructure

-- Create the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema for customer data
CREATE SCHEMA IF NOT EXISTS customer_data;

-- Original customer table (migrated from SQL Server)
CREATE TABLE customer_data.customers (
    customer_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    industry VARCHAR(100),
    annual_revenue DECIMAL(15,2),
    employee_count INTEGER,
    website VARCHAR(255),
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Vector embeddings for similarity search
    company_name_embedding vector(1536),
    full_profile_embedding vector(1536),
    
    -- Computed fields for search
    search_text TEXT GENERATED ALWAYS AS (
        COALESCE(company_name, '') || ' ' ||
        COALESCE(contact_name, '') || ' ' ||
        COALESCE(email, '') || ' ' ||
        COALESCE(address_line1, '') || ' ' ||
        COALESCE(city, '') || ' ' ||
        COALESCE(state_province, '') || ' ' ||
        COALESCE(country, '') || ' ' ||
        COALESCE(industry, '') || ' ' ||
        COALESCE(website, '') || ' ' ||
        COALESCE(description, '')
    ) STORED
);

-- Incoming customer requests table
CREATE TABLE customer_data.incoming_customers (
    request_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    industry VARCHAR(100),
    annual_revenue DECIMAL(15,2),
    employee_count INTEGER,
    website VARCHAR(255),
    description TEXT,
    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Vector embeddings
    company_name_embedding vector(1536),
    full_profile_embedding vector(1536),
    
    -- Processing status
    processing_status VARCHAR(20) DEFAULT 'pending',
    processed_date TIMESTAMP,
    
    -- Search text
    search_text TEXT GENERATED ALWAYS AS (
        COALESCE(company_name, '') || ' ' ||
        COALESCE(contact_name, '') || ' ' ||
        COALESCE(email, '') || ' ' ||
        COALESCE(address_line1, '') || ' ' ||
        COALESCE(city, '') || ' ' ||
        COALESCE(state_province, '') || ' ' ||
        COALESCE(country, '') || ' ' ||
        COALESCE(industry, '') || ' ' ||
        COALESCE(website, '') || ' ' ||
        COALESCE(description, '')
    ) STORED
);

-- Customer matching results table
CREATE TABLE customer_data.matching_results (
    match_id SERIAL PRIMARY KEY,
    incoming_customer_id INTEGER REFERENCES customer_data.incoming_customers(request_id),
    matched_customer_id INTEGER REFERENCES customer_data.customers(customer_id),
    similarity_score DECIMAL(5,4),
    match_type VARCHAR(50), -- 'exact', 'high_confidence', 'potential', 'low_confidence'
    match_criteria JSONB, -- Store details about what matched
    confidence_level DECIMAL(5,4),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_notes TEXT
);

-- Create indexes for performance
CREATE INDEX idx_customers_company_name ON customer_data.customers(company_name);
CREATE INDEX idx_customers_email ON customer_data.customers(email);
CREATE INDEX idx_customers_phone ON customer_data.customers(phone);
CREATE INDEX idx_customers_search_text ON customer_data.customers USING gin(to_tsvector('english', search_text));

-- Vector similarity indexes using HNSW (Hierarchical Navigable Small World)
CREATE INDEX idx_customers_company_embedding ON customer_data.customers 
USING hnsw (company_name_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_customers_profile_embedding ON customer_data.customers 
USING hnsw (full_profile_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_incoming_company_embedding ON customer_data.incoming_customers 
USING hnsw (company_name_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

CREATE INDEX idx_incoming_profile_embedding ON customer_data.incoming_customers 
USING hnsw (full_profile_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Indexes for matching results
CREATE INDEX idx_matching_results_incoming ON customer_data.matching_results(incoming_customer_id);
CREATE INDEX idx_matching_results_matched ON customer_data.matching_results(matched_customer_id);
CREATE INDEX idx_matching_results_score ON customer_data.matching_results(similarity_score DESC);

-- Function to calculate similarity between customers
CREATE OR REPLACE FUNCTION customer_data.calculate_similarity(
    customer1_embedding vector(1536),
    customer2_embedding vector(1536)
) RETURNS DECIMAL(5,4) AS $$
BEGIN
    RETURN 1 - (customer1_embedding <=> customer2_embedding);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to find similar customers
CREATE OR REPLACE FUNCTION customer_data.find_similar_customers(
    input_embedding vector(1536),
    similarity_threshold DECIMAL(5,4) DEFAULT 0.8,
    max_results INTEGER DEFAULT 10
) RETURNS TABLE (
    customer_id INTEGER,
    company_name VARCHAR(255),
    similarity_score DECIMAL(5,4),
    contact_name VARCHAR(255),
    email VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.customer_id,
        c.company_name,
        (1 - (c.full_profile_embedding <=> input_embedding))::DECIMAL(5,4) as similarity_score,
        c.contact_name,
        c.email,
        c.city,
        c.country
    FROM customer_data.customers c
    WHERE c.full_profile_embedding IS NOT NULL
    AND (1 - (c.full_profile_embedding <=> input_embedding)) >= similarity_threshold
    ORDER BY c.full_profile_embedding <=> input_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to process incoming customer and find matches
CREATE OR REPLACE FUNCTION customer_data.process_incoming_customer(
    p_request_id INTEGER
) RETURNS TABLE (
    match_id INTEGER,
    matched_customer_id INTEGER,
    similarity_score DECIMAL(5,4),
    match_type VARCHAR(50)
) AS $$
DECLARE
    incoming_record RECORD;
    match_record RECORD;
    new_match_id INTEGER;
BEGIN
    -- Get the incoming customer record
    SELECT * INTO incoming_record 
    FROM customer_data.incoming_customers 
    WHERE request_id = p_request_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incoming customer with ID % not found', p_request_id;
    END IF;
    
    -- Find matches using vector similarity
    FOR match_record IN
        SELECT * FROM customer_data.find_similar_customers(
            incoming_record.full_profile_embedding,
            0.7, -- Lower threshold for more matches
            5    -- Top 5 matches
        )
    LOOP
        -- Determine match type based on similarity score
        DECLARE
            match_type_val VARCHAR(50);
        BEGIN
            IF match_record.similarity_score >= 0.95 THEN
                match_type_val := 'exact';
            ELSIF match_record.similarity_score >= 0.85 THEN
                match_type_val := 'high_confidence';
            ELSIF match_record.similarity_score >= 0.75 THEN
                match_type_val := 'potential';
            ELSE
                match_type_val := 'low_confidence';
            END IF;
            
            -- Insert match result
            INSERT INTO customer_data.matching_results (
                incoming_customer_id,
                matched_customer_id,
                similarity_score,
                match_type,
                confidence_level,
                match_criteria
            ) VALUES (
                p_request_id,
                match_record.customer_id,
                match_record.similarity_score,
                match_type_val,
                match_record.similarity_score,
                jsonb_build_object(
                    'vector_similarity', match_record.similarity_score,
                    'matched_company', match_record.company_name,
                    'matched_contact', match_record.contact_name
                )
            ) RETURNING customer_data.matching_results.match_id INTO new_match_id;
            
            -- Return the match
            match_id := new_match_id;
            matched_customer_id := match_record.customer_id;
            similarity_score := match_record.similarity_score;
            match_type := match_type_val;
            RETURN NEXT;
        END;
    END LOOP;
    
    -- Update processing status
    UPDATE customer_data.incoming_customers 
    SET processing_status = 'processed', processed_date = CURRENT_TIMESTAMP
    WHERE request_id = p_request_id;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Create a view for easy querying of match results
CREATE OR REPLACE VIEW customer_data.v_customer_matches AS
SELECT 
    mr.match_id,
    mr.incoming_customer_id,
    ic.company_name as incoming_company,
    ic.contact_name as incoming_contact,
    ic.email as incoming_email,
    mr.matched_customer_id,
    c.company_name as matched_company,
    c.contact_name as matched_contact,
    c.email as matched_email,
    mr.similarity_score,
    mr.match_type,
    mr.confidence_level,
    mr.match_criteria,
    mr.created_date,
    mr.reviewed,
    mr.reviewer_notes
FROM customer_data.matching_results mr
JOIN customer_data.incoming_customers ic ON mr.incoming_customer_id = ic.request_id
JOIN customer_data.customers c ON mr.matched_customer_id = c.customer_id
ORDER BY mr.similarity_score DESC;

-- Grant permissions (adjust as needed for your security model)
-- GRANT USAGE ON SCHEMA customer_data TO your_application_user;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA customer_data TO your_application_user;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA customer_data TO your_application_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA customer_data TO your_application_user;

-- Sample data insertion (for testing)
-- use import_customers.py to populate the database

COMMIT;

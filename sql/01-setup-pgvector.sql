-- PostgreSQL pgvector Setup for Customer Matching POC
-- Run this script before 02-functions.sql

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

-- View for easy querying of match results
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

-- All functions and stored procedures have been moved to 02-functions.sql
-- Please run 02-functions.sql after this file to create all required functions.

COMMIT;

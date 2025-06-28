-- PostgreSQL Functions and Stored Procedures for Customer Matching
-- This file contains all the functions and stored procedures used for customer matching
-- Run this after the main setup script (01-setup-pgvector.sql)

-- Function to calculate similarity between customers
CREATE OR REPLACE FUNCTION customer_data.calculate_similarity(
    customer1_embedding vector(1536),
    customer2_embedding vector(1536)
) RETURNS DECIMAL(5,4) AS $$
BEGIN
    RETURN 1 - (customer1_embedding <=> customer2_embedding);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to find similar customers using vector similarity
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

-- Function to find exact matches based on key fields
CREATE OR REPLACE FUNCTION customer_data.find_exact_matches(
    p_request_id INTEGER
) RETURNS TABLE (
    customer_id INTEGER,
    company_name VARCHAR(255),
    match_score DECIMAL(5,4),
    match_criteria JSONB
) AS $$
DECLARE
    incoming_record RECORD;
    match_record RECORD;
    match_score DECIMAL(5,4);
    match_criteria JSONB;
BEGIN
    -- Get the incoming customer record
    SELECT * INTO incoming_record 
    FROM customer_data.incoming_customers 
    WHERE request_id = p_request_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incoming customer with ID % not found', p_request_id;
    END IF;
    
    -- Find exact matches
    FOR match_record IN
        SELECT 
            c.customer_id,
            c.company_name,
            c.email,
            c.phone,
            c.contact_name
        FROM customer_data.customers c
        WHERE 
            -- Exact company name match (case insensitive)
            (incoming_record.company_name IS NOT NULL AND 
             LOWER(c.company_name) = LOWER(incoming_record.company_name))
            OR
            -- Exact email match (case insensitive)
            (incoming_record.email IS NOT NULL AND 
             LOWER(c.email) = LOWER(incoming_record.email))
            OR
            -- Exact phone match (normalized)
            (incoming_record.phone IS NOT NULL AND 
             REGEXP_REPLACE(c.phone, '[^0-9]', '', 'g') = 
             REGEXP_REPLACE(incoming_record.phone, '[^0-9]', '', 'g'))
    LOOP
        -- Calculate match score based on number of exact matches
        match_score := 0.0;
        match_criteria := '{}'::jsonb;
        
        -- Company name exact match
        IF LOWER(match_record.company_name) = LOWER(incoming_record.company_name) THEN
            match_score := match_score + 0.4;
            match_criteria := match_criteria || jsonb_build_object('exact_company_name', true);
        END IF;
        
        -- Email exact match
        IF LOWER(match_record.email) = LOWER(incoming_record.email) THEN
            match_score := match_score + 0.4;
            match_criteria := match_criteria || jsonb_build_object('exact_email', true);
        END IF;
        
        -- Phone exact match
        IF REGEXP_REPLACE(match_record.phone, '[^0-9]', '', 'g') = 
           REGEXP_REPLACE(incoming_record.phone, '[^0-9]', '', 'g') THEN
            match_score := match_score + 0.2;
            match_criteria := match_criteria || jsonb_build_object('exact_phone', true);
        END IF;
        
        -- Return match if score is above threshold
        IF match_score >= 0.4 THEN
            customer_id := match_record.customer_id;
            company_name := match_record.company_name;
            RETURN NEXT;
        END IF;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to find fuzzy string matches
CREATE OR REPLACE FUNCTION customer_data.find_fuzzy_matches(
    p_request_id INTEGER,
    similarity_threshold DECIMAL(5,4) DEFAULT 0.8
) RETURNS TABLE (
    customer_id INTEGER,
    company_name VARCHAR(255),
    similarity_score DECIMAL(5,4),
    match_criteria JSONB
) AS $$
DECLARE
    incoming_record RECORD;
    match_record RECORD;
BEGIN
    -- Get the incoming customer record
    SELECT * INTO incoming_record 
    FROM customer_data.incoming_customers 
    WHERE request_id = p_request_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incoming customer with ID % not found', p_request_id;
    END IF;
    
    -- Find fuzzy matches using PostgreSQL similarity function
    FOR match_record IN
        SELECT 
            c.customer_id,
            c.company_name,
            GREATEST(
                similarity(LOWER(c.company_name), LOWER(incoming_record.company_name)),
                similarity(LOWER(COALESCE(c.contact_name, '')), LOWER(COALESCE(incoming_record.contact_name, '')))
            ) as similarity_score
        FROM customer_data.customers c
        WHERE 
            incoming_record.company_name IS NOT NULL
            AND similarity(LOWER(c.company_name), LOWER(incoming_record.company_name)) >= similarity_threshold
        ORDER BY similarity_score DESC
        LIMIT 10
    LOOP
        customer_id := match_record.customer_id;
        company_name := match_record.company_name;
        similarity_score := match_record.similarity_score;
        match_criteria := jsonb_build_object(
            'fuzzy_company_name', true,
            'similarity_score', match_record.similarity_score
        );
        RETURN NEXT;
    END LOOP;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Original function to process incoming customer (vector similarity only)
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

-- Enhanced function to process incoming customer with hybrid matching
CREATE OR REPLACE FUNCTION customer_data.process_incoming_customer_hybrid(
    p_request_id INTEGER
) RETURNS TABLE (
    match_id INTEGER,
    matched_customer_id INTEGER,
    similarity_score DECIMAL(5,4),
    match_type VARCHAR(50),
    match_method VARCHAR(50)
) AS $$
DECLARE
    incoming_record RECORD;
    match_record RECORD;
    new_match_id INTEGER;
    match_type_val VARCHAR(50);
    match_method_val VARCHAR(50);
BEGIN
    -- Get the incoming customer record
    SELECT * INTO incoming_record 
    FROM customer_data.incoming_customers 
    WHERE request_id = p_request_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incoming customer with ID % not found', p_request_id;
    END IF;
    
    -- Step 1: Try exact matches first
    FOR match_record IN
        SELECT * FROM customer_data.find_exact_matches(p_request_id)
    LOOP
        match_type_val := 'exact';
        match_method_val := 'exact_fields';
        
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
            match_record.match_score,
            match_type_val,
            match_record.match_score,
            match_record.match_criteria
        ) RETURNING customer_data.matching_results.match_id INTO new_match_id;
        
        -- Return the match
        match_id := new_match_id;
        matched_customer_id := match_record.customer_id;
        similarity_score := match_record.match_score;
        match_type := match_type_val;
        match_method := match_method_val;
        RETURN NEXT;
    END LOOP;
    
    -- Step 2: If no exact matches, try vector similarity
    IF NOT FOUND THEN
        FOR match_record IN
            SELECT * FROM customer_data.find_similar_customers(
                incoming_record.full_profile_embedding,
                0.7, -- Lower threshold for more matches
                5    -- Top 5 matches
            )
        LOOP
            -- Determine match type based on similarity score
            IF match_record.similarity_score >= 0.95 THEN
                match_type_val := 'exact';
            ELSIF match_record.similarity_score >= 0.85 THEN
                match_type_val := 'high_confidence';
            ELSIF match_record.similarity_score >= 0.75 THEN
                match_type_val := 'potential';
            ELSE
                match_type_val := 'low_confidence';
            END IF;
            
            match_method_val := 'vector_similarity';
            
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
            match_method := match_method_val;
            RETURN NEXT;
        END LOOP;
    END IF;
    
    -- Step 3: If still no matches, try fuzzy string matching
    IF NOT FOUND THEN
        FOR match_record IN
            SELECT * FROM customer_data.find_fuzzy_matches(p_request_id, 0.8)
        LOOP
            match_type_val := 'potential';
            match_method_val := 'fuzzy_string';
            
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
                match_record.match_criteria
            ) RETURNING customer_data.matching_results.match_id INTO new_match_id;
            
            -- Return the match
            match_id := new_match_id;
            matched_customer_id := match_record.customer_id;
            similarity_score := match_record.similarity_score;
            match_type := match_type_val;
            match_method := match_method_val;
            RETURN NEXT;
        END LOOP;
    END IF;
    
    -- Update processing status
    UPDATE customer_data.incoming_customers 
    SET processing_status = 'processed', processed_date = CURRENT_TIMESTAMP
    WHERE request_id = p_request_id;
    
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to apply business rules to match results
CREATE OR REPLACE FUNCTION customer_data.apply_business_rules(
    p_request_id INTEGER
) RETURNS VOID AS $$
DECLARE
    match_record RECORD;
    incoming_record RECORD;
    customer_record RECORD;
BEGIN
    -- Get the incoming customer record
    SELECT * INTO incoming_record 
    FROM customer_data.incoming_customers 
    WHERE request_id = p_request_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Incoming customer with ID % not found', p_request_id;
    END IF;
    
    -- Apply business rules to all matches for this request
    FOR match_record IN
        SELECT mr.*, c.industry as customer_industry, c.city as customer_city, 
               c.country as customer_country, c.annual_revenue as customer_revenue
        FROM customer_data.matching_results mr
        JOIN customer_data.customers c ON mr.matched_customer_id = c.customer_id
        WHERE mr.incoming_customer_id = p_request_id
    LOOP
        -- Get the matched customer details
        SELECT * INTO customer_record 
        FROM customer_data.customers 
        WHERE customer_id = match_record.matched_customer_id;
        
        -- Apply business rules and update confidence level
        DECLARE
            new_confidence DECIMAL(5,4) := match_record.confidence_level;
            updated_criteria JSONB := match_record.match_criteria;
        BEGIN
            -- Industry match boost
            IF (incoming_record.industry IS NOT NULL AND customer_record.industry IS NOT NULL AND
                LOWER(incoming_record.industry) = LOWER(customer_record.industry)) THEN
                new_confidence := new_confidence * 1.2;
                updated_criteria := updated_criteria || jsonb_build_object('industry_match', true);
            END IF;
            
            -- Location match boost
            IF (incoming_record.city IS NOT NULL AND customer_record.city IS NOT NULL AND
                LOWER(incoming_record.city) = LOWER(customer_record.city)) THEN
                new_confidence := new_confidence * 1.1;
                updated_criteria := updated_criteria || jsonb_build_object('location_match', true);
            END IF;
            
            -- Country mismatch penalty
            IF (incoming_record.country IS NOT NULL AND customer_record.country IS NOT NULL AND
                LOWER(incoming_record.country) != LOWER(customer_record.country)) THEN
                new_confidence := new_confidence * 0.8;
                updated_criteria := updated_criteria || jsonb_build_object('country_mismatch', true);
            END IF;
            
            -- Revenue size similarity boost
            IF (incoming_record.annual_revenue IS NOT NULL AND customer_record.annual_revenue IS NOT NULL) THEN
                DECLARE
                    revenue_ratio DECIMAL;
                BEGIN
                    revenue_ratio := LEAST(incoming_record.annual_revenue, customer_record.annual_revenue) / 
                                   GREATEST(incoming_record.annual_revenue, customer_record.annual_revenue);
                    IF revenue_ratio > 0.8 THEN
                        new_confidence := new_confidence * 1.1;
                        updated_criteria := updated_criteria || jsonb_build_object('revenue_similar', true);
                    END IF;
                END;
            END IF;
            
            -- Update the match record with new confidence and criteria
            UPDATE customer_data.matching_results 
            SET confidence_level = new_confidence,
                match_criteria = updated_criteria
            WHERE match_id = match_record.match_id;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to get match statistics
CREATE OR REPLACE FUNCTION customer_data.get_match_statistics(
    p_request_id INTEGER
) RETURNS TABLE (
    total_matches INTEGER,
    exact_matches INTEGER,
    high_confidence_matches INTEGER,
    potential_matches INTEGER,
    low_confidence_matches INTEGER,
    avg_confidence DECIMAL(5,4),
    processing_time_ms INTEGER
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    -- Get processing time
    SELECT processed_date - request_date INTO start_time
    FROM customer_data.incoming_customers 
    WHERE request_id = p_request_id;
    
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_matches,
        COUNT(*) FILTER (WHERE match_type = 'exact')::INTEGER as exact_matches,
        COUNT(*) FILTER (WHERE match_type = 'high_confidence')::INTEGER as high_confidence_matches,
        COUNT(*) FILTER (WHERE match_type = 'potential')::INTEGER as potential_matches,
        COUNT(*) FILTER (WHERE match_type = 'low_confidence')::INTEGER as low_confidence_matches,
        AVG(confidence_level)::DECIMAL(5,4) as avg_confidence,
        EXTRACT(EPOCH FROM (processed_date - request_date)) * 1000::INTEGER as processing_time_ms
    FROM customer_data.matching_results mr
    JOIN customer_data.incoming_customers ic ON mr.incoming_customer_id = ic.request_id
    WHERE mr.incoming_customer_id = p_request_id;
END;
$$ LANGUAGE plpgsql;

COMMIT; 
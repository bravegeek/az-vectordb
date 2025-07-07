-- Enhanced Database View for Matching Results Display
-- This file creates the v_detailed_matches view with comprehensive comparison capabilities
-- Run this after the main setup scripts (01-setup-pgvector.sql and 02-functions.sql)
--
-- AZURE COMPATIBILITY: This view uses alternative string matching methods that don't require
-- the pg_trgm extension, making it compatible with Azure Database for PostgreSQL

-- Drop existing view if it exists
DROP VIEW IF EXISTS customer_data.v_detailed_matches;

-- Create enhanced view for detailed display purposes
CREATE OR REPLACE VIEW customer_data.v_detailed_matches AS
SELECT 
    mr.match_id,
    -- Incoming customer details
    ic.request_id,
    ic.company_name as incoming_company,
    ic.contact_name as incoming_contact,
    ic.email as incoming_email,
    ic.phone as incoming_phone,
    ic.address_line1 as incoming_address_line1,
    ic.address_line2 as incoming_address_line2,
    ic.city as incoming_city,
    ic.state_province as incoming_state_province,
    ic.postal_code as incoming_postal_code,
    ic.country as incoming_country,
    ic.industry as incoming_industry,
    ic.annual_revenue as incoming_revenue,
    ic.employee_count as incoming_employee_count,
    ic.website as incoming_website,
    ic.description as incoming_description,
    ic.processing_status,
    ic.request_date,
    ic.processed_date,
    
    -- Matched customer details  
    c.customer_id,
    c.company_name as matched_company,
    c.contact_name as matched_contact,
    c.email as matched_email,
    c.phone as matched_phone,
    c.address_line1 as matched_address_line1,
    c.address_line2 as matched_address_line2,
    c.city as matched_city,
    c.state_province as matched_state_province,
    c.postal_code as matched_postal_code,
    c.country as matched_country,
    c.industry as matched_industry,
    c.annual_revenue as matched_revenue,
    c.employee_count as matched_employee_count,
    c.website as matched_website,
    c.description as matched_description,
    c.created_date as matched_created_date,
    c.updated_date as matched_updated_date,
    
    -- Match details
    mr.similarity_score,
    mr.match_type,
    mr.confidence_level,
    mr.match_criteria,
    mr.created_date as match_created_date,
    mr.reviewed,
    mr.reviewer_notes,
    
    -- Confidence categorization
    CASE 
        WHEN mr.confidence_level >= 0.9 THEN 'High'
        WHEN mr.confidence_level >= 0.7 THEN 'Medium'
        WHEN mr.confidence_level >= 0.5 THEN 'Low'
        ELSE 'Very Low'
    END as confidence_category,
    
    -- Confidence level for badges/indicators
    CASE 
        WHEN mr.confidence_level >= 0.9 THEN '🟢'
        WHEN mr.confidence_level >= 0.7 THEN '🟡'
        WHEN mr.confidence_level >= 0.5 THEN '🟠'
        ELSE '🔴'
    END as confidence_indicator,
    
    -- Match recommendation
    CASE 
        WHEN mr.confidence_level >= 0.95 THEN 'Auto-approve'
        WHEN mr.confidence_level >= 0.85 THEN 'Review recommended'
        WHEN mr.confidence_level >= 0.7 THEN 'Needs review'
        ELSE 'Needs attention'
    END as recommendation,
    
    -- Field comparison flags for company name
    CASE 
        WHEN LOWER(TRIM(ic.company_name)) = LOWER(TRIM(c.company_name)) THEN 'exact'
        WHEN LOWER(TRIM(ic.company_name)) LIKE '%' || LOWER(TRIM(c.company_name)) || '%' 
             OR LOWER(TRIM(c.company_name)) LIKE '%' || LOWER(TRIM(ic.company_name)) || '%' THEN 'similar'
        WHEN ABS(LENGTH(LOWER(TRIM(ic.company_name))) - LENGTH(LOWER(TRIM(c.company_name)))) <= 3 
             AND LENGTH(LOWER(TRIM(ic.company_name))) > 3 
             AND LENGTH(LOWER(TRIM(c.company_name))) > 3 THEN 'related'
        ELSE 'different'
    END as company_name_match,
    
    -- Field comparison flags for contact name
    CASE 
        WHEN ic.contact_name IS NULL AND c.contact_name IS NULL THEN 'missing'
        WHEN ic.contact_name IS NULL OR c.contact_name IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.contact_name)) = LOWER(TRIM(c.contact_name)) THEN 'exact'
        WHEN LOWER(TRIM(ic.contact_name)) LIKE '%' || LOWER(TRIM(c.contact_name)) || '%' 
             OR LOWER(TRIM(c.contact_name)) LIKE '%' || LOWER(TRIM(ic.contact_name)) || '%' THEN 'similar'
        WHEN ABS(LENGTH(LOWER(TRIM(ic.contact_name))) - LENGTH(LOWER(TRIM(c.contact_name)))) <= 2 
             AND LENGTH(LOWER(TRIM(ic.contact_name))) > 2 
             AND LENGTH(LOWER(TRIM(c.contact_name))) > 2 THEN 'related'
        ELSE 'different'
    END as contact_name_match,
    
    -- Field comparison flags for email
    CASE 
        WHEN ic.email IS NULL AND c.email IS NULL THEN 'missing'
        WHEN ic.email IS NULL OR c.email IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.email)) = LOWER(TRIM(c.email)) THEN 'exact'
        WHEN LOWER(TRIM(ic.email)) LIKE '%' || LOWER(TRIM(c.email)) || '%' 
             OR LOWER(TRIM(c.email)) LIKE '%' || LOWER(TRIM(ic.email)) || '%' THEN 'similar'
        WHEN split_part(LOWER(TRIM(ic.email)), '@', 2) = split_part(LOWER(TRIM(c.email)), '@', 2) THEN 'same_domain'
        ELSE 'different'
    END as email_match,
    
    -- Field comparison flags for phone
    CASE 
        WHEN ic.phone IS NULL AND c.phone IS NULL THEN 'missing'
        WHEN ic.phone IS NULL OR c.phone IS NULL THEN 'missing'
        WHEN REGEXP_REPLACE(ic.phone, '[^0-9]', '', 'g') = 
             REGEXP_REPLACE(c.phone, '[^0-9]', '', 'g') THEN 'exact'
        WHEN LENGTH(REGEXP_REPLACE(ic.phone, '[^0-9]', '', 'g')) >= 10 
             AND LENGTH(REGEXP_REPLACE(c.phone, '[^0-9]', '', 'g')) >= 10
             AND RIGHT(REGEXP_REPLACE(ic.phone, '[^0-9]', '', 'g'), 10) = 
                 RIGHT(REGEXP_REPLACE(c.phone, '[^0-9]', '', 'g'), 10) THEN 'similar'
        ELSE 'different'
    END as phone_match,
    
    -- Field comparison flags for industry
    CASE 
        WHEN ic.industry IS NULL AND c.industry IS NULL THEN 'missing'
        WHEN ic.industry IS NULL OR c.industry IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.industry)) = LOWER(TRIM(c.industry)) THEN 'exact'
        WHEN LOWER(TRIM(ic.industry)) LIKE '%' || LOWER(TRIM(c.industry)) || '%' 
             OR LOWER(TRIM(c.industry)) LIKE '%' || LOWER(TRIM(ic.industry)) || '%' THEN 'similar'
        ELSE 'different'
    END as industry_match,
    
    -- Field comparison flags for annual revenue
    CASE 
        WHEN ic.annual_revenue IS NULL AND c.annual_revenue IS NULL THEN 'missing'
        WHEN ic.annual_revenue IS NULL OR c.annual_revenue IS NULL THEN 'missing'
        WHEN ic.annual_revenue = c.annual_revenue THEN 'exact'
        WHEN ABS(ic.annual_revenue - c.annual_revenue) / GREATEST(ic.annual_revenue, c.annual_revenue) <= 0.1 THEN 'similar'
        WHEN ABS(ic.annual_revenue - c.annual_revenue) / GREATEST(ic.annual_revenue, c.annual_revenue) <= 0.25 THEN 'related'
        ELSE 'different'
    END as revenue_match,
    
    -- Field comparison flags for employee count
    CASE 
        WHEN ic.employee_count IS NULL AND c.employee_count IS NULL THEN 'missing'
        WHEN ic.employee_count IS NULL OR c.employee_count IS NULL THEN 'missing'
        WHEN ic.employee_count = c.employee_count THEN 'exact'
        WHEN ABS(ic.employee_count - c.employee_count) / GREATEST(ic.employee_count, c.employee_count) <= 0.2 THEN 'similar'
        WHEN ABS(ic.employee_count - c.employee_count) / GREATEST(ic.employee_count, c.employee_count) <= 0.5 THEN 'related'
        ELSE 'different'
    END as employee_count_match,
    
    -- Field comparison flags for city
    CASE 
        WHEN ic.city IS NULL AND c.city IS NULL THEN 'missing'
        WHEN ic.city IS NULL OR c.city IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.city)) = LOWER(TRIM(c.city)) THEN 'exact'
        WHEN LOWER(TRIM(ic.city)) LIKE '%' || LOWER(TRIM(c.city)) || '%' 
             OR LOWER(TRIM(c.city)) LIKE '%' || LOWER(TRIM(ic.city)) || '%' THEN 'similar'
        ELSE 'different'
    END as city_match,
    
    -- Field comparison flags for state/province
    CASE 
        WHEN ic.state_province IS NULL AND c.state_province IS NULL THEN 'missing'
        WHEN ic.state_province IS NULL OR c.state_province IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.state_province)) = LOWER(TRIM(c.state_province)) THEN 'exact'
        WHEN LOWER(TRIM(ic.state_province)) LIKE '%' || LOWER(TRIM(c.state_province)) || '%' 
             OR LOWER(TRIM(c.state_province)) LIKE '%' || LOWER(TRIM(ic.state_province)) || '%' THEN 'similar'
        ELSE 'different'
    END as state_province_match,
    
    -- Field comparison flags for country
    CASE 
        WHEN ic.country IS NULL AND c.country IS NULL THEN 'missing'
        WHEN ic.country IS NULL OR c.country IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.country)) = LOWER(TRIM(c.country)) THEN 'exact'
        WHEN LOWER(TRIM(ic.country)) LIKE '%' || LOWER(TRIM(c.country)) || '%' 
             OR LOWER(TRIM(c.country)) LIKE '%' || LOWER(TRIM(ic.country)) || '%' THEN 'similar'
        ELSE 'different'
    END as country_match,
    
    -- Field comparison flags for website
    CASE 
        WHEN ic.website IS NULL AND c.website IS NULL THEN 'missing'
        WHEN ic.website IS NULL OR c.website IS NULL THEN 'missing'
        WHEN LOWER(TRIM(ic.website)) = LOWER(TRIM(c.website)) THEN 'exact'
        WHEN LOWER(TRIM(ic.website)) LIKE '%' || LOWER(TRIM(c.website)) || '%' 
             OR LOWER(TRIM(c.website)) LIKE '%' || LOWER(TRIM(ic.website)) || '%' THEN 'similar'
        ELSE 'different'
    END as website_match,
    
    -- Overall match quality score (0-100)
    ROUND(
        (
            CASE 
                WHEN LOWER(TRIM(ic.company_name)) = LOWER(TRIM(c.company_name)) THEN 25
                WHEN LOWER(TRIM(ic.company_name)) LIKE '%' || LOWER(TRIM(c.company_name)) || '%' 
                     OR LOWER(TRIM(c.company_name)) LIKE '%' || LOWER(TRIM(ic.company_name)) || '%' THEN 20
                WHEN ABS(LENGTH(LOWER(TRIM(ic.company_name))) - LENGTH(LOWER(TRIM(c.company_name)))) <= 3 
                     AND LENGTH(LOWER(TRIM(ic.company_name))) > 3 
                     AND LENGTH(LOWER(TRIM(c.company_name))) > 3 THEN 15
                ELSE 0
            END
            +
            CASE 
                WHEN ic.contact_name IS NOT NULL AND c.contact_name IS NOT NULL THEN
                    CASE 
                        WHEN LOWER(TRIM(ic.contact_name)) = LOWER(TRIM(c.contact_name)) THEN 15
                        WHEN LOWER(TRIM(ic.contact_name)) LIKE '%' || LOWER(TRIM(c.contact_name)) || '%' 
                             OR LOWER(TRIM(c.contact_name)) LIKE '%' || LOWER(TRIM(ic.contact_name)) || '%' THEN 12
                        WHEN ABS(LENGTH(LOWER(TRIM(ic.contact_name))) - LENGTH(LOWER(TRIM(c.contact_name)))) <= 2 
                             AND LENGTH(LOWER(TRIM(ic.contact_name))) > 2 
                             AND LENGTH(LOWER(TRIM(c.contact_name))) > 2 THEN 8
                        ELSE 0
                    END
                ELSE 0
            END
            +
            CASE 
                WHEN ic.email IS NOT NULL AND c.email IS NOT NULL THEN
                    CASE 
                        WHEN LOWER(TRIM(ic.email)) = LOWER(TRIM(c.email)) THEN 20
                        WHEN split_part(LOWER(TRIM(ic.email)), '@', 2) = split_part(LOWER(TRIM(c.email)), '@', 2) THEN 10
                        ELSE 0
                    END
                ELSE 0
            END
            +
            CASE 
                WHEN ic.phone IS NOT NULL AND c.phone IS NOT NULL THEN
                    CASE 
                        WHEN REGEXP_REPLACE(ic.phone, '[^0-9]', '', 'g') = 
                             REGEXP_REPLACE(c.phone, '[^0-9]', '', 'g') THEN 15
                        WHEN RIGHT(REGEXP_REPLACE(ic.phone, '[^0-9]', '', 'g'), 10) = 
                             RIGHT(REGEXP_REPLACE(c.phone, '[^0-9]', '', 'g'), 10) THEN 10
                        ELSE 0
                    END
                ELSE 0
            END
            +
            CASE 
                WHEN ic.industry IS NOT NULL AND c.industry IS NOT NULL THEN
                    CASE 
                        WHEN LOWER(TRIM(ic.industry)) = LOWER(TRIM(c.industry)) THEN 10
                        WHEN LOWER(TRIM(ic.industry)) LIKE '%' || LOWER(TRIM(c.industry)) || '%' 
                             OR LOWER(TRIM(c.industry)) LIKE '%' || LOWER(TRIM(ic.industry)) || '%' THEN 8
                        ELSE 0
                    END
                ELSE 0
            END
            +
            CASE 
                WHEN ic.city IS NOT NULL AND c.city IS NOT NULL THEN
                    CASE 
                        WHEN LOWER(TRIM(ic.city)) = LOWER(TRIM(c.city)) THEN 10
                        WHEN LOWER(TRIM(ic.city)) LIKE '%' || LOWER(TRIM(c.city)) || '%' 
                             OR LOWER(TRIM(c.city)) LIKE '%' || LOWER(TRIM(ic.city)) || '%' THEN 8
                        ELSE 0
                    END
                ELSE 0
            END
            +
            CASE 
                WHEN ic.country IS NOT NULL AND c.country IS NOT NULL THEN
                    CASE 
                        WHEN LOWER(TRIM(ic.country)) = LOWER(TRIM(c.country)) THEN 5
                        ELSE 0
                    END
                ELSE 0
            END
        ), 0
    ) as match_quality_score,
    
    -- Processing time calculation
    CASE 
        WHEN ic.processed_date IS NOT NULL AND ic.request_date IS NOT NULL THEN
            EXTRACT(EPOCH FROM (ic.processed_date - ic.request_date)) * 1000
        ELSE NULL
    END as processing_time_ms,
    
    -- Record counts for summary calculations
    COUNT(*) OVER (PARTITION BY ic.request_id) as total_matches_for_request,
    COUNT(*) OVER (PARTITION BY ic.request_id, CASE WHEN mr.confidence_level >= 0.9 THEN 1 END) as high_confidence_matches,
    COUNT(*) OVER (PARTITION BY ic.request_id, CASE WHEN mr.confidence_level >= 0.7 AND mr.confidence_level < 0.9 THEN 1 END) as medium_confidence_matches,
    COUNT(*) OVER (PARTITION BY ic.request_id, CASE WHEN mr.confidence_level < 0.7 THEN 1 END) as low_confidence_matches

FROM customer_data.matching_results mr
    JOIN customer_data.incoming_customers ic ON mr.incoming_customer_id = ic.request_id
    JOIN customer_data.customers c ON mr.matched_customer_id = c.customer_id
ORDER BY mr.confidence_level DESC, mr.similarity_score DESC;

-- Create indexes for the view to improve performance
CREATE INDEX IF NOT EXISTS idx_matching_results_confidence_desc 
ON customer_data.matching_results(confidence_level DESC);

CREATE INDEX IF NOT EXISTS idx_matching_results_similarity_desc 
ON customer_data.matching_results(similarity_score DESC);

CREATE INDEX IF NOT EXISTS idx_matching_results_incoming_confidence 
ON customer_data.matching_results(incoming_customer_id, confidence_level DESC);

CREATE INDEX IF NOT EXISTS idx_matching_results_type_confidence 
ON customer_data.matching_results(match_type, confidence_level DESC);

CREATE INDEX IF NOT EXISTS idx_matching_results_created_date 
ON customer_data.matching_results(created_date DESC);

CREATE INDEX IF NOT EXISTS idx_incoming_customers_processed_date 
ON customer_data.incoming_customers(processed_date DESC);

CREATE INDEX IF NOT EXISTS idx_incoming_customers_processing_status 
ON customer_data.incoming_customers(processing_status);

-- Create a summary statistics view
CREATE OR REPLACE VIEW customer_data.v_matching_summary AS
SELECT 
    -- Overall statistics
    COUNT(DISTINCT ic.request_id) as total_incoming_customers,
    COUNT(DISTINCT CASE WHEN ic.processing_status = 'completed' THEN ic.request_id END) as processed_customers,
    COUNT(DISTINCT CASE WHEN ic.processing_status = 'pending' THEN ic.request_id END) as pending_customers,
    COUNT(mr.match_id) as total_matches,
    COUNT(CASE WHEN mr.reviewed = true THEN mr.match_id END) as reviewed_matches,
    COUNT(CASE WHEN mr.reviewed = false THEN mr.match_id END) as unreviewed_matches,
    
    -- Confidence distribution
    COUNT(CASE WHEN mr.confidence_level >= 0.9 THEN mr.match_id END) as high_confidence_matches,
    COUNT(CASE WHEN mr.confidence_level >= 0.7 AND mr.confidence_level < 0.9 THEN mr.match_id END) as medium_confidence_matches,
    COUNT(CASE WHEN mr.confidence_level >= 0.5 AND mr.confidence_level < 0.7 THEN mr.match_id END) as low_confidence_matches,
    COUNT(CASE WHEN mr.confidence_level < 0.5 THEN mr.match_id END) as very_low_confidence_matches,
    
    -- Match type distribution
    COUNT(CASE WHEN mr.match_type = 'exact' THEN mr.match_id END) as exact_matches,
    COUNT(CASE WHEN mr.match_type = 'high_confidence' THEN mr.match_id END) as high_confidence_type_matches,
    COUNT(CASE WHEN mr.match_type = 'potential' THEN mr.match_id END) as potential_matches,
    COUNT(CASE WHEN mr.match_type = 'low_confidence' THEN mr.match_id END) as low_confidence_type_matches,
    
    -- Average metrics
    ROUND(AVG(mr.confidence_level), 4) as avg_confidence_level,
    ROUND(AVG(mr.similarity_score), 4) as avg_similarity_score,
    ROUND(AVG(EXTRACT(EPOCH FROM (ic.processed_date - ic.request_date)) * 1000), 2) as avg_processing_time_ms,
    
    -- Date ranges
    MIN(ic.request_date) as earliest_request_date,
    MAX(ic.request_date) as latest_request_date,
    MIN(mr.created_date) as earliest_match_date,
    MAX(mr.created_date) as latest_match_date
    
FROM customer_data.incoming_customers ic
    LEFT JOIN customer_data.matching_results mr ON ic.request_id = mr.incoming_customer_id;

COMMIT; 
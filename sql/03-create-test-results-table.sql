-- Create test results table for storing test execution results
CREATE TABLE customer_data.test_results (
    test_id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    test_type VARCHAR(100) NOT NULL,
    test_configuration JSONB,
    test_data_summary JSONB,
    execution_metrics JSONB,
    results_summary JSONB,
    analysis_results JSONB,
    recommendations JSONB,
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    created_by VARCHAR(100),
    notes TEXT
);

-- Create indexes for performance
CREATE INDEX idx_test_results_test_type ON customer_data.test_results(test_type);
CREATE INDEX idx_test_results_status ON customer_data.test_results(status);
CREATE INDEX idx_test_results_created_date ON customer_data.test_results(created_date);
CREATE INDEX idx_test_results_test_name ON customer_data.test_results(test_name);

-- Create composite index for common queries
CREATE INDEX idx_test_results_type_status_date ON customer_data.test_results(test_type, status, created_date);

-- Add comments for documentation
COMMENT ON TABLE customer_data.test_results IS 'Stores test execution results and analysis for the customer matching system';
COMMENT ON COLUMN customer_data.test_results.test_configuration IS 'JSON object containing test parameters and settings';
COMMENT ON COLUMN customer_data.test_results.test_data_summary IS 'JSON object summarizing the test data used';
COMMENT ON COLUMN customer_data.test_results.execution_metrics IS 'JSON object containing performance metrics and timing data';
COMMENT ON COLUMN customer_data.test_results.results_summary IS 'JSON object containing aggregate test results';
COMMENT ON COLUMN customer_data.test_results.analysis_results IS 'JSON object containing detailed analysis and insights';
COMMENT ON COLUMN customer_data.test_results.recommendations IS 'JSON object containing recommendations from analysis'; 
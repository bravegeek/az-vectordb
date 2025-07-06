"""
Integration test for vector matching pre-testing setup validation.

This test implements the pre-testing setup checklist from the vector matching testing plan.
Each test method corresponds to a checklist item and will be marked as completed when passed.
"""

import pytest
import logging
import os
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.matching.vector_matcher import VectorMatcher
from app.services.matching.result_processor import ResultProcessor

logger = logging.getLogger(__name__)


class TestVectorMatchingPreSetup:
    """
    Pre-testing setup validation for vector matching functionality.
    
    This class implements the checklist from docs/vector_match_testing_plan.md
    Each test method corresponds to a checklist item.
    """
    
    def test_01_verify_database_connection(self, db_session: Session):
        """
        ✅ Verify database connection is working
        
        Checklist item: Verify database connection is working
        """
        try:
            # Test basic database connectivity
            result = db_session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row is not None, "Database connection test query returned no rows"
            assert row[0] == 1
            logger.info("✅ Database connection verified successfully")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def test_02_check_vector_matcher_configuration(self):
        """
        ✅ Check that vector_matcher service is properly configured
        
        Checklist item: Check that vector_matcher service is properly configured
        """
        try:
            # Test vector matcher initialization
            vector_matcher = VectorMatcher()
            assert vector_matcher is not None
            
            # Check if vector matching is enabled in settings
            assert hasattr(settings, 'enable_vector_matching')
            assert hasattr(settings, 'vector_similarity_threshold')
            assert hasattr(settings, 'vector_max_results')
            
            # Verify threshold values are reasonable
            assert 0.0 <= settings.vector_similarity_threshold <= 1.0
            assert settings.vector_max_results > 0
            
            logger.info("✅ Vector matcher configuration verified successfully")
            logger.info(f"   - Vector matching enabled: {settings.enable_vector_matching}")
            logger.info(f"   - Similarity threshold: {settings.vector_similarity_threshold}")
            logger.info(f"   - Max results: {settings.vector_max_results}")
        except Exception as e:
            logger.error(f"❌ Vector matcher configuration check failed: {e}")
            raise
    
    def test_03_confirm_result_processor_availability(self):
        """
        ✅ Confirm result_processor service is available
        
        Checklist item: Confirm result_processor service is available
        """
        try:
            # Test result processor initialization
            result_processor = ResultProcessor()
            assert result_processor is not None
            
            # Verify required methods exist
            assert hasattr(result_processor, 'process_results')
            assert hasattr(result_processor, 'store_matching_results')
            assert hasattr(result_processor, 'update_processing_status')
            assert hasattr(result_processor, 'deduplicate_matches')
            assert hasattr(result_processor, 'sort_matches')
            
            logger.info("✅ Result processor service verified successfully")
        except Exception as e:
            logger.error(f"❌ Result processor availability check failed: {e}")
            raise
    
    def test_04_validate_environment_variables(self):
        """
        ✅ Validate environment variables are set correctly
        
        Checklist item: Validate environment variables are set correctly
        """
        try:
            # Check required database environment variables
            assert settings.postgres_host is not None, "PostgreSQL host is required"
            assert settings.postgres_password is not None, "PostgreSQL password is required"
            assert settings.postgres_user is not None, "PostgreSQL user is required"
            assert settings.postgres_db is not None, "PostgreSQL database name is required"
            
            # Check Azure OpenAI settings (required for embeddings)
            assert settings.azure_openai_endpoint is not None, "Azure OpenAI endpoint is required"
            assert settings.azure_openai_api_key is not None, "Azure OpenAI API key is required"
            assert settings.azure_openai_deployment_name is not None, "Azure OpenAI deployment name is required"
            
            # Verify database URL can be built
            db_url = settings.database_url
            assert db_url is not None and len(db_url) > 0, "Database URL could not be built"
            
            logger.info("✅ Environment variables validated successfully")
            logger.info(f"   - Database host: {settings.postgres_host}")
            logger.info(f"   - Database name: {settings.postgres_db}")
            logger.info(f"   - Azure OpenAI endpoint: {settings.azure_openai_endpoint}")
            logger.info(f"   - Azure OpenAI deployment: {settings.azure_openai_deployment_name}")
        except Exception as e:
            logger.error(f"❌ Environment variables validation failed: {e}")
            raise
    
    def test_05_ensure_pgvector_extension_enabled(self, db_session: Session):
        """
        ✅ Ensure pgvector extension is enabled in PostgreSQL
        
        Checklist item: Ensure pgvector extension is enabled in PostgreSQL
        """
        try:
            # Check if pgvector extension is installed and enabled
            result = db_session.execute(text("""
                SELECT extname, extversion 
                FROM pg_extension 
                WHERE extname = 'vector'
            """))
            
            vector_extension = result.fetchone()
            assert vector_extension is not None, "pgvector extension is not installed"
            
            logger.info(f"✅ pgvector extension verified successfully")
            logger.info(f"   - Extension name: {vector_extension[0]}")
            logger.info(f"   - Extension version: {vector_extension[1]}")
            
            # Test vector operations
            test_result = db_session.execute(text("""
                SELECT '[1,2,3]'::vector AS test_vector
            """))
            
            test_vector = test_result.fetchone()
            assert test_vector is not None, "Vector operations are not working"
            
            logger.info("✅ Vector operations verified successfully")
            
        except Exception as e:
            logger.error(f"❌ pgvector extension check failed: {e}")
            raise
    
    def test_06_verify_required_tables_exist(self, db_session: Session):
        """
        ✅ Verify required database tables exist
        
        Additional check: Ensure all required tables for vector matching exist
        """
        try:
            # Check for required tables
            required_tables = [
                'customer_data.customers',
                'customer_data.incoming_customers', 
                'customer_data.matching_results'
            ]
            
            for table_name in required_tables:
                result = db_session.execute(text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema || '.' || table_name = '{table_name}'
                    )
                """))
                
                row = result.fetchone()
                assert row is not None, f"Table check query returned no rows for {table_name}"
                table_exists = row[0]
                assert table_exists, f"Required table {table_name} does not exist"
                logger.info(f"✅ Table {table_name} exists")
            
            # Check for required columns in customers table
            result = db_session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'customer_data' 
                AND table_name = 'customers' 
                AND column_name = 'full_profile_embedding'
            """))
            
            embedding_column = result.fetchone()
            assert embedding_column is not None, "full_profile_embedding column missing from customers table"
            
            logger.info("✅ Required tables and columns verified successfully")
            
        except Exception as e:
            logger.error(f"❌ Required tables check failed: {e}")
            raise
    
    def test_07_verify_embedding_service_availability(self):
        """
        ✅ Verify embedding service is available
        
        Additional check: Ensure embedding service can be imported and configured
        """
        try:
            # Import embedding service
            from app.services.embedding_service import EmbeddingService
            
            # Test embedding service initialization
            embedding_service = EmbeddingService()
            assert embedding_service is not None
            
            # Verify required methods exist
            assert hasattr(embedding_service, 'generate_text_embedding')
            assert hasattr(embedding_service, 'generate_batch_embeddings')
            assert hasattr(embedding_service, 'generate_customer_embeddings')
            
            logger.info("✅ Embedding service verified successfully")
            
        except Exception as e:
            logger.error(f"❌ Embedding service availability check failed: {e}")
            raise
    
    def test_08_verify_matching_service_integration(self):
        """
        ✅ Verify matching service integration
        
        Additional check: Ensure all matching services can work together
        """
        try:
            # Import matching service
            from app.services.matching.matching_service import MatchingService
            
            # Test matching service initialization
            matching_service = MatchingService()
            assert matching_service is not None
            
            # Verify it has access to vector matcher
            assert hasattr(matching_service, 'vector_matcher')
            assert matching_service.vector_matcher is not None
            
            # Verify it has access to result processor
            assert hasattr(matching_service, 'result_processor')
            assert matching_service.result_processor is not None
            
            logger.info("✅ Matching service integration verified successfully")
            
        except Exception as e:
            logger.error(f"❌ Matching service integration check failed: {e}")
            raise


class TestPreSetupSummary:
    """
    Summary test that runs all pre-setup checks and provides a comprehensive report.
    """
    
    def test_all_pre_setup_checks_passed(self, db_session: Session):
        """
        Run all pre-setup checks and provide summary report.
        
        This test ensures all checklist items from the vector matching testing plan
        are completed successfully before proceeding with actual vector matching tests.
        """
        logger.info("=" * 60)
        logger.info("VECTOR MATCHING PRE-TESTING SETUP VALIDATION")
        logger.info("=" * 60)
        
        # Create test instance to run all checks
        pre_setup = TestVectorMatchingPreSetup()
        
        # Run all pre-setup checks
        checks = [
            ("Database Connection", pre_setup.test_01_verify_database_connection),
            ("Vector Matcher Configuration", pre_setup.test_02_check_vector_matcher_configuration),
            ("Result Processor Availability", pre_setup.test_03_confirm_result_processor_availability),
            ("Environment Variables", pre_setup.test_04_validate_environment_variables),
            ("pgvector Extension", pre_setup.test_05_ensure_pgvector_extension_enabled),
            ("Required Tables", pre_setup.test_06_verify_required_tables_exist),
            ("Embedding Service", pre_setup.test_07_verify_embedding_service_availability),
            ("Matching Service Integration", pre_setup.test_08_verify_matching_service_integration),
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check_name, check_method in checks:
            try:
                if check_name in ["Database Connection", "pgvector Extension", "Required Tables"]:
                    check_method(db_session)
                else:
                    check_method()
                logger.info(f"✅ {check_name}: PASSED")
                passed_checks += 1
            except Exception as e:
                logger.error(f"❌ {check_name}: FAILED - {e}")
        
        logger.info("=" * 60)
        logger.info(f"PRE-SETUP SUMMARY: {passed_checks}/{total_checks} checks passed")
        logger.info("=" * 60)
        
        # Assert all checks passed
        assert passed_checks == total_checks, f"Only {passed_checks}/{total_checks} pre-setup checks passed"
        
        logger.info("🎉 ALL PRE-TESTING SETUP CHECKS COMPLETED SUCCESSFULLY!")
        logger.info("Ready to proceed with vector matching tests.") 
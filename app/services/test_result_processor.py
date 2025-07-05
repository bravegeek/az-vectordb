"""Test result processing and storage service"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.database import TestResult
from app.models.schemas import TestResultCreate, TestResultResponse

logger = logging.getLogger(__name__)


class TestResultProcessor:
    """Handles processing and storage of test results"""
    
    def store_test_result(self, test_data: TestResultCreate, db: Session) -> Optional[TestResultResponse]:
        """Store a test result in the database"""
        try:
            db_test_result = TestResult(
                test_name=test_data.test_name,
                test_type=test_data.test_type,
                test_configuration=test_data.test_configuration,
                test_data_summary=test_data.test_data_summary,
                execution_metrics=test_data.execution_metrics,
                results_summary=test_data.results_summary,
                analysis_results=test_data.analysis_results,
                recommendations=test_data.recommendations,
                status=test_data.status,
                error_message=test_data.error_message,
                created_by=test_data.created_by,
                notes=test_data.notes,
                completed_date=datetime.now() if test_data.status == "completed" else None
            )
            
            db.add(db_test_result)
            db.commit()
            db.refresh(db_test_result)
            
            logger.info(f"Stored test result: {test_data.test_name} (ID: {db_test_result.test_id})")
            return TestResultResponse.model_validate(db_test_result)
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error storing test result: {e}")
            return None
    
    def get_test_result(self, test_id: int, db: Session) -> Optional[TestResultResponse]:
        """Retrieve a test result by ID"""
        try:
            test_result = db.query(TestResult).filter(TestResult.test_id == test_id).first()
            if test_result:
                return TestResultResponse.model_validate(test_result)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving test result {test_id}: {e}")
            return None
    
    def get_test_results(
        self, 
        test_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Session = None
    ) -> List[TestResultResponse]:
        """Retrieve test results with optional filtering"""
        try:
            query = db.query(TestResult)
            
            if test_type:
                query = query.filter(TestResult.test_type == test_type)
            
            if status:
                query = query.filter(TestResult.status == status)
            
            test_results = query.order_by(desc(TestResult.created_date)).offset(offset).limit(limit).all()
            
            return [TestResultResponse.model_validate(result) for result in test_results]
            
        except Exception as e:
            logger.error(f"Error retrieving test results: {e}")
            return []
    
    def update_test_status(self, test_id: int, status: str, error_message: Optional[str] = None, db: Session = None) -> bool:
        """Update test result status"""
        try:
            test_result = db.query(TestResult).filter(TestResult.test_id == test_id).first()
            if test_result:
                test_result.status = status
                if error_message:
                    test_result.error_message = error_message
                if status == "completed":
                    test_result.completed_date = datetime.now()
                
                db.commit()
                logger.info(f"Updated test result {test_id} status to: {status}")
                return True
            else:
                logger.warning(f"Test result {test_id} not found for status update")
                return False
                
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating test result status: {e}")
            return False
    
    def get_test_statistics(self, db: Session) -> Dict[str, Any]:
        """Get aggregate statistics about test results"""
        try:
            total_tests = db.query(TestResult).count()
            completed_tests = db.query(TestResult).filter(TestResult.status == "completed").count()
            failed_tests = db.query(TestResult).filter(TestResult.status == "failed").count()
            
            # Get test types distribution
            test_types = db.query(TestResult.test_type, db.func.count(TestResult.test_id)).group_by(TestResult.test_type).all()
            
            # Get recent activity
            recent_tests = db.query(TestResult).order_by(desc(TestResult.created_date)).limit(5).all()
            
            return {
                "total_tests": total_tests,
                "completed_tests": completed_tests,
                "failed_tests": failed_tests,
                "success_rate": (completed_tests / total_tests * 100) if total_tests > 0 else 0,
                "test_types_distribution": dict(test_types),
                "recent_tests": [
                    {
                        "test_id": test.test_id,
                        "test_name": test.test_name,
                        "test_type": test.test_type,
                        "status": test.status,
                        "created_date": test.created_date
                    }
                    for test in recent_tests
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting test statistics: {e}")
            return {}
    
    def store_semantic_test_result(
        self, 
        test_name: str,
        test_configuration: Dict[str, Any],
        test_data_summary: Dict[str, Any],
        execution_metrics: Dict[str, Any],
        results_summary: Dict[str, Any],
        analysis_results: Dict[str, Any],
        recommendations: List[str],
        db: Session
    ) -> Optional[TestResultResponse]:
        """Convenience method for storing semantic similarity test results"""
        test_data = TestResultCreate(
            test_name=test_name,
            test_type="semantic_similarity",
            test_configuration=test_configuration,
            test_data_summary=test_data_summary,
            execution_metrics=execution_metrics,
            results_summary=results_summary,
            analysis_results=analysis_results,
            recommendations={"recommendations": recommendations},
            status="completed",
            created_by="system"
        )
        
        return self.store_test_result(test_data, db) 
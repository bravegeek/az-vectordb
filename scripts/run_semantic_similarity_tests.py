"""
Run semantic similarity tests for vector matching

This script generates semantic test data and runs comprehensive tests
to validate vector matching functionality across different variation intensities.
"""

import os
import sys
import logging
import json
import time
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add the app directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set up environment file path before importing settings
env_file_path = os.path.join(os.path.dirname(__file__), '..', 'app', '.env')
if os.path.exists(env_file_path):
    os.environ['ENV_FILE'] = env_file_path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.database import Customer, IncomingCustomer
from app.services.matching.vector_matcher import VectorMatcher
from app.services.matching_service import MatchingService
from scripts.generate_semantic_test_data import SemanticTestDataGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SemanticSimilarityTester:
    """Test semantic similarity functionality with generated test data"""
    
    def __init__(self, db_url: str):
        """Initialize the tester with database connection"""
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.vector_matcher = VectorMatcher()
        self.matching_service = MatchingService()
        
        # Test results storage
        self.test_results = {
            "low": {"total": 0, "matches": 0, "high_confidence": 0, "avg_score": 0.0},
            "medium": {"total": 0, "matches": 0, "high_confidence": 0, "avg_score": 0.0},
            "high": {"total": 0, "matches": 0, "high_confidence": 0, "avg_score": 0.0}
        }

    def generate_test_data(self, count_per_intensity: int = 20) -> Dict[str, List[IncomingCustomer]]:
        """Generate semantic test data"""
        logger.info("Generating semantic test data...")
        
        generator = SemanticTestDataGenerator(settings.database_url)
        test_data = generator.create_semantic_test_data(count_per_intensity)
        saved_data = generator.save_to_database(test_data)
        
        logger.info(f"Generated test data: {sum(len(customers) for customers in saved_data.values())} customers")
        return saved_data

    def run_vector_matching_test(self, incoming_customer: IncomingCustomer) -> Dict[str, Any]:
        """Run vector matching test for a single incoming customer"""
        try:
            with self.SessionLocal() as db:
                # Run vector matching
                start_time = time.time()
                matches = self.vector_matcher.find_matches(incoming_customer, db)
                end_time = time.time()
                
                # Get processing status after matching
                db.refresh(incoming_customer)
                processing_status = getattr(incoming_customer, 'processing_status', 'unknown')
                processed_date = getattr(incoming_customer, 'processed_date', None)
                
                # Analyze results
                result = {
                    "request_id": getattr(incoming_customer, 'request_id'),
                    "company_name": incoming_customer.company_name,
                    "base_customer_id": getattr(incoming_customer, 'base_customer_id', None),
                    "variation_intensity": getattr(incoming_customer, 'variation_intensity', 'unknown'),
                    "matches_found": len(matches),
                    "response_time": end_time - start_time,
                    "best_match_score": 0.0,
                    "best_match_type": "none",
                    "high_confidence_matches": 0,
                    "match_details": [],
                    "processing_status": processing_status,
                    "processed_date": processed_date.isoformat() if processed_date else None
                }
                
                if matches:
                    # Sort by similarity score (descending)
                    matches.sort(key=lambda x: x.similarity_score, reverse=True)
                    best_match = matches[0]
                    
                    result["best_match_score"] = best_match.similarity_score
                    result["best_match_type"] = best_match.match_type
                    result["high_confidence_matches"] = len([m for m in matches if m.confidence_level >= 0.8])
                    
                    # Store match details
                    for match in matches[:5]:  # Top 5 matches
                        result["match_details"].append({
                            "customer_id": match.matched_customer_id,
                            "company_name": match.matched_company_name,
                            "similarity_score": match.similarity_score,
                            "confidence_level": match.confidence_level,
                            "match_type": match.match_type
                        })
                
                return result
                
        except Exception as e:
            logger.error(f"Error running vector matching test for request {getattr(incoming_customer, 'request_id')}: {e}")
            return {
                "request_id": getattr(incoming_customer, 'request_id'),
                "company_name": incoming_customer.company_name,
                "error": str(e),
                "matches_found": 0,
                "response_time": 0.0,
                "best_match_score": 0.0,
                "best_match_type": "error",
                "processing_status": "error",
                "processed_date": None
            }

    def run_semantic_similarity_tests(self, test_data: Dict[str, List[IncomingCustomer]]) -> Dict[str, Any]:
        """Run comprehensive semantic similarity tests"""
        logger.info("Running semantic similarity tests...")
        
        all_results = {
            "test_timestamp": datetime.now().isoformat(),
            "intensity_results": {},
            "overall_summary": {},
            "detailed_results": []
        }
        
        total_tests = 0
        total_matches = 0
        total_high_confidence = 0
        total_scores = []
        total_response_time = 0.0
        
        for intensity, customers in test_data.items():
            logger.info(f"Testing {intensity} intensity customers ({len(customers)} customers)")
            
            intensity_results = {
                "total_customers": len(customers),
                "customers_with_matches": 0,
                "high_confidence_matches": 0,
                "average_similarity_score": 0.0,
                "average_response_time": 0.0,
                "score_distribution": {"0.9+": 0, "0.8-0.9": 0, "0.7-0.8": 0, "0.6-0.7": 0, "<0.6": 0},
                "match_type_distribution": {"exact": 0, "high_confidence": 0, "potential": 0, "low_confidence": 0, "no_match": 0}
            }
            
            intensity_scores = []
            intensity_response_times = []
            
            for customer in customers:
                result = self.run_vector_matching_test(customer)
                all_results["detailed_results"].append(result)
                
                # Update intensity statistics
                if result["matches_found"] > 0:
                    intensity_results["customers_with_matches"] += 1
                    intensity_scores.append(result["best_match_score"])
                    intensity_results["high_confidence_matches"] += result["high_confidence_matches"]
                    
                    # Update score distribution
                    score = result["best_match_score"]
                    if score >= 0.9:
                        intensity_results["score_distribution"]["0.9+"] += 1
                    elif score >= 0.8:
                        intensity_results["score_distribution"]["0.8-0.9"] += 1
                    elif score >= 0.7:
                        intensity_results["score_distribution"]["0.7-0.8"] += 1
                    elif score >= 0.6:
                        intensity_results["score_distribution"]["0.6-0.7"] += 1
                    else:
                        intensity_results["score_distribution"]["<0.6"] += 1
                    
                    # Update match type distribution
                    match_type = result["best_match_type"]
                    if match_type in intensity_results["match_type_distribution"]:
                        intensity_results["match_type_distribution"][match_type] += 1
                
                intensity_response_times.append(result["response_time"])
                
                # Update overall statistics
                total_tests += 1
                if result["matches_found"] > 0:
                    total_matches += 1
                    total_scores.append(result["best_match_score"])
                    total_high_confidence += result["high_confidence_matches"]
                total_response_time += result["response_time"]
            
            # Calculate averages for intensity
            if intensity_scores:
                intensity_results["average_similarity_score"] = sum(intensity_scores) / len(intensity_scores)
            if intensity_response_times:
                intensity_results["average_response_time"] = sum(intensity_response_times) / len(intensity_response_times)
            
            all_results["intensity_results"][intensity] = intensity_results
            
            logger.info(f"✅ {intensity} intensity tests completed:")
            logger.info(f"   - Customers with matches: {intensity_results['customers_with_matches']}/{intensity_results['total_customers']}")
            logger.info(f"   - Average similarity score: {intensity_results['average_similarity_score']:.3f}")
            logger.info(f"   - Average response time: {intensity_results['average_response_time']:.3f}s")
        
        # Calculate overall summary
        all_results["overall_summary"] = {
            "total_customers_tested": total_tests,
            "customers_with_matches": total_matches,
            "match_rate": total_matches / total_tests if total_tests > 0 else 0,
            "high_confidence_matches": total_high_confidence,
            "average_similarity_score": sum(total_scores) / len(total_scores) if total_scores else 0,
            "average_response_time": total_response_time / total_tests if total_tests > 0 else 0
        }
        
        return all_results

    def analyze_semantic_patterns(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze semantic patterns in test results"""
        logger.info("Analyzing semantic patterns...")
        
        analysis = {
            "semantic_variation_effectiveness": {},
            "industry_specific_patterns": {},
            "company_name_patterns": {},
            "recommendations": []
        }
        
        # Analyze by intensity level
        for intensity, results in test_results["intensity_results"].items():
            match_rate = results["customers_with_matches"] / results["total_customers"]
            avg_score = results["average_similarity_score"]
            
            analysis["semantic_variation_effectiveness"][intensity] = {
                "match_rate": match_rate,
                "average_score": avg_score,
                "effectiveness": "high" if match_rate > 0.8 and avg_score > 0.8 else 
                               "medium" if match_rate > 0.6 and avg_score > 0.7 else "low"
            }
        
        # Analyze company name patterns
        company_patterns = {}
        for result in test_results["detailed_results"]:
            if "error" not in result and result["matches_found"] > 0:
                company_name = result["company_name"]
                score = result["best_match_score"]
                
                # Analyze common patterns
                patterns = []
                if " Inc." in company_name or " Incorporated" in company_name:
                    patterns.append("suffix_variation")
                if "Tech" in company_name or "Technology" in company_name:
                    patterns.append("industry_term")
                if "Solutions" in company_name or "Services" in company_name:
                    patterns.append("service_term")
                
                for pattern in patterns:
                    if pattern not in company_patterns:
                        company_patterns[pattern] = {"count": 0, "avg_score": 0.0, "scores": []}
                    company_patterns[pattern]["count"] += 1
                    company_patterns[pattern]["scores"].append(score)
        
        # Calculate averages for patterns
        for pattern, data in company_patterns.items():
            if data["scores"]:
                data["avg_score"] = sum(data["scores"]) / len(data["scores"])
        
        analysis["company_name_patterns"] = company_patterns
        
        # Generate recommendations
        recommendations = []
        
        # Check if low intensity is working well
        low_effectiveness = analysis["semantic_variation_effectiveness"].get("low", {})
        if low_effectiveness.get("effectiveness") == "low":
            recommendations.append("Low intensity variations may need refinement - consider adjusting semantic patterns")
        
        # Check if high intensity is too aggressive
        high_effectiveness = analysis["semantic_variation_effectiveness"].get("high", {})
        if high_effectiveness.get("match_rate") < 0.5:
            recommendations.append("High intensity variations may be too aggressive - consider reducing variation complexity")
        
        # Check response time performance
        overall_summary = test_results["overall_summary"]
        if overall_summary["average_response_time"] > 2.0:
            recommendations.append("Response times are slow - consider optimizing vector queries or adding indexes")
        
        analysis["recommendations"] = recommendations
        
        return analysis

    def save_test_results(self, test_results: Dict[str, Any], analysis: Dict[str, Any], output_path: str):
        """Save test results and analysis to JSON file"""
        try:
            output_data = {
                "test_results": test_results,
                "analysis": analysis,
                "test_configuration": {
                    "vector_similarity_threshold": settings.vector_similarity_threshold,
                    "vector_max_results": settings.vector_max_results,
                    "high_confidence_threshold": settings.high_confidence_threshold,
                    "default_similarity_threshold": settings.default_similarity_threshold,
                    "potential_match_threshold": settings.potential_match_threshold
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, default=str)
            
            logger.info(f"Test results saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving test results: {e}")
            return False

    def print_test_summary(self, test_results: Dict[str, Any], analysis: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("SEMANTIC SIMILARITY TEST RESULTS SUMMARY")
        print("="*80)
        
        # Overall summary
        overall = test_results["overall_summary"]
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total customers tested: {overall['total_customers_tested']}")
        print(f"   Customers with matches: {overall['customers_with_matches']}")
        print(f"   Match rate: {overall['match_rate']:.1%}")
        print(f"   High confidence matches: {overall['high_confidence_matches']}")
        print(f"   Average similarity score: {overall['average_similarity_score']:.3f}")
        print(f"   Average response time: {overall['average_response_time']:.3f}s")
        
        # Intensity-specific results
        print(f"\n🎯 INTENSITY-SPECIFIC RESULTS:")
        for intensity, results in test_results["intensity_results"].items():
            effectiveness = analysis["semantic_variation_effectiveness"][intensity]["effectiveness"]
            print(f"\n   {intensity.upper()} INTENSITY:")
            print(f"      Customers tested: {results['total_customers']}")
            print(f"      Match rate: {results['customers_with_matches']}/{results['total_customers']} ({results['customers_with_matches']/results['total_customers']:.1%})")
            print(f"      Average score: {results['average_similarity_score']:.3f}")
            print(f"      Effectiveness: {effectiveness.upper()}")
            
            # Score distribution
            print(f"      Score distribution:")
            for range_name, count in results["score_distribution"].items():
                if count > 0:
                    percentage = count / results['total_customers'] * 100
                    print(f"         {range_name}: {count} ({percentage:.1f}%)")
        
        # Company name patterns
        print(f"\n🏢 COMPANY NAME PATTERNS:")
        for pattern, data in analysis["company_name_patterns"].items():
            if data["count"] > 0:
                print(f"   {pattern}: {data['count']} instances, avg score: {data['avg_score']:.3f}")
        
        # Recommendations
        if analysis["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS:")
            for i, recommendation in enumerate(analysis["recommendations"], 1):
                print(f"   {i}. {recommendation}")
        
        print("\n" + "="*80)


def main():
    """Main function to run semantic similarity tests"""
    parser = argparse.ArgumentParser(description="Run semantic similarity tests for vector matching")
    parser.add_argument("--count-per-intensity", type=int, default=20, 
                       help="Number of customers to generate per intensity level (default: 20)")
    parser.add_argument("--output-json", type=str, default="semantic_test_results.json",
                       help="Output JSON file for test results (default: semantic_test_results.json)")
    parser.add_argument("--skip-generation", action="store_true",
                       help="Skip test data generation (use existing incoming customers)")
    parser.add_argument("--db-url", type=str, 
                       help="Database URL (defaults to settings)")
    
    args = parser.parse_args()
    
    # Use provided DB URL or default from settings
    try:
        db_url = args.db_url or settings.database_url
        logger.info(f"Using database URL: {db_url}")
    except Exception as e:
        logger.error(f"Failed to get database URL from settings: {e}")
        logger.error("Please ensure app/.env file exists and contains database configuration")
        sys.exit(1)
    
    try:
        # Initialize tester
        tester = SemanticSimilarityTester(db_url)
        
        # Generate or retrieve test data
        if args.skip_generation:
            logger.info("Skipping test data generation, using existing incoming customers")
            # TODO: Implement retrieval of existing test data
            test_data = {}
        else:
            test_data = tester.generate_test_data(args.count_per_intensity)
        
        # Run tests
        test_results = tester.run_semantic_similarity_tests(test_data)
        
        # Analyze results
        analysis = tester.analyze_semantic_patterns(test_results)
        
        # Save results
        tester.save_test_results(test_results, analysis, args.output_json)
        
        # Print summary
        tester.print_test_summary(test_results, analysis)
        
        logger.info(f"✅ Semantic similarity tests completed successfully!")
        logger.info(f"📄 Detailed results saved to: {args.output_json}")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 
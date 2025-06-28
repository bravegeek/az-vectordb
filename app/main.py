"""FastAPI application for Customer Matching POC"""
import logging
import time
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, desc
import uvicorn

from config import settings
from database import get_db, check_database_connection, check_pgvector_extension, initialize_database
from models import (
    Customer, IncomingCustomer, MatchingResult,
    CustomerCreate, CustomerResponse, IncomingCustomerCreate, IncomingCustomerResponse,
    CustomerMatchResponse, MatchResult, SimilaritySearchRequest, SimilaritySearchResult,
    HealthCheck
)
from embedding_service import embedding_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Customer account matching using PostgreSQL with pgvector",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize database
    if not initialize_database():
        logger.error("Failed to initialize database")
        raise RuntimeError("Database initialization failed")
    
    # Test embedding service
    if not embedding_service.test_connection():
        logger.error("Failed to connect to Azure OpenAI service")
        raise RuntimeError("Azure OpenAI connection failed")
    
    logger.info("Application started successfully")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with simple web interface"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Customer Matching POC</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: #007acc; font-weight: bold; }
            h1 { color: #333; }
            h2 { color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Customer Matching POC</h1>
            <p>PostgreSQL with pgvector for customer account matching</p>
            
            <h2>Available Endpoints:</h2>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/health</strong><br>
                Check system health and connectivity
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <strong>/customers</strong><br>
                Add a new customer to the database
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/customers</strong><br>
                List all customers
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <strong>/customers/incoming</strong><br>
                Submit an incoming customer for matching
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <strong>/customers/match/{request_id}</strong><br>
                Process matching for an incoming customer
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <strong>/customers/search</strong><br>
                Search for similar customers using text query
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/matches/{request_id}</strong><br>
                Get matching results for an incoming customer
            </div>
            
            <p><a href="/docs">📖 Interactive API Documentation</a></p>
            <p><a href="/redoc">📋 ReDoc Documentation</a></p>
        </div>
    </body>
    </html>
    """
    return html_content


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    db_connected = check_database_connection()
    openai_connected = embedding_service.test_connection()
    
    return HealthCheck(
        status="healthy" if db_connected and openai_connected else "unhealthy",
        timestamp=datetime.now(),
        version=settings.app_version,
        database_connected=db_connected,
        openai_connected=openai_connected
    )


@app.post("/customers", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    """Create a new customer with embeddings"""
    try:
        # Generate embeddings
        company_embedding, profile_embedding = embedding_service.generate_customer_embeddings(
            customer.dict()
        )
        
        # Create customer record
        db_customer = Customer(
            **customer.dict(),
            company_name_embedding=company_embedding,
            full_profile_embedding=profile_embedding
        )
        
        db.add(db_customer)
        db.commit()
        db.refresh(db_customer)
        
        logger.info(f"Created customer: {customer.company_name}")
        return db_customer
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/customers", response_model=List[CustomerResponse])
async def list_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all customers"""
    customers = db.query(Customer).offset(skip).limit(limit).all()
    return customers


@app.post("/customers/incoming", response_model=IncomingCustomerResponse)
async def create_incoming_customer(customer: IncomingCustomerCreate, db: Session = Depends(get_db)):
    """Create an incoming customer request with embeddings"""
    try:
        # Generate embeddings
        company_embedding, profile_embedding = embedding_service.generate_customer_embeddings(
            customer.dict()
        )
        
        # Create incoming customer record
        db_incoming = IncomingCustomer(
            **customer.dict(),
            company_name_embedding=company_embedding,
            full_profile_embedding=profile_embedding
        )
        
        db.add(db_incoming)
        db.commit()
        db.refresh(db_incoming)
        
        logger.info(f"Created incoming customer request: {customer.company_name}")
        return db_incoming
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating incoming customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customers/match/{request_id}", response_model=CustomerMatchResponse)
async def process_customer_matching(request_id: int, db: Session = Depends(get_db)):
    """Process customer matching for an incoming customer"""
    start_time = time.time()
    
    try:
        # Get incoming customer
        incoming_customer = db.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == request_id
        ).first()
        
        if not incoming_customer:
            raise HTTPException(status_code=404, detail="Incoming customer not found")
        
        # Call the PostgreSQL function to process matching
        result = db.execute(
            text("SELECT * FROM customer_data.process_incoming_customer(:request_id)"),
            {"request_id": request_id}
        )
        
        # Get the matching results
        matches_query = db.query(MatchingResult).filter(
            MatchingResult.incoming_customer_id == request_id
        ).order_by(desc(MatchingResult.similarity_score))
        
        matches = matches_query.all()
        
        # Format match results
        match_results = []
        for match in matches:
            matched_customer = db.query(Customer).filter(
                Customer.customer_id == match.matched_customer_id
            ).first()
            
            if matched_customer:
                match_results.append(MatchResult(
                    match_id=match.match_id,
                    matched_customer_id=match.matched_customer_id,
                    matched_company_name=matched_customer.company_name,
                    matched_contact_name=matched_customer.contact_name,
                    matched_email=matched_customer.email,
                    similarity_score=float(match.similarity_score),
                    match_type=match.match_type,
                    confidence_level=float(match.confidence_level),
                    match_criteria=match.match_criteria or {},
                    created_date=match.created_date
                ))
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        db.commit()
        
        logger.info(f"Processed matching for request {request_id}: {len(match_results)} matches found")
        
        return CustomerMatchResponse(
            incoming_customer=incoming_customer,
            matches=match_results,
            total_matches=len(match_results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing customer matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customers/match-hybrid/{request_id}", response_model=CustomerMatchResponse)
async def process_customer_matching_hybrid(request_id: int, db: Session = Depends(get_db)):
    """Process customer matching using hybrid approach (exact + vector + fuzzy)"""
    start_time = time.time()
    
    try:
        # Get incoming customer
        incoming_customer = db.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == request_id
        ).first()
        
        if not incoming_customer:
            raise HTTPException(status_code=404, detail="Incoming customer not found")
        
        # Call the enhanced PostgreSQL function for hybrid matching
        result = db.execute(
            text("SELECT * FROM customer_data.process_incoming_customer_hybrid(:request_id)"),
            {"request_id": request_id}
        )
        
        # Get the matching results
        matches_query = db.query(MatchingResult).filter(
            MatchingResult.incoming_customer_id == request_id
        ).order_by(desc(MatchingResult.similarity_score))
        
        matches = matches_query.all()
        
        # Format match results
        match_results = []
        for match in matches:
            matched_customer = db.query(Customer).filter(
                Customer.customer_id == match.matched_customer_id
            ).first()
            
            if matched_customer:
                match_results.append(MatchResult(
                    match_id=match.match_id,
                    matched_customer_id=match.matched_customer_id,
                    matched_company_name=matched_customer.company_name,
                    matched_contact_name=matched_customer.contact_name,
                    matched_email=matched_customer.email,
                    similarity_score=float(match.similarity_score),
                    match_type=match.match_type,
                    confidence_level=float(match.confidence_level),
                    match_criteria=match.match_criteria or {},
                    created_date=match.created_date
                ))
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        db.commit()
        
        logger.info(f"Processed hybrid matching for request {request_id}: {len(match_results)} matches found")
        
        return CustomerMatchResponse(
            incoming_customer=incoming_customer,
            matches=match_results,
            total_matches=len(match_results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing hybrid customer matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customers/match-exact/{request_id}", response_model=CustomerMatchResponse)
async def process_customer_matching_exact(request_id: int, db: Session = Depends(get_db)):
    """Process customer matching using only exact field matching"""
    start_time = time.time()
    
    try:
        # Get incoming customer
        incoming_customer = db.query(IncomingCustomer).filter(
            IncomingCustomer.request_id == request_id
        ).first()
        
        if not incoming_customer:
            raise HTTPException(status_code=404, detail="Incoming customer not found")
        
        # Call the exact matching function
        result = db.execute(
            text("SELECT * FROM customer_data.find_exact_matches(:request_id)"),
            {"request_id": request_id}
        )
        
        # Process exact matches
        match_results = []
        for row in result:
            matched_customer = db.query(Customer).filter(
                Customer.customer_id == row.customer_id
            ).first()
            
            if matched_customer:
                # Create match result record
                match_result = MatchingResult(
                    incoming_customer_id=request_id,
                    matched_customer_id=row.customer_id,
                    similarity_score=row.match_score,
                    match_type='exact',
                    confidence_level=row.match_score,
                    match_criteria=row.match_criteria
                )
                db.add(match_result)
                
                match_results.append(MatchResult(
                    match_id=0,  # Will be set after commit
                    matched_customer_id=row.customer_id,
                    matched_company_name=matched_customer.company_name,
                    matched_contact_name=matched_customer.contact_name,
                    matched_email=matched_customer.email,
                    similarity_score=float(row.match_score),
                    match_type='exact',
                    confidence_level=float(row.match_score),
                    match_criteria=row.match_criteria or {},
                    created_date=datetime.now()
                ))
        
        # Update processing status
        incoming_customer.processing_status = 'processed'
        incoming_customer.processed_date = datetime.now()
        
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        db.commit()
        
        logger.info(f"Processed exact matching for request {request_id}: {len(match_results)} matches found")
        
        return CustomerMatchResponse(
            incoming_customer=incoming_customer,
            matches=match_results,
            total_matches=len(match_results),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing exact customer matching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/customers/search", response_model=List[SimilaritySearchResult])
async def search_similar_customers(
    search_request: SimilaritySearchRequest,
    db: Session = Depends(get_db)
):
    """Search for similar customers using text query"""
    try:
        # Generate embedding for search query
        query_embedding = embedding_service.generate_embedding(search_request.query_text)
        
        if not query_embedding:
            raise HTTPException(status_code=400, detail="Failed to generate embedding for query")
        
        # Call the PostgreSQL function for similarity search
        result = db.execute(
            text("""
                SELECT * FROM customer_data.find_similar_customers(
                    :query_embedding::vector,
                    :threshold,
                    :max_results
                )
            """),
            {
                "query_embedding": query_embedding,
                "threshold": search_request.similarity_threshold,
                "max_results": search_request.max_results
            }
        )
        
        # Format results
        search_results = []
        for row in result:
            search_results.append(SimilaritySearchResult(
                customer_id=row.customer_id,
                company_name=row.company_name,
                contact_name=row.contact_name,
                email=row.email,
                city=row.city,
                country=row.country,
                similarity_score=float(row.similarity_score)
            ))
        
        logger.info(f"Similarity search for '{search_request.query_text}': {len(search_results)} results")
        return search_results
        
    except Exception as e:
        logger.error(f"Error in similarity search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/matches/{request_id}", response_model=List[MatchResult])
async def get_matching_results(request_id: int, db: Session = Depends(get_db)):
    """Get matching results for an incoming customer"""
    matches = db.query(MatchingResult).filter(
        MatchingResult.incoming_customer_id == request_id
    ).order_by(desc(MatchingResult.similarity_score)).all()
    
    if not matches:
        raise HTTPException(status_code=404, detail="No matching results found")
    
    # Format results
    match_results = []
    for match in matches:
        matched_customer = db.query(Customer).filter(
            Customer.customer_id == match.matched_customer_id
        ).first()
        
        if matched_customer:
            match_results.append(MatchResult(
                match_id=match.match_id,
                matched_customer_id=match.matched_customer_id,
                matched_company_name=matched_customer.company_name,
                matched_contact_name=matched_customer.contact_name,
                matched_email=matched_customer.email,
                similarity_score=float(match.similarity_score),
                match_type=match.match_type,
                confidence_level=float(match.confidence_level),
                match_criteria=match.match_criteria or {},
                created_date=match.created_date
            ))
    
    return match_results


@app.get("/customers/incoming", response_model=List[IncomingCustomerResponse])
async def list_incoming_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all incoming customer requests"""
    incoming_customers = db.query(IncomingCustomer).offset(skip).limit(limit).all()
    return incoming_customers


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

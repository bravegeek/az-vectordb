"""FastAPI application for Customer Matching POC"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.database import initialize_database, check_database_connection
from app.services.embedding_service import embedding_service
from app.api.v1.api import api_router

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
                <span class="method">POST</span> <strong>/matching/{request_id}</strong><br>
                Process matching for an incoming customer
            </div>
            
            <div class="endpoint">
                <span class="method">POST</span> <strong>/customers/search</strong><br>
                Search for similar customers using text query
            </div>
            
            <div class="endpoint">
                <span class="method">GET</span> <strong>/matching/results/{request_id}</strong><br>
                Get matching results for an incoming customer
            </div>
            
            <p><a href="/docs">📖 Interactive API Documentation</a></p>
            <p><a href="/redoc">📋 ReDoc Documentation</a></p>
        </div>
    </body>
    </html>
    """
    return html_content


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_new:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    ) 
"""
Main application entry point for user management service
"""
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.database import db_manager
from app.cache import cache_manager
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting user management service...")
    
    try:
        # Initialize database
        await db_manager.initialize()
        logger.info("Database initialized successfully")
        
        # Initialize cache
        await cache_manager.initialize()
        logger.info("Cache initialized successfully")
        
        # Create default admin user if no users exist
        await create_default_admin()
        
        logger.info("User management service started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down user management service...")
    
    try:
        # Close cache connection
        await cache_manager.close()
        logger.info("Cache connection closed")
        
        # Close database connection
        await db_manager.close()
        logger.info("Database connection closed")
        
        logger.info("User management service shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="User Management Service",
    description="Comprehensive user management system with multi-tenant support",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = asyncio.get_event_loop().time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = asyncio.get_event_loop().time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Include API routes
app.include_router(router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": asyncio.get_event_loop().time()
        }
    )

async def create_default_admin():
    """Create default admin user if no users exist"""
    try:
        from app.database import db_manager
        from app.models import UserRole, UserStatus
        from app.auth import auth_manager
        import uuid
        
        # Check if any users exist
        result = await db_manager.execute_one("SELECT COUNT(*) as count FROM users")
        user_count = result["count"] if result else 0
        
        if user_count == 0:
            logger.info("No users found, creating default admin user...")
            
            # Create default admin user
            admin_id = uuid.uuid4()
            admin_password = "admin123"  # Change this in production!
            password_hash = auth_manager.hash_password(admin_password)
            
            query = """
                INSERT INTO users (
                    id, email, username, password_hash, first_name, last_name,
                    role, status, is_verified
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
            await db_manager.execute_command(
                query,
                admin_id,
                "admin@example.com",
                "admin",
                password_hash,
                "Admin",
                "User",
                UserRole.ADMIN.value,
                UserStatus.ACTIVE.value,
                True
            )
            
            logger.warning(f"Default admin user created: admin@example.com / {admin_password}")
            logger.warning("Please change the default password immediately!")
            
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")

def main():
    """Main function to run the application"""
    logger.info(f"Starting {settings.service_name} on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
        access_log=True
    )

if __name__ == "__main__":
    main()
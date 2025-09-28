"""
User Management Service Main Application
"""
import uvicorn
import logging
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info(f"Starting User Management Service on {settings.service_host}:{settings.service_port}")
    
    uvicorn.run(
        "app.api:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
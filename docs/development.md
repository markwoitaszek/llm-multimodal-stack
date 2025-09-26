# Development Guide

This guide covers development setup, testing, and contribution guidelines for the Multimodal LLM Stack.

## Development Setup

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- NVIDIA Docker runtime (for GPU support)
- Git

### Quick Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd llm-multimodal-stack

# Setup development environment
./scripts/setup.sh

# Start in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Development Docker Compose

Create `docker-compose.dev.yml` for development:

```yaml
version: '3.8'

services:
  multimodal-worker:
    volumes:
      - ./services/multimodal-worker:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

  retrieval-proxy:
    volumes:
      - ./services/retrieval-proxy:/app
    environment:
      - DEBUG=true
      - LOG_LEVEL=DEBUG
    command: ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

  # Development database with exposed ports
  postgres:
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=dev_password

  # Development tools
  pgadmin:
    image: dpage/pgadmin4:7.8
    ports:
      - "5050:80"
    environment:
      - PGADMIN_DEFAULT_EMAIL=dev@multimodal.local
      - PGADMIN_DEFAULT_PASSWORD=dev_password
```

## Local Development

### Python Environment Setup

```bash
# Create virtual environment for each service
cd services/multimodal-worker
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

cd ../retrieval-proxy
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Services Locally

```bash
# Terminal 1: Start infrastructure
docker-compose up -d qdrant postgres minio

# Terminal 2: Start multimodal worker
cd services/multimodal-worker
source venv/bin/activate
python main.py

# Terminal 3: Start retrieval proxy
cd services/retrieval-proxy
source venv/bin/activate
python main.py

# Terminal 4: Start LiteLLM (if needed locally)
pip install litellm
litellm --config ../../configs/litellm_config.yaml
```

## Code Structure

### Project Layout

```
llm-multimodal-stack/
├── services/
│   ├── multimodal-worker/       # Image/video/text processing
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Configuration settings
│   │   │   ├── models.py        # ML model management
│   │   │   ├── database.py      # Database operations
│   │   │   ├── storage.py       # MinIO/S3 operations
│   │   │   ├── processors.py    # Media processing logic
│   │   │   └── api.py          # FastAPI routes
│   │   ├── main.py             # Application entry point
│   │   ├── requirements.txt    # Python dependencies
│   │   └── Dockerfile
│   └── retrieval-proxy/        # Search and context bundling
│       ├── app/
│       │   ├── config.py       # Configuration settings
│       │   ├── database.py     # Database operations
│       │   ├── vector_store.py # Qdrant operations
│       │   ├── retrieval.py    # Search engine logic
│       │   └── api.py         # FastAPI routes
│       ├── main.py
│       ├── requirements.txt
│       └── Dockerfile
├── configs/                    # Configuration files
├── sql/                       # Database schemas and migrations
├── scripts/                   # Utility scripts
├── docs/                      # Documentation
└── docker-compose.yml         # Main Docker Compose file
```

### Key Components

#### Multimodal Worker (`services/multimodal-worker/`)

**Purpose**: Processes images, videos, and text to extract embeddings and metadata.

**Key Classes**:
- `ModelManager`: Loads and manages ML models (CLIP, BLIP, Whisper)
- `ImageProcessor`: Handles image embedding and captioning
- `VideoProcessor`: Handles video transcription and keyframe extraction
- `TextProcessor`: Handles text chunking and embedding
- `DatabaseManager`: PostgreSQL operations
- `StorageManager`: MinIO/S3 operations

#### Retrieval Proxy (`services/retrieval-proxy/`)

**Purpose**: Provides unified search across all modalities and creates context bundles.

**Key Classes**:
- `RetrievalEngine`: Main search and context bundling logic
- `VectorStoreManager`: Qdrant vector database operations
- `DatabaseManager`: PostgreSQL metadata operations

## Testing

### Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock httpx

# Run tests for multimodal worker
cd services/multimodal-worker
python -m pytest tests/ -v

# Run tests for retrieval proxy
cd services/retrieval-proxy  
python -m pytest tests/ -v
```

### Integration Tests

```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
./scripts/test-multimodal.sh

# Run performance tests
./scripts/benchmark.sh
```

### Test Structure

```
services/multimodal-worker/tests/
├── __init__.py
├── conftest.py              # Pytest configuration
├── test_models.py           # Model loading tests
├── test_processors.py       # Processing logic tests
├── test_database.py         # Database operation tests
├── test_storage.py          # Storage operation tests
└── test_api.py             # API endpoint tests
```

### Example Test

```python
# services/multimodal-worker/tests/test_processors.py
import pytest
from unittest.mock import Mock, AsyncMock
from PIL import Image
import numpy as np

from app.processors import ImageProcessor
from app.models import ModelManager
from app.database import DatabaseManager
from app.storage import StorageManager

@pytest.fixture
async def image_processor():
    model_manager = Mock(spec=ModelManager)
    db_manager = Mock(spec=DatabaseManager)
    storage_manager = Mock(spec=StorageManager)
    
    # Mock model responses
    model_manager.get_model.return_value = Mock()
    model_manager.get_processor.return_value = Mock()
    
    return ImageProcessor(model_manager, db_manager, storage_manager)

@pytest.mark.asyncio
async def test_generate_image_embedding(image_processor):
    """Test image embedding generation"""
    # Create test image
    test_image = Image.new('RGB', (100, 100), color='red')
    
    # Mock CLIP model response
    mock_embedding = np.random.rand(512)
    image_processor.model_manager.get_model.return_value.get_image_features.return_value.cpu.return_value.numpy.return_value.flatten.return_value = mock_embedding
    
    # Test embedding generation
    result = await image_processor.generate_image_embedding(test_image)
    
    assert isinstance(result, np.ndarray)
    assert result.shape == (512,)
```

## Code Quality

### Linting and Formatting

```bash
# Install development tools
pip install black isort flake8 mypy

# Format code
black services/
isort services/

# Check linting
flake8 services/
mypy services/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

## Debugging

### Logging Configuration

```python
# app/config.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/app/logs/service.log')
        ]
    )
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Start services with debug logging
docker-compose up -d
```

### Common Debug Commands

```bash
# Check service logs
docker-compose logs -f multimodal-worker

# Execute commands in running container
docker-compose exec multimodal-worker bash

# Check GPU usage
nvidia-smi

# Monitor resource usage
docker stats

# Check database connections
docker-compose exec postgres psql -U postgres -d multimodal -c "SELECT COUNT(*) FROM documents;"

# Check vector store
curl http://localhost:6333/collections
```

## Performance Optimization

### Profiling

```python
# Add to main.py for profiling
import cProfile
import pstats
from pstats import SortKey

def profile_function(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats(SortKey.TIME)
        stats.print_stats(10)  # Top 10 functions
        
        return result
    return wrapper
```

### Memory Management

```python
# Monitor GPU memory
import torch

def log_gpu_memory():
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3
        cached = torch.cuda.memory_reserved() / 1024**3
        logger.info(f"GPU Memory - Allocated: {allocated:.2f}GB, Cached: {cached:.2f}GB")
```

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_documents_file_type_created 
ON documents(file_type, created_at DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM documents WHERE file_type = 'image';

-- Monitor slow queries
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC 
LIMIT 10;
```

## Contributing

### Development Workflow

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-fork/llm-multimodal-stack.git
   cd llm-multimodal-stack
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-processor
   ```

3. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Test Changes**
   ```bash
   ./scripts/test-multimodal.sh
   ./scripts/health-check.sh
   ```

5. **Submit Pull Request**
   - Clear description of changes
   - Link to related issues
   - Include test results

### Code Style Guidelines

- **Python**: Follow PEP 8, use Black formatter
- **Docstrings**: Use Google style docstrings
- **Type Hints**: Use type hints for all functions
- **Error Handling**: Use specific exception types
- **Logging**: Use structured logging with appropriate levels

### Adding New Processors

```python
# services/multimodal-worker/app/processors.py

class NewProcessor(BaseProcessor):
    """Processes new media type"""
    
    async def process_media(self, media_path: str, document_id: str) -> Dict[str, Any]:
        """
        Process new media type
        
        Args:
            media_path: Path to media file
            document_id: Document UUID
            
        Returns:
            Processing results dictionary
            
        Raises:
            ProcessingError: If processing fails
        """
        try:
            # Processing logic here
            result = await self._process_logic(media_path)
            
            # Store results
            await self._store_results(result, document_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process media: {e}")
            raise ProcessingError(f"Processing failed: {e}")
```

### Documentation Standards

- Update API documentation for new endpoints
- Add configuration examples
- Include performance benchmarks
- Provide troubleshooting guides

## Deployment

### Production Checklist

- [ ] Update all default passwords
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategies
- [ ] Review security settings
- [ ] Performance test with expected load
- [ ] Set up log aggregation

### Environment-Specific Configs

```bash
# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d

# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```


# Test Contribution Guidelines

This document provides comprehensive guidelines for contributing to the LLM Multimodal Stack test suite.

## 🎯 Overview

The test suite has been transformed from basic stubs into a **production-ready, comprehensive testing framework** that validates real business logic. All tests now verify actual functionality rather than just mocking everything.

## 🚀 Key Principles

### 1. **Test Real Business Logic**
- **DO**: Test actual model loading, processing, database operations, and API behavior
- **DON'T**: Mock internal business logic - test the real implementation
- **WHY**: Catches real bugs and validates actual functionality

### 2. **Strategic Mocking**
- **DO**: Mock external dependencies (databases, storage, APIs, network calls)
- **DON'T**: Mock internal processing logic, algorithms, or data transformations
- **WHY**: Ensures tests validate real functionality while maintaining isolation

### 3. **Comprehensive Coverage**
- **DO**: Test success cases, failure cases, edge cases, and error conditions
- **DON'T**: Only test happy paths
- **WHY**: Ensures robust error handling and edge case coverage

### 4. **Performance Validation**
- **DO**: Measure actual performance metrics and validate against thresholds
- **DON'T**: Ignore performance implications of code changes
- **WHY**: Maintains system performance and scalability

## 📁 Test Structure

### Unit Tests (`tests/services/{service}/`)
Test individual components with real business logic:

```
tests/services/multimodal-worker/
├── test_models.py          # REAL: Model loading and inference
├── test_processors.py      # REAL: Content processing logic
├── test_database.py        # REAL: Database operations
├── test_storage.py         # REAL: File storage operations
├── test_api.py            # REAL: API endpoint testing
└── test_config.py         # Configuration testing
```

### Integration Tests (`tests/integration/`)
Test real service interactions and data flow:

```
tests/integration/
├── test_service_communication.py        # Original integration tests
├── test_workflow_execution.py           # Original workflow tests
├── test_enhanced_service_communication.py  # NEW: Real service communication
└── test_enhanced_workflow_execution.py     # NEW: Real workflow execution
```

### Performance Tests (`tests/performance/`)
Test actual performance metrics and scalability:

```
tests/performance/
├── test_api_response_times.py           # Original API performance tests
├── test_model_inference.py              # Original model performance tests
├── test_comprehensive_performance.py    # NEW: End-to-end performance
└── test_performance_monitoring.py       # NEW: Performance monitoring
```

## 🧪 Writing Real Unit Tests

### Example: Testing Real Model Loading

```python
@pytest.mark.asyncio
@patch('app.models.CLIPModel')
async def test_load_models_success(self, mock_clip_model):
    """Test successful model loading with real model initialization"""
    # Setup mock for external model loading
    mock_model = Mock()
    mock_clip_model.return_value = mock_model
    
    # Test REAL model manager initialization
    model_manager = ModelManager()
    await model_manager.initialize()
    
    # Verify REAL model loading logic
    assert model_manager.clip_model is not None
    assert model_manager.device == "cuda" or model_manager.device == "cpu"
    
    # Verify REAL model retrieval
    clip_model = model_manager.get_clip_model()
    assert clip_model == mock_model
```

### Example: Testing Real Database Operations

```python
@pytest.mark.asyncio
async def test_create_document_success(self, mock_pool):
    """Test real document creation with actual database interaction"""
    # Setup real database connection
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    
    # Test REAL database manager
    db_manager = DatabaseManager()
    db_manager.pool = mock_pool
    
    # Test REAL document creation logic
    result = await db_manager.create_document(
        content_hash="test_hash",
        content_type="text",
        metadata={"source": "test"}
    )
    
    # Verify REAL database interaction
    assert result is True
    mock_conn.execute.assert_called_once()
    
    # Verify REAL SQL query structure
    call_args = mock_conn.execute.call_args
    assert "INSERT INTO documents" in call_args[0][0]
    assert call_args[0][1] == "test_hash"
```

### Example: Testing Real API Endpoints

```python
@pytest.mark.asyncio
@patch('main.model_manager')
async def test_process_image_success(self, mock_model_manager, client):
    """Test real image processing API with actual endpoint behavior"""
    # Setup mock for external dependencies
    mock_model_manager.process_image.return_value = {
        "success": True,
        "content_id": "test_id",
        "embeddings": [0.1, 0.2, 0.3] * 128
    }
    
    # Test REAL API endpoint
    response = client.post(
        "/api/v1/process/image",
        files={"file": ("test.jpg", b"fake_image_data", "image/jpeg")},
        data={"document_name": "test.jpg"}
    )
    
    # Verify REAL API response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "content_id" in data
    assert "embeddings" in data
    
    # Verify REAL model manager was called
    mock_model_manager.process_image.assert_called_once()
```

## 🔗 Writing Real Integration Tests

### Example: Testing Real Service Communication

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_multimodal_processing_workflow(self, test_services, real_test_data):
    """Test real multimodal processing with actual data flow"""
    multimodal_worker = test_services["multimodal_worker"]
    retrieval_proxy = test_services["retrieval_proxy"]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Process REAL image data
        with open(image_path, 'rb') as f:
            files = {'file': (real_test_data["image_filename"], f, 'image/jpeg')}
            data = {'document_name': 'integration_test_image'}
            
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/image",
                files=files,
                data=data
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
            content_id = result["content_id"]
        
        # Step 2: Search for REAL processed content
        search_response = await client.post(
            f"{retrieval_proxy['url']}/api/v1/search",
            json={
                "query": "test image",
                "modalities": ["image"],
                "limit": 10
            }
        )
        
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["success"] is True
        
        # Verify REAL data consistency
        found_content_ids = {result["document_id"] for result in search_result["results"]}
        assert content_id in found_content_ids
```

## ⚡ Writing Real Performance Tests

### Example: Testing Real Performance Benchmarks

```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_real_performance_benchmarks(self, test_services, performance_test_data):
    """Test real performance benchmarks with actual data processing"""
    multimodal_worker = test_services["multimodal_worker"]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Test REAL processing performance
        processing_times = []
        
        for i in range(20):
            start_time = time.time()
            
            response = await client.post(
                f"{multimodal_worker['url']}/api/v1/process/text",
                json={
                    "text": performance_test_data["documents"]["large"],
                    "document_name": f"perf_test_{i}.txt"
                }
            )
            
            end_time = time.time()
            processing_times.append(end_time - start_time)
            
            assert response.status_code == 200
            result = response.json()
            assert result["success"] is True
        
        # Validate REAL performance metrics
        avg_processing_time = statistics.mean(processing_times)
        assert avg_processing_time < performance_thresholds["text_processing_time"], \
            f"Average processing time {avg_processing_time:.2f}s exceeds threshold"
```

## 🎭 Mocking Strategy

### When to Use Mocks

```python
# ✅ DO: Mock external dependencies
@patch('httpx.AsyncClient')  # External HTTP calls
@patch('asyncpg.create_pool')  # External database connections
@patch('minio.Minio')  # External storage services
@patch('qdrant_client.QdrantClient')  # External vector database

# ✅ DO: Mock expensive operations for unit tests
@patch('torch.cuda.is_available')  # GPU availability
@patch('time.sleep')  # Time delays in tests
```

### When NOT to Use Mocks

```python
# ❌ DON'T: Mock internal business logic
# BAD: Mocking the actual processing logic
@patch('app.processors.ImageProcessor.process_image')

# ✅ DO: Test the real processing logic
def test_process_image_success(self):
    processor = ImageProcessor()
    result = processor.process_image(image_data)  # Test real logic
    assert result["success"] is True

# ❌ DON'T: Mock data transformations
# BAD: Mocking the actual data processing
@patch('app.processors.TextProcessor.chunk_text')

# ✅ DO: Test real data transformations
def test_chunk_text_success(self):
    processor = TextProcessor()
    chunks = processor.chunk_text("This is a test document")
    assert len(chunks) > 0
    assert all(len(chunk) <= 1000 for chunk in chunks)
```

## 📊 Coverage Requirements

### Coverage Targets
- **Minimum Coverage**: 80% for all services
- **Target Coverage**: 90% for critical components
- **Critical Components**: 95% (models, processors, APIs)

### Coverage Analysis
```bash
# Run coverage analysis
python3 scripts/analyze_test_coverage.py

# Run tests with coverage
pytest tests/ --cov=services --cov-report=html --cov-report=term-missing
```

### Coverage Best Practices
1. **Test all public methods** - Ensure all exposed functionality is tested
2. **Test error conditions** - Include failure cases and edge conditions
3. **Test data validation** - Verify input validation and sanitization
4. **Test configuration** - Ensure configuration handling is tested
5. **Test integration points** - Verify service interactions

## ⚡ Performance Testing Guidelines

### Performance Thresholds
```python
PERFORMANCE_THRESHOLDS = {
    "api_response_time_ms": 1000,
    "text_processing_time": 2.0,  # seconds
    "image_processing_time": 5.0,  # seconds
    "search_response_time": 1.0,  # seconds
    "agent_execution_time": 10.0,  # seconds
    "model_inference_time_ms": 5000,
    "database_query_time_ms": 100,
    "vector_search_time_ms": 200
}
```

### Performance Test Structure
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_performance_benchmark(self):
    """Test actual performance against real thresholds"""
    # Measure real performance
    start_time = time.time()
    result = await real_operation()
    actual_time = time.time() - start_time
    
    # Validate against real thresholds
    assert actual_time < PERFORMANCE_THRESHOLDS["operation_time"]
    assert result["success"] is True
```

## 🔧 Test Configuration

### Test Markers
```python
@pytest.mark.unit          # Unit tests with real business logic
@pytest.mark.integration   # Integration tests with real service communication
@pytest.mark.performance   # Performance tests with real benchmarks
@pytest.mark.slow         # Slow-running tests
@pytest.mark.gpu          # GPU-required tests
@pytest.mark.api          # API tests with real endpoints
@pytest.mark.database     # Database tests with real queries
@pytest.mark.storage      # Storage tests with real files
@pytest.mark.models       # Model tests with real inference
@pytest.mark.agents       # Agent tests with real execution
@pytest.mark.retrieval    # Retrieval tests with real search
@pytest.mark.multimodal   # Multimodal tests with real content
```

### Test Fixtures
```python
@pytest.fixture
def real_test_data(self):
    """Create real test data for comprehensive testing"""
    return {
        "documents": ["Real document content..."],
        "images": [real_image_data],
        "queries": ["Real search queries..."]
    }

@pytest.fixture
def performance_thresholds(self):
    """Real performance thresholds for validation"""
    return {
        "api_response_time_ms": 1000,
        "processing_time": 2.0
    }
```

## 🚀 Running Tests

### Unit Tests
```bash
# Run all unit tests
pytest tests/services/ -v

# Run specific service tests
pytest tests/services/multimodal-worker/ -v
pytest tests/services/retrieval-proxy/ -v
pytest tests/services/ai-agents/ -v

# Run with coverage
pytest tests/services/ --cov=services --cov-report=html
```

### Integration Tests
```bash
# Run integration tests
pytest tests/integration/ -v -m integration

# Run enhanced integration tests
pytest tests/integration/test_enhanced_service_communication.py -v
```

### Performance Tests
```bash
# Run performance tests
pytest tests/performance/ -v -m performance

# Run comprehensive performance tests
pytest tests/performance/test_comprehensive_performance.py -v
```

### All Tests
```bash
# Run all tests
pytest tests/ -v

# Run with markers
pytest tests/ -v -m "unit or integration or performance"

# Run excluding slow tests
pytest tests/ -v -m "not slow"
```

## 🐛 Debugging Tests

### Verbose Output
```bash
pytest tests/ -v -s --tb=long
```

### Debug Specific Test
```bash
pytest tests/services/multimodal-worker/test_models.py::TestModelManager::test_load_models_success -v -s
```

### Run with PDB
```bash
pytest tests/ --pdb
```

## 📝 Code Review Checklist

### Test Quality Checklist
- [ ] **Real business logic tested** - Not just mocked
- [ ] **Success and failure cases covered** - Comprehensive scenarios
- [ ] **Edge cases included** - Boundary conditions and error states
- [ ] **Performance validated** - Meets established thresholds
- [ ] **Integration points tested** - Real service communication
- [ ] **Error handling verified** - Proper exception handling
- [ ] **Data validation tested** - Input/output validation
- [ ] **Configuration tested** - Settings and environment handling

### Code Quality Checklist
- [ ] **Clear test names** - Descriptive and specific
- [ ] **Comprehensive docstrings** - Explain test purpose and scenarios
- [ ] **Proper fixtures** - Reusable test data and setup
- [ ] **Appropriate markers** - Correct test categorization
- [ ] **Clean assertions** - Clear and specific assertions
- [ ] **No test pollution** - Tests don't affect each other
- [ ] **Maintainable code** - Easy to understand and modify

## 🎯 Best Practices

### 1. **Test Real Functionality**
```python
# ✅ GOOD: Test real business logic
def test_process_image_success(self):
    processor = ImageProcessor()
    result = processor.process_image(real_image_data)
    assert result["success"] is True
    assert "embeddings" in result

# ❌ BAD: Mock internal logic
@patch('app.processors.ImageProcessor.process_image')
def test_process_image_success(self, mock_process):
    mock_process.return_value = {"success": True}
    # This doesn't test real functionality
```

### 2. **Comprehensive Error Testing**
```python
# ✅ GOOD: Test error conditions
def test_process_image_invalid_data(self):
    processor = ImageProcessor()
    with pytest.raises(ValueError, match="Invalid image data"):
        processor.process_image(None)

# ✅ GOOD: Test edge cases
def test_process_image_empty_data(self):
    processor = ImageProcessor()
    result = processor.process_image(b"")
    assert result["success"] is False
    assert "error" in result
```

### 3. **Performance Validation**
```python
# ✅ GOOD: Validate real performance
def test_api_response_time(self):
    start_time = time.time()
    response = client.post("/api/v1/process/text", json=data)
    response_time = time.time() - start_time
    
    assert response.status_code == 200
    assert response_time < PERFORMANCE_THRESHOLDS["api_response_time"]
```

### 4. **Integration Testing**
```python
# ✅ GOOD: Test real service communication
async def test_service_integration(self):
    # Process content in one service
    response1 = await client.post(f"{service1_url}/process", json=data)
    content_id = response1.json()["content_id"]
    
    # Search for it in another service
    response2 = await client.post(f"{service2_url}/search", json={"query": "test"})
    results = response2.json()["results"]
    
    # Verify real data consistency
    assert any(r["content_id"] == content_id for r in results)
```

## 🚨 Common Pitfalls

### 1. **Over-Mocking**
```python
# ❌ BAD: Mocking everything
@patch('app.models.ModelManager')
@patch('app.processors.ImageProcessor')
@patch('app.database.DatabaseManager')
def test_process_image(self, mock_db, mock_processor, mock_models):
    # This tests nothing real

# ✅ GOOD: Mock only external dependencies
@patch('httpx.AsyncClient')
def test_process_image(self, mock_client):
    # Test real processing logic with mocked external calls
```

### 2. **Ignoring Error Cases**
```python
# ❌ BAD: Only testing success
def test_process_image(self):
    result = processor.process_image(valid_image)
    assert result["success"] is True

# ✅ GOOD: Testing both success and failure
def test_process_image_success(self):
    result = processor.process_image(valid_image)
    assert result["success"] is True

def test_process_image_failure(self):
    result = processor.process_image(invalid_image)
    assert result["success"] is False
    assert "error" in result
```

### 3. **Not Validating Performance**
```python
# ❌ BAD: Not measuring performance
def test_process_image(self):
    result = processor.process_image(image_data)
    assert result["success"] is True

# ✅ GOOD: Validating performance
def test_process_image_performance(self):
    start_time = time.time()
    result = processor.process_image(image_data)
    processing_time = time.time() - start_time
    
    assert result["success"] is True
    assert processing_time < PERFORMANCE_THRESHOLDS["image_processing_time"]
```

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Pytest-Cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Testing Best Practices](https://docs.python.org/3/library/unittest.html)

## 🎉 Success Criteria

- ✅ **Real business logic tested** - Not just mocked
- ✅ **80%+ test coverage** - Comprehensive coverage achieved
- ✅ **Performance validated** - All thresholds met
- ✅ **Integration tested** - Real service communication verified
- ✅ **Error handling tested** - Comprehensive error scenarios covered
- ✅ **Production-ready quality** - Tests suitable for CI/CD
- ✅ **Maintainable code** - Clear, documented, and maintainable tests

Remember: The goal is to create a **production-ready test suite** that validates real functionality and ensures system reliability. Test real business logic, use strategic mocking, and maintain comprehensive coverage.
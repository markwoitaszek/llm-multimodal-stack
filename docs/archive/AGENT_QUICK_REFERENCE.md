# Agent Quick Reference: Real Test Implementation

## 🎯 Current Status
- **Application**: 29 Python files, ~5,836 lines of production code
- **Test Infrastructure**: ✅ Complete and working
- **Current Tests**: Mostly stubs with heavy mocking
- **Goal**: Build real tests that verify actual business logic

## 📁 Key Files to Examine

### **Application Code (Real Business Logic)**
```
services/multimodal-worker/app/
├── models.py          # ModelManager - ML model loading/management
├── processors.py      # Image/Video/Text processing (455 lines)
├── database.py        # Database operations
├── storage.py         # MinIO object storage
└── api.py            # FastAPI endpoints

services/retrieval-proxy/app/
├── vector_store.py    # Qdrant vector operations (287 lines)
├── retrieval.py       # Search algorithms (414 lines)
├── database.py        # Database operations
└── api.py            # FastAPI endpoints

services/ai-agents/app/
├── agent_manager.py   # LangChain agent management (264 lines)
├── tools.py          # Tool registry and execution
├── memory.py         # Agent memory management
└── api.py            # FastAPI endpoints
```

### **Current Test Structure (Stubs)**
```
services/*/tests/
├── test_models.py     # 93 test cases (mocked)
├── test_processors.py # Image/Video/Text tests (mocked)
├── test_database.py   # Database tests (mocked)
├── test_storage.py    # Storage tests (mocked)
└── test_api.py       # API tests (mocked)
```

## 🚀 Implementation Priority

### **Phase 1: Critical Business Logic (Start Here)**
1. **ImageProcessor.process_image()** - Core image processing pipeline
2. **VectorStoreManager.search_vectors()** - Core search functionality
3. **AgentManager.execute_agent()** - Core agent execution

### **Phase 2: Integration Points**
1. **Service-to-service communication** (multimodal-worker → retrieval-proxy)
2. **Database operations** (real PostgreSQL/Qdrant operations)
3. **File storage operations** (real MinIO operations)

### **Phase 3: Performance & Load**
1. **ML model inference times** (real model performance)
2. **API response times** (real endpoint performance)
3. **Concurrent operations** (system under load)

## 🛠️ Test Data Requirements

### **Create Test Fixtures**
```python
# Test images (small, real images)
test_images/
├── red_square_100x100.jpg
├── blue_circle_200x200.jpg
└── test_pattern_300x300.jpg

# Test videos (short, real videos)
test_videos/
├── sample_10s.mp4
└── sample_30s.mp4

# Test text samples
test_text/
├── short_text.txt
├── medium_text.txt
└── long_text.txt
```

### **Test Database Setup**
```python
# Use real PostgreSQL with test schema
# Use real Qdrant with test collections
# Use real MinIO with test buckets
```

## 🎯 Example: Real Test vs Current Stub

### **Current Stub (What We Have)**
```python
async def test_generate_image_embedding(image_processor):
    test_image = Image.new('RGB', (100, 100))
    mock_embedding = np.random.rand(512)
    image_processor.model_manager.get_model.return_value.get_image_features.return_value.cpu.return_value.numpy.return_value.flatten.return_value = mock_embedding
    result = await image_processor.generate_image_embedding(test_image)
    assert isinstance(result, np.ndarray)
    assert result.shape == (512,)
```

### **Real Test (What We Need)**
```python
async def test_generate_image_embedding_with_real_model(image_processor):
    # Load real test image
    test_image = Image.open("tests/fixtures/red_square_100x100.jpg")
    
    # Use real model (or mock only the heavy loading part)
    with patch('app.models.CLIPModel.from_pretrained') as mock_clip:
        mock_clip.return_value = create_mock_clip_model()
        result = await image_processor.generate_image_embedding(test_image)
    
    # Test actual embedding properties
    assert isinstance(result, np.ndarray)
    assert result.shape == (512,)  # CLIP ViT-B/32 embedding size
    assert not np.allclose(result, 0)  # Not all zeros
    assert np.isfinite(result).all()  # All finite values
```

## 🔧 Tools & Commands

### **Run Tests**
```bash
# Run all tests
./scripts/run-tests.sh all

# Run specific service tests
./scripts/run-tests.sh unit

# Run with coverage
./scripts/run-tests.sh all --coverage
```

### **Test Environment**
```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Check service health
curl http://localhost:8001/health  # multimodal-worker
curl http://localhost:8002/health  # retrieval-proxy
curl http://localhost:8003/health  # ai-agents
```

### **Create Test Data**
```bash
# Create test images
python scripts/create_test_data.py --images

# Create test videos
python scripts/create_test_data.py --videos

# Setup test databases
python scripts/setup_test_db.py
```

## 📊 Success Metrics

### **Coverage Targets**
- **Unit Tests**: 80%+ code coverage
- **Integration Tests**: All service interactions covered
- **Performance Tests**: All critical paths benchmarked

### **Test Quality**
- **Real Data**: Use actual test images, videos, text
- **Real Services**: Test actual database/storage operations
- **Real Performance**: Measure actual ML model inference times
- **Real Integration**: Test actual service-to-service communication

## 🎯 Key Principles

1. **Test Real Functionality**: Don't just test mocks
2. **Use Real Data**: Test with actual images, videos, text
3. **Test Real Services**: Use real databases, storage, APIs
4. **Maintain Structure**: Keep existing test file organization
5. **Focus on Critical Paths**: Start with most important business logic
6. **Ensure Reliability**: Tests should be fast, consistent, maintainable

## 🚨 Common Pitfalls to Avoid

- ❌ **Over-mocking**: Don't mock everything, test real logic
- ❌ **Fake data**: Use real test data, not just random values
- ❌ **Ignoring integration**: Test how services actually work together
- ❌ **Performance ignorance**: Measure real performance, not mock performance
- ❌ **Breaking existing structure**: Maintain the current test organization

## 💡 Pro Tips

1. **Start Small**: Begin with one service, one test file
2. **Use Real Models**: Test actual ML model behavior where possible
3. **Test Edge Cases**: Use real edge case data (empty images, malformed text)
4. **Measure Performance**: Benchmark actual inference times
5. **Document Test Data**: Clearly document what test data represents
6. **Maintain Fixtures**: Keep test data organized and reusable

Remember: You're building tests for a **production system** with **real ML models, databases, and APIs**. The goal is to create tests that actually verify the system works correctly in production scenarios.

# Agent Prompt: Build Real Tests for LLM Multimodal Stack

## 🎯 Mission
You are tasked with building **real, comprehensive tests** for a production-ready LLM Multimodal Stack application. The testing infrastructure is already in place, but the current tests are mostly stubs with heavy mocking. Your job is to create **actual tests that verify real business logic** while maintaining the existing test structure.

## 📊 Application Overview

### **Scale & Complexity**
- **29 Python files** with **~5,836 lines of production code**
- **3 microservices**: multimodal-worker, retrieval-proxy, ai-agents
- **Real ML models**: CLIP, BLIP, Whisper, SentenceTransformer
- **Real databases**: PostgreSQL, Qdrant vector store, MinIO object storage
- **Real APIs**: FastAPI with complex endpoints

### **Services Breakdown**

#### 1. **Multimodal Worker** (~2,000 lines)
- **ModelManager**: Loads and manages ML models (CLIP, BLIP, Whisper, SentenceTransformer)
- **ImageProcessor**: Image embedding generation, captioning, feature extraction
- **VideoProcessor**: Video transcription, keyframe extraction, audio processing  
- **TextProcessor**: Text chunking and embedding generation
- **Database/Storage/Cache managers**: Full persistence layer

#### 2. **Retrieval Proxy** (~1,400 lines)
- **VectorStoreManager**: Qdrant integration for vector operations
- **RetrievalEngine**: Semantic search and ranking algorithms
- **Database/Cache managers**: Full data layer

#### 3. **AI Agents** (~2,400 lines)
- **AgentManager**: Creates and manages autonomous AI agents using LangChain
- **ToolRegistry**: Tool management for agent capabilities
- **MemoryManager**: Agent memory and execution history
- **Templates**: Agent prompt templates and configurations

## 🧪 Current Test Infrastructure (Already Built)

### **What's Already Working**
- ✅ **pytest configuration** with 80% coverage target
- ✅ **Global fixtures** in `tests/conftest.py`
- ✅ **Service-specific fixtures** in each service's `tests/conftest.py`
- ✅ **Test runner script** (`scripts/run-tests.sh`)
- ✅ **Docker Compose test environment** (`docker-compose.test.yml`)
- ✅ **CI/CD workflow** (`.github/workflows/test.yml`)
- ✅ **Test structure** with unit/integration/performance directories

### **Current Test Files (Stubs)**
```
services/multimodal-worker/tests/
├── test_models.py          # 93 test cases (mostly mocked)
├── test_processors.py      # Image/Video/Text processor tests (mocked)
├── test_database.py        # Database manager tests (mocked)
├── test_storage.py         # Storage manager tests (mocked)
└── test_api.py            # API endpoint tests (mocked)

services/retrieval-proxy/tests/
├── test_vector_store.py    # Qdrant integration tests (mocked)
├── test_retrieval.py       # Search engine tests (mocked)
└── test_api.py            # API endpoint tests (mocked)

services/ai-agents/tests/
├── test_agent_manager.py   # Agent creation/execution tests (mocked)
├── test_tools.py          # Tool registry tests (mocked)
├── test_memory.py         # Memory manager tests (mocked)
└── test_api.py            # API endpoint tests (mocked)

tests/integration/
├── test_service_communication.py  # Service-to-service tests
└── test_workflow_execution.py     # End-to-end workflow tests

tests/performance/
├── test_api_response_times.py     # API performance benchmarks
└── test_model_inference.py        # ML model performance tests
```

## 🎯 Your Task: Build Real Tests

### **Phase 1: Unit Tests with Real Business Logic**

#### **Multimodal Worker - Real Tests Needed**

1. **ModelManager Tests**
   ```python
   # Instead of mocking everything, test real model loading
   async def test_clip_model_loading_with_real_model():
       """Test CLIP model loads and can process real images"""
       # Use a small test model or mock only the heavy parts
       # Test actual image embedding generation
   
   async def test_model_cleanup_releases_memory():
       """Test that model cleanup actually frees GPU memory"""
       # Test real memory cleanup, not just mock calls
   ```

2. **ImageProcessor Tests**
   ```python
   async def test_image_embedding_generation_with_real_image():
       """Test embedding generation with actual PIL Image"""
       # Use real test images, test actual embedding dimensions
   
   async def test_image_captioning_with_real_image():
       """Test BLIP captioning with real images"""
       # Test actual caption generation, not just mock returns
   
   async def test_image_feature_extraction():
       """Test feature extraction with real image data"""
       # Test actual brightness, color analysis, etc.
   ```

3. **VideoProcessor Tests**
   ```python
   async def test_video_keyframe_extraction():
       """Test keyframe extraction with real video file"""
       # Use small test video, test actual keyframe generation
   
   async def test_audio_transcription():
       """Test Whisper transcription with real audio"""
       # Test actual transcription, not just mock responses
   ```

#### **Retrieval Proxy - Real Tests Needed**

1. **VectorStoreManager Tests**
   ```python
   async def test_vector_storage_and_retrieval():
       """Test actual vector storage in Qdrant"""
       # Use real Qdrant instance, test actual vector operations
   
   async def test_similarity_search():
       """Test similarity search with real vectors"""
       # Test actual search results, not just mock returns
   ```

2. **RetrievalEngine Tests**
   ```python
   async def test_semantic_search_with_real_queries():
       """Test search with actual text queries"""
       # Test real search algorithms, ranking, etc.
   ```

#### **AI Agents - Real Tests Needed**

1. **AgentManager Tests**
   ```python
   async def test_agent_creation_with_real_tools():
       """Test agent creation with actual tool integration"""
       # Test real LangChain agent creation
   
   async def test_agent_execution_with_real_tasks():
       """Test agent execution with actual tasks"""
       # Test real agent reasoning and tool usage
   ```

2. **ToolRegistry Tests**
   ```python
   async def test_tool_execution_with_real_apis():
       """Test tools with actual API calls"""
       # Test real tool functionality, not just mocks
   ```

### **Phase 2: Integration Tests with Real Services**

1. **Service Communication Tests**
   ```python
   async def test_multimodal_worker_to_retrieval_proxy():
       """Test actual service-to-service communication"""
       # Start real services, test actual API calls
   
   async def test_end_to_end_image_processing_workflow():
       """Test complete image processing pipeline"""
       # Upload image → process → store → search → retrieve
   ```

2. **Database Integration Tests**
   ```python
   async def test_database_operations_with_real_data():
       """Test actual database operations"""
       # Use real PostgreSQL, test actual CRUD operations
   ```

### **Phase 3: Performance Tests with Real Workloads**

1. **ML Model Performance**
   ```python
   async def test_image_embedding_performance():
       """Test actual embedding generation speed"""
       # Measure real inference times, not just mock calls
   
   async def test_concurrent_model_usage():
       """Test model performance under load"""
       # Test actual concurrent model usage
   ```

2. **API Performance**
   ```python
   async def test_api_response_times_under_load():
       """Test actual API performance"""
       # Test real endpoints with real data
   ```

## 🛠️ Implementation Strategy

### **1. Start with Critical Path Tests**
Focus on the most important business logic first:
- Image processing pipeline
- Vector search functionality  
- Agent execution flow

### **2. Use Real Data Where Possible**
- **Test images**: Use small, real images for testing
- **Test videos**: Use short test videos for keyframe extraction
- **Test text**: Use real text samples for embedding tests
- **Test databases**: Use real database instances in test environment

### **3. Mock Only What's Necessary**
- **Heavy ML models**: Mock only the model loading, test the processing logic
- **External APIs**: Mock external services, test internal logic
- **File I/O**: Use real file operations with test data

### **4. Maintain Test Structure**
- Keep existing test file structure
- Use existing fixtures where possible
- Add new fixtures for real data
- Maintain the same test naming conventions

### **5. Test Environment Setup**
- Use the existing `docker-compose.test.yml` for real services
- Create test data fixtures (images, videos, text samples)
- Set up test databases with real schemas

## 📋 Deliverables

### **1. Enhanced Unit Tests**
- Replace mock-heavy tests with real business logic tests
- Maintain 80%+ code coverage
- Test actual functionality, not just mock interactions

### **2. Real Integration Tests**
- Test actual service-to-service communication
- Test real database operations
- Test real file storage operations

### **3. Performance Benchmarks**
- Test actual ML model performance
- Test real API response times
- Test system performance under load

### **4. Test Data & Fixtures**
- Create test images, videos, and text samples
- Set up test database schemas
- Create test configuration files

### **5. Documentation**
- Update test documentation with real test examples
- Document test data requirements
- Document performance benchmarks

## 🎯 Success Criteria

### **Functional Tests**
- ✅ All critical business logic paths tested with real data
- ✅ Service integration tested with real services
- ✅ Error handling tested with real error conditions
- ✅ Edge cases tested with real edge case data

### **Performance Tests**
- ✅ ML model inference times measured and benchmarked
- ✅ API response times measured and benchmarked
- ✅ System performance under load tested
- ✅ Memory usage and cleanup verified

### **Quality Metrics**
- ✅ 80%+ code coverage maintained
- ✅ All tests pass consistently
- ✅ Tests run in reasonable time (< 10 minutes)
- ✅ Tests are maintainable and readable

## 🚀 Getting Started

1. **Examine the existing test structure** in `services/*/tests/`
2. **Identify the most critical business logic** to test first
3. **Create test data fixtures** (images, videos, text samples)
4. **Start with one service** (recommend multimodal-worker)
5. **Build real tests incrementally** while maintaining existing structure
6. **Use the existing test runner** to verify tests work

## 💡 Key Principles

- **Test real functionality, not mocks**
- **Use real data where possible**
- **Maintain existing test structure**
- **Focus on critical business logic first**
- **Ensure tests are fast and reliable**
- **Document test data requirements**

Remember: You're building tests for a **production-ready application** with **real ML models, databases, and APIs**. The goal is to create tests that actually verify the system works correctly, not just that the test infrastructure works.

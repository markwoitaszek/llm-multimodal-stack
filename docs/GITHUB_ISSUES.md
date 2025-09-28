# GitHub Issues

## Issue #1: Create Real Integration Tests for Multimodal Worker API

### **Priority**: Medium
### **Type**: Enhancement
### **Labels**: `integration-tests`, `api`, `testing`, `future-phase`

### **Problem Statement**

The current API tests are failing because they're attempting to do real integration testing (downloading 139MB CLIP models, connecting to real databases) instead of unit testing. While this shows the system works end-to-end, we need proper separation between unit tests and integration tests.

### **Current Status**

- ✅ **Unit Tests**: 83/103 tests passing (100% of core functionality)
  - Model tests: 16/16 passing with real dependencies
  - Processor tests: 18/18 passing with real dependencies  
  - Storage tests: 20/20 passing with real dependencies
  - Database tests: 22/22 passing with real dependencies

- ⚠️ **API Tests**: 4/20 passing (failing due to integration requirements)
  - Tests are downloading real ML models (139MB CLIP model)
  - Tests are trying to connect to real PostgreSQL databases
  - Tests are attempting real MinIO storage operations

### **Proposed Solution**

Create a separate integration test suite that:

1. **Sets up real infrastructure**:
   - PostgreSQL database with proper schema
   - MinIO storage with required buckets
   - Redis cache server
   - Qdrant vector database

2. **Downloads and caches real models**:
   - CLIP model (139MB)
   - BLIP model for captioning
   - Whisper model for audio transcription
   - Sentence transformer models

3. **Tests real end-to-end workflows**:
   - Image upload → processing → storage → database
   - Video upload → transcription → keyframe extraction
   - Text processing → chunking → embedding generation
   - Search and retrieval operations

4. **Uses test data**:
   - Sample images, videos, and text documents
   - Predefined test cases with expected outputs
   - Performance benchmarks and validation

### **Implementation Plan**

#### Phase 1: Infrastructure Setup
- [ ] Create Docker Compose for test infrastructure
- [ ] Set up test database with schema migrations
- [ ] Configure test storage buckets
- [ ] Set up test vector database collections

#### Phase 2: Model Management
- [ ] Create model caching system for tests
- [ ] Download and cache required models
- [ ] Create model validation tests
- [ ] Implement model cleanup after tests

#### Phase 3: Integration Test Suite
- [ ] Create `tests/integration/` directory
- [ ] Implement image processing integration tests
- [ ] Implement video processing integration tests
- [ ] Implement text processing integration tests
- [ ] Implement search and retrieval tests

#### Phase 4: CI/CD Integration
- [ ] Add integration test job to GitHub Actions
- [ ] Set up test infrastructure in CI environment
- [ ] Add integration test coverage reporting
- [ ] Create integration test documentation

### **Acceptance Criteria**

- [ ] Integration tests run in isolated environment
- [ ] Tests use real infrastructure (PostgreSQL, MinIO, Redis, Qdrant)
- [ ] Tests use real ML models and processing
- [ ] Tests validate end-to-end workflows
- [ ] Tests can run in CI/CD pipeline
- [ ] Clear separation between unit tests and integration tests
- [ ] Integration tests complete in reasonable time (< 10 minutes)

### **Benefits**

1. **Confidence**: Real end-to-end testing ensures system works in production
2. **Regression Prevention**: Catches integration issues early
3. **Documentation**: Tests serve as living documentation of system behavior
4. **Performance Validation**: Ensures system meets performance requirements
5. **Quality Assurance**: Validates real ML model outputs and accuracy

### **Technical Notes**

- Use pytest markers to separate unit vs integration tests
- Consider using testcontainers for infrastructure setup
- Implement proper test data management and cleanup
- Add performance benchmarking and validation
- Consider using smaller test models for faster execution

### **Estimated Effort**

- **Setup**: 2-3 days
- **Implementation**: 1-2 weeks  
- **CI/CD Integration**: 2-3 days
- **Documentation**: 1-2 days

**Total**: ~3 weeks

---

*This issue addresses the need for comprehensive integration testing while keeping unit tests fast and focused on individual components.*

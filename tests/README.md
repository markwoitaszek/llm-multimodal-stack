# Testing Infrastructure

## Overview

This directory contains comprehensive testing infrastructure for the Multimodal LLM Stack, including unit tests, integration tests, performance tests, and CI/CD integration.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── ai-agents/          # AI Agents service tests
│   ├── ide-bridge/         # IDE Bridge service tests
│   ├── protocol-integration/ # Protocol Integration service tests
│   ├── realtime-collaboration/ # Real-Time Collaboration service tests
│   └── n8n-monitoring/     # n8n Monitoring service tests
├── integration/            # Integration tests
│   ├── api/               # API integration tests
│   ├── database/          # Database integration tests
│   ├── websocket/         # WebSocket integration tests
│   └── services/          # Service-to-service integration tests
├── performance/           # Performance and load tests
│   ├── load/              # Load testing
│   ├── stress/            # Stress testing
│   └── benchmarks/        # Performance benchmarks
├── e2e/                   # End-to-end tests
│   ├── user-workflows/    # User workflow tests
│   ├── agent-execution/   # Agent execution tests
│   └── collaboration/     # Collaboration feature tests
├── fixtures/              # Test fixtures and data
├── utils/                 # Testing utilities
└── config/                # Test configuration
```

## Test Requirements

### Unit Tests
- **Coverage**: 90%+ code coverage
- **Scope**: Individual functions, classes, and modules
- **Framework**: pytest
- **Mocking**: unittest.mock, pytest-mock
- **Assertions**: pytest assertions

### Integration Tests
- **Scope**: API endpoints, database operations, service communication
- **Framework**: pytest with httpx for API testing
- **Database**: Test database with fixtures
- **Services**: Docker Compose test environment

### Performance Tests
- **Load Testing**: 100+ concurrent users
- **Response Times**: <200ms for API endpoints
- **Memory Usage**: Monitor memory consumption
- **Framework**: locust, pytest-benchmark

### End-to-End Tests
- **Scope**: Complete user workflows
- **Framework**: pytest with selenium/playwright
- **Browser**: Chrome, Firefox, Safari
- **Mobile**: Responsive design testing

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Start test services
docker-compose -f docker-compose.test.yml up -d
```

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=services --cov-report=html

# Run specific service tests
pytest tests/unit/ai-agents/ -v
pytest tests/unit/ide-bridge/ -v
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run API tests
pytest tests/integration/api/ -v

# Run database tests
pytest tests/integration/database/ -v
```

### Performance Tests

```bash
# Run performance tests
pytest tests/performance/ -v

# Run load tests
locust -f tests/performance/load/locustfile.py --host=http://localhost:3000

# Run benchmarks
pytest tests/performance/benchmarks/ -v
```

### End-to-End Tests

```bash
# Run E2E tests
pytest tests/e2e/ -v

# Run with browser
pytest tests/e2e/ --browser=chrome

# Run mobile tests
pytest tests/e2e/ --mobile
```

## Test Configuration

### Environment Variables

```bash
# Test environment
TEST_ENVIRONMENT=testing
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/test_db
TEST_REDIS_URL=redis://localhost:6379/1
TEST_AI_AGENTS_URL=http://localhost:3000
TEST_IDE_BRIDGE_URL=http://localhost:3004
TEST_PROTOCOL_INTEGRATION_URL=http://localhost:3005
TEST_REALTIME_COLLABORATION_URL=http://localhost:3006
```

### Test Data

- **Fixtures**: Located in `tests/fixtures/`
- **Mock Data**: Generated using factory_boy
- **Database**: Test database with sample data
- **Files**: Test files and documents

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-test.txt
      - name: Run tests
        run: pytest tests/ --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Reports

- **Coverage**: HTML and XML reports
- **Performance**: Benchmark results
- **Load Testing**: Load test reports
- **E2E**: Screenshots and videos

## Test Utilities

### Database Fixtures

```python
# tests/utils/database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def test_db():
    engine = create_engine(TEST_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

### API Client

```python
# tests/utils/api_client.py
import httpx
import pytest

@pytest.fixture
async def api_client():
    async with httpx.AsyncClient() as client:
        yield client
```

### WebSocket Client

```python
# tests/utils/websocket_client.py
import websockets
import pytest

@pytest.fixture
async def websocket_client():
    async with websockets.connect("ws://localhost:3006/ws") as websocket:
        yield websocket
```

## Best Practices

### Test Organization

1. **One test file per module**
2. **Descriptive test names**
3. **Arrange-Act-Assert pattern**
4. **Independent tests**
5. **Clean up after tests**

### Test Data

1. **Use fixtures for common data**
2. **Generate test data dynamically**
3. **Clean up test data**
4. **Use realistic data**

### Assertions

1. **Specific assertions**
2. **Clear error messages**
3. **Test edge cases**
4. **Validate all outputs**

### Performance

1. **Mock external services**
2. **Use test databases**
3. **Parallel test execution**
4. **Optimize test setup**

## Troubleshooting

### Common Issues

1. **Test Database Connection**
   - Check database URL
   - Verify database is running
   - Check permissions

2. **Service Dependencies**
   - Start required services
   - Check service URLs
   - Verify health checks

3. **Test Timeouts**
   - Increase timeout values
   - Check service performance
   - Optimize test setup

### Debug Mode

```bash
# Run tests with debug output
pytest tests/ -v -s --log-cli-level=DEBUG

# Run specific test with debug
pytest tests/unit/ai-agents/test_agent_manager.py::test_create_agent -v -s
```

## Contributing

1. **Write tests for new features**
2. **Maintain test coverage**
3. **Update test documentation**
4. **Follow test conventions**

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [locust Documentation](https://docs.locust.io/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
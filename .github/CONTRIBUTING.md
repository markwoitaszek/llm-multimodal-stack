# 🤝 Contributing to Multimodal LLM Stack

Thank you for your interest in contributing to the Multimodal LLM Stack! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Branching Strategy](#branching-strategy)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Pledge

- **Be respectful** and inclusive
- **Be collaborative** and constructive
- **Be patient** with newcomers
- **Focus on the project** and technical discussions

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Git
- Python 3.11+
- NVIDIA GPU (for full testing)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/llm-multimodal-stack.git
   cd llm-multimodal-stack
   ```

2. **Set up development environment**
   ```bash
   ./scripts/setup.sh
   ```

3. **Start development stack**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

4. **Run tests**
   ```bash
   ./scripts/health-check.sh
   ./scripts/test-multimodal.sh
   ```

## 🔄 Development Workflow

### 1. Choose Your Contribution Type

- 🐛 **Bug Fix**: Fix an existing issue
- ✨ **Feature**: Add new functionality
- 📚 **Documentation**: Improve docs
- 🔧 **Maintenance**: Code cleanup, refactoring
- ⚡ **Performance**: Optimize existing code

### 2. Find or Create an Issue

- Check [existing issues](https://github.com/your-org/llm-multimodal-stack/issues)
- Use appropriate issue templates
- Discuss major changes in issues first

### 3. Follow the Branching Strategy

See [Branching Strategy](#branching-strategy) below.

## 🌳 Branching Strategy

We use **Git Flow** with some modifications for CI/CD automation:

### Main Branches

- **`main`**: Production-ready code, protected branch
- **`develop`**: Integration branch for features, auto-deploys to staging

### Supporting Branches

#### Feature Branches
- **Naming**: `feature/short-description` or `feature/issue-number`
- **From**: `develop`
- **Merge to**: `develop`
- **Lifespan**: Until feature is complete

```bash
# Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/add-video-thumbnails

# Work on feature
git add .
git commit -m "✨ Add video thumbnail generation"

# Push and create PR
git push origin feature/add-video-thumbnails
```

#### Hotfix Branches
- **Naming**: `hotfix/short-description` or `hotfix/issue-number`
- **From**: `main`
- **Merge to**: `main` and `develop`
- **Lifespan**: Until hotfix is deployed

```bash
# Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/fix-memory-leak

# Fix issue
git add .
git commit -m "🐛 Fix memory leak in image processor"

# Push and create PR to main
git push origin hotfix/fix-memory-leak
```

#### Release Branches
- **Naming**: `release/v1.2.3`
- **From**: `develop`
- **Merge to**: `main` and `develop`
- **Lifespan**: Until release is complete

### Branch Protection Rules

#### `main` branch:
- ✅ Require pull request reviews (1 reviewer)
- ✅ Require status checks to pass
- ✅ Require up-to-date branches
- ✅ Include administrators
- ❌ Allow force pushes

#### `develop` branch:
- ✅ Require status checks to pass
- ✅ Require up-to-date branches
- ❌ Allow force pushes

## 💬 Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/) with emoji prefixes:

### Format
```
<emoji> <type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types and Emojis

| Type | Emoji | Description | Release Impact |
|------|-------|-------------|----------------|
| `feat` | ✨ | New feature | Minor version |
| `fix` | 🐛 | Bug fix | Patch version |
| `docs` | 📚 | Documentation | Patch version |
| `style` | 🎨 | Code style changes | Patch version |
| `refactor` | ♻️ | Code refactoring | Patch version |
| `perf` | ⚡ | Performance improvements | Patch version |
| `test` | 🧪 | Adding tests | Patch version |
| `chore` | 🔧 | Maintenance tasks | Patch version |
| `ci` | 👷 | CI/CD changes | Patch version |
| `build` | 📦 | Build system changes | Patch version |
| `revert` | ⏪ | Revert changes | Patch version |

### Breaking Changes
For breaking changes, add `!` after the type or add `BREAKING CHANGE:` in the footer:

```bash
git commit -m "✨ feat!: redesign API endpoints

BREAKING CHANGE: API endpoints now use v2 format"
```

### Examples

```bash
# Good commits
git commit -m "✨ feat(worker): add video thumbnail generation"
git commit -m "🐛 fix(proxy): resolve memory leak in search cache"
git commit -m "📚 docs: update API reference for new endpoints"
git commit -m "⚡ perf(worker): optimize image processing pipeline"
git commit -m "🔧 chore: update dependencies to latest versions"

# Bad commits
git commit -m "fix stuff"
git commit -m "WIP"
git commit -m "Update file.py"
```

## 🔀 Pull Request Process

### Before Creating a PR

1. ✅ Ensure your branch is up to date with the target branch
2. ✅ Run all tests locally
3. ✅ Update documentation if needed
4. ✅ Add/update tests for your changes
5. ✅ Follow code style guidelines

### PR Creation

1. **Use the PR template** - fill out all relevant sections
2. **Clear title** - follow conventional commit format
3. **Detailed description** - explain what and why
4. **Link issues** - use "Fixes #123" or "Closes #123"
5. **Add reviewers** - at least one code owner
6. **Add labels** - help categorize the PR

### PR Review Process

#### As an Author:
- 📝 Respond to feedback promptly
- 🔄 Push changes to the same branch
- ✅ Resolve conversations when addressed
- 🙏 Be receptive to suggestions

#### As a Reviewer:
- 🔍 Review code quality and logic
- 🧪 Test functionality if possible
- 📚 Check documentation updates
- 🚀 Consider deployment impact
- 💬 Provide constructive feedback

### Merge Requirements

- ✅ All CI checks pass
- ✅ At least 1 approval from code owner
- ✅ No requested changes
- ✅ Branch is up to date
- ✅ All conversations resolved

## 🐛 Issue Guidelines

### Before Creating an Issue

1. 🔍 Search existing issues
2. 📚 Check documentation and troubleshooting guide
3. 🧪 Run health checks (`./scripts/health-check.sh`)

### Issue Types

Use the appropriate template:

- 🐛 **Bug Report**: For reporting bugs
- ✨ **Feature Request**: For suggesting enhancements
- 📋 **Task**: For maintenance and technical debt
- ❓ **Question**: Use Discussions instead

### Issue Quality

#### Good Issues Include:
- ✅ Clear, descriptive title
- ✅ Detailed description
- ✅ Steps to reproduce (for bugs)
- ✅ Expected vs actual behavior
- ✅ Environment information
- ✅ Relevant logs/screenshots

#### Labels We Use:
- **Type**: `bug`, `enhancement`, `task`, `question`
- **Priority**: `critical`, `high`, `medium`, `low`
- **Component**: `api`, `worker`, `proxy`, `docs`, `ci`
- **Status**: `needs-triage`, `in-progress`, `blocked`

## 🎨 Code Style

### Python

We follow **PEP 8** with some modifications:

```python
# Use Black formatter
black services/

# Use isort for imports
isort services/

# Use flake8 for linting
flake8 services/ --max-line-length=88
```

#### Key Guidelines:
- ✅ Maximum line length: 88 characters
- ✅ Use type hints
- ✅ Use docstrings (Google style)
- ✅ Use async/await for I/O operations
- ✅ Handle exceptions appropriately
- ✅ Use logging instead of print statements

#### Example:
```python
async def process_image(
    self, 
    image_path: str, 
    document_id: str
) -> Dict[str, Any]:
    """
    Process an image and extract features.
    
    Args:
        image_path: Path to the image file
        document_id: Document UUID
        
    Returns:
        Dictionary containing processing results
        
    Raises:
        ProcessingError: If image processing fails
    """
    try:
        logger.info(f"Processing image: {image_path}")
        # Implementation here
        return {"success": True, "features": features}
    except Exception as e:
        logger.error(f"Image processing failed: {e}")
        raise ProcessingError(f"Failed to process {image_path}: {e}")
```

### Docker

- ✅ Use multi-stage builds
- ✅ Minimize layer count
- ✅ Use specific base image tags
- ✅ Include health checks
- ✅ Set proper user permissions
- ✅ Use .dockerignore

### YAML

- ✅ Use 2-space indentation
- ✅ Quote strings when necessary
- ✅ Use consistent naming
- ✅ Add comments for complex configurations

## 🧪 Testing

### Test Types

1. **Unit Tests**: Test individual functions/classes
2. **Integration Tests**: Test service interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Test system performance

### Running Tests

```bash
# All tests
./scripts/test-multimodal.sh

# Health checks
./scripts/health-check.sh

# Performance tests
./scripts/benchmark.sh

# Specific service tests
cd services/multimodal-worker
python -m pytest tests/
```

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.mark.asyncio
async def test_process_image_success():
    """Test successful image processing"""
    # Arrange
    processor = ImageProcessor(mock_model, mock_db, mock_storage)
    
    # Act
    result = await processor.process_image("test.jpg", "doc-id")
    
    # Assert
    assert result["success"] is True
    assert "features" in result
```

### Test Coverage

- 🎯 Aim for 80%+ test coverage
- ✅ Test happy paths and error cases
- ✅ Mock external dependencies
- ✅ Use meaningful test names
- ✅ Keep tests fast and isolated

## 📚 Documentation

### Types of Documentation

1. **Code Comments**: Explain complex logic
2. **Docstrings**: Document functions/classes
3. **API Documentation**: OpenAPI/Swagger specs
4. **User Guides**: How to use features
5. **Developer Guides**: How to contribute

### Documentation Standards

- ✅ Keep documentation up to date with code
- ✅ Use clear, concise language
- ✅ Include examples and code snippets
- ✅ Test documentation examples
- ✅ Use consistent formatting

### Updating Documentation

When making changes that affect:
- **APIs**: Update `docs/api-reference.md`
- **Configuration**: Update `docs/configuration.md`
- **Deployment**: Update `DEPLOYMENT.md`
- **Troubleshooting**: Update `docs/troubleshooting.md`

## 🏆 Recognition

Contributors are recognized in:
- 📝 Release notes
- 👥 GitHub contributors page
- 🌟 Special mentions for significant contributions

## ❓ Questions?

- 💬 [GitHub Discussions](https://github.com/your-org/llm-multimodal-stack/discussions)
- 📚 [Documentation](docs/)
- 🐛 [Issues](https://github.com/your-org/llm-multimodal-stack/issues)

Thank you for contributing to the Multimodal LLM Stack! 🚀

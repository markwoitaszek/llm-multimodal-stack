# Pull Request

## 📋 Summary
<!-- Provide a brief description of your changes -->

## 🔗 Related Issues
<!-- Link to related issues using "Fixes #123" or "Closes #123" -->
- Fixes #
- Related to #

## 🚀 Type of Change
<!-- Mark the relevant option with an "x" -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration change
- [ ] 🧪 Test improvement
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🔒 Security improvement

## 🧪 Testing
<!-- Describe the tests you ran and how to reproduce them -->

### Test Environment
- [ ] Local development environment
- [ ] Docker Compose stack
- [ ] Production-like environment
- [ ] GPU testing (RTX 3090)

### Test Results
- [ ] All existing tests pass
- [ ] New tests added and passing
- [ ] Manual testing completed
- [ ] Health checks pass (`./scripts/health-check.sh`)
- [ ] Performance tests pass (`./scripts/benchmark.sh`)

### Test Commands
```bash
# Commands used to test the changes
./scripts/health-check.sh
./scripts/test-multimodal.sh
docker-compose up -d && docker-compose ps
```

## 📸 Screenshots/Demos
<!-- If applicable, add screenshots or demo videos -->

## 🔍 Code Quality
<!-- Confirm code quality checks -->
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is well-commented
- [ ] No debugging code left in place
- [ ] Error handling is appropriate
- [ ] Logging is appropriate

## 📚 Documentation
<!-- Documentation updates -->
- [ ] Updated relevant documentation in `docs/`
- [ ] Updated API documentation if applicable
- [ ] Updated configuration examples
- [ ] Updated troubleshooting guide if needed
- [ ] Added/updated code comments

## 🚀 Deployment
<!-- Deployment considerations -->
- [ ] No breaking changes to existing deployments
- [ ] Database migrations included (if applicable)
- [ ] Environment variable changes documented
- [ ] Docker image builds successfully
- [ ] No new security vulnerabilities introduced

## ⚠️ Breaking Changes
<!-- If this is a breaking change, describe what breaks and how to migrate -->

## 🔄 Migration Guide
<!-- If applicable, provide migration steps for users -->

## 📋 Checklist
<!-- Final checklist before merging -->
- [ ] PR title follows conventional commit format
- [ ] All CI checks are passing
- [ ] Code coverage hasn't decreased
- [ ] Security scan passes
- [ ] Performance impact assessed
- [ ] Ready for review

## 🤔 Questions for Reviewers
<!-- Any specific questions or areas you'd like reviewers to focus on -->

## 📝 Additional Notes
<!-- Any additional information that reviewers should know -->

---

### Reviewer Guidelines
- [ ] Code quality and style
- [ ] Test coverage and quality
- [ ] Documentation completeness
- [ ] Security considerations
- [ ] Performance impact
- [ ] Breaking changes assessment
- [ ] Deployment considerations

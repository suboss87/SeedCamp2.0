# Contributing to AdCamp

Thank you for your interest in contributing to AdCamp! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/adcamp.git
   cd adcamp
   ```
3. **Set up development environment**:
   ```bash
   make install
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Locally

```bash
# Start dev servers (API + Dashboard)
make dev

# Or manually:
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
streamlit run dashboard/app.py --server.port 8501
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_model_router.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Code Style

We use `ruff` for linting and `black` for formatting:

```bash
# Check code style
make lint

# Auto-format code
black app/ dashboard/
ruff check app/ --fix
```

## Making Changes

### 1. Code Changes

- Write clean, readable code
- Follow existing patterns and conventions
- Add docstrings for functions and classes
- Keep functions focused and single-purpose

### 2. Testing

- Add unit tests for new functions
- Add integration tests for new features
- Ensure all tests pass before submitting PR
- Aim for >80% code coverage

### 3. Documentation

- Update relevant README files
- Add docstrings to new code
- Update API documentation if endpoints change
- Add examples for new features

## Submitting Changes

### 1. Commit Messages

Use clear, descriptive commit messages:

```
feat: add batch video generation endpoint
fix: resolve rate limit handling in retry logic
docs: update GCP deployment guide
```

Prefixes:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `chore:` Build/tooling changes

### 2. Pull Requests

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR** on GitHub with:
   - Clear title and description
   - Link to related issues
   - Screenshots/videos for UI changes
   - Test results

3. **PR Checklist**:
   - [ ] Code follows project style
   - [ ] Tests added/updated and passing
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   - [ ] Commits are clean and meaningful

### 3. Review Process

- Maintainers will review your PR
- Address feedback promptly
- Rebase on main if conflicts arise
- Once approved, maintainers will merge

## Areas for Contribution

### 🐛 Bug Fixes
- Check [Issues](https://github.com/suboss87/adcamp/issues) for bugs
- Reproduce the bug
- Write a test that fails
- Fix the bug
- Verify test passes

### ✨ Features
- Discuss major features in Issues first
- Start with small, focused PRs
- Break large features into multiple PRs

### 📚 Documentation
- Fix typos and clarify instructions
- Add deployment guides for new platforms
- Create tutorials and examples
- Improve API documentation

### 🧪 Testing
- Add missing tests
- Improve test coverage
- Add integration tests
- Add performance benchmarks

### 🎨 UI/UX
- Improve Streamlit dashboard
- Add visualizations
- Enhance user experience

## Project Structure

```
adcamp/
├── app/                    # FastAPI backend
│   ├── services/          # Core business logic
│   ├── models/            # Pydantic schemas
│   └── utils/             # Utilities
├── dashboard/             # Streamlit UI
├── deploy/                # Deployment configs by platform
├── docs/                  # Documentation
├── examples/              # Usage examples
└── tests/                 # Test suite
```

## Development Tips

### Environment Variables

Create `.env` file:
```bash
ARK_API_KEY=your_test_key_here
ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
LOG_LEVEL=DEBUG
```

### Debugging

```python
# Add breakpoints
import pdb; pdb.set_trace()

# Or use debugger in VS Code
```

### Testing Against Real API

For integration tests, use test mode or staging environment to avoid production costs.

## Questions?

- **GitHub Discussions**: Ask questions, share ideas
- **Issues**: Report bugs, request features
- **Discord**: Join our community (link in README)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for making AdCamp better! 🎉

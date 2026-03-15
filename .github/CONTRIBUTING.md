# Contributing to SeedCamp

Thank you for your interest in contributing to SeedCamp! This document provides guidelines for contributing to the project.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/seedcamp.git
   cd seedcamp
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

### Bug Fixes
- Check [Issues](https://github.com/suboss87/seedcamp/issues) for bugs
- Reproduce the bug
- Write a test that fails
- Fix the bug
- Verify test passes

### Features
- Discuss major features in Issues first
- Start with small, focused PRs
- Break large features into multiple PRs

### Documentation
- Fix typos and clarify instructions
- Add deployment guides for new platforms
- Create tutorials and examples
- Improve API documentation

### Testing
- Add missing tests
- Improve test coverage
- Add integration tests
- Add performance benchmarks

### UI/UX
- Improve Streamlit dashboard
- Add visualizations
- Enhance user experience

## Good First Issues

New to SeedCamp? These are self-contained tasks that don't require deep knowledge of the codebase:

| Task | Difficulty | Files | Description |
|------|-----------|-------|-------------|
| **Add a new industry example** | Easy | `docs/examples/` | Write a script like `automotive_dealer.py` for another vertical (education, hospitality, travel). Follow the existing pattern. |
| **Add Azure deployment guide** | Easy | `deploy/azure/` | Create Terraform + docs for Azure Container Apps, following the GCP/AWS pattern. |
| **Add DigitalOcean deployment guide** | Easy | `deploy/digitalocean/` | Create deployment config for DigitalOcean App Platform. |
| **Multi-language brief support** | Medium | `app/services/script_writer.py` | Add a `language` parameter to script generation for non-English markets (SE Asia, LATAM). |
| **Interactive cost calculator** | Medium | `dashboard/` | Add a Streamlit page where users input SKU count, hero %, and refresh frequency to see projected annual costs. |
| **Dashboard chart improvements** | Easy | `dashboard/app.py` | Add cost-per-tier breakdown chart and hero vs catalog comparison visualizations. |
| **Batch timing benchmarks** | Medium | `docs/` | Run benchmarks at different batch sizes and concurrency levels, publish results. |
| **Webhook delivery retry** | Medium | `app/services/notifications.py` | Add retry logic for failed webhook deliveries (currently fire-and-forget). |
| **CSV validation error messages** | Easy | `app/services/csv_parser.py` | Improve error messages when CSV upload fails validation (row numbers, specific field errors). |
| **API rate limit headers** | Easy | `app/main.py` | Add `X-RateLimit-Remaining` and `X-RateLimit-Reset` response headers. |

Look for issues tagged [`good first issue`](https://github.com/suboss87/seedcamp/labels/good%20first%20issue) on GitHub.

## Project Structure

```
seedcamp/
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

- **GitHub Issues**: Report bugs, request features
- **GitHub Discussions**: Ask questions, share ideas

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for making SeedCamp better! 🎉

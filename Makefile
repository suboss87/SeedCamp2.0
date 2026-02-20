.PHONY: help install test dev docker-build docker-up docker-down monitoring-up monitoring-down deploy-gcp deploy-aws deploy-byteplus lint clean

# Default target
help:
	@echo "AdCamp - Available Commands"
	@echo "============================"
	@echo ""
	@echo "Development:"
	@echo "  make install          Install dependencies"
	@echo "  make dev              Run development servers (API + Dashboard)"
	@echo "  make test             Run test suite"
	@echo "  make lint             Run linters and formatters"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build     Build Docker image"
	@echo "  make docker-up        Start services with Docker Compose"
	@echo "  make docker-down      Stop Docker Compose services"
	@echo ""
	@echo "Monitoring:"
	@echo "  make monitoring-up    Start Prometheus + Grafana stack"
	@echo "  make monitoring-down  Stop monitoring stack"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-gcp       Deploy to GCP Cloud Run"
	@echo "  make deploy-aws       Deploy to AWS ECS (placeholder)"
	@echo "  make deploy-byteplus  Deploy to BytePlus VKE"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean            Clean build artifacts and caches"
	@echo "  make docs             Generate API documentation"

# Development targets
install:
	@echo "📦 Installing dependencies..."
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Installation complete"

dev:
	@echo "🚀 Starting development servers..."
	@echo "   API: http://localhost:8000"
	@echo "   Dashboard: http://localhost:8501"
	@echo "   Press Ctrl+C to stop"
	@(. venv/bin/activate && uvicorn app.main:app --reload --port 8000) & \
	(. venv/bin/activate && streamlit run dashboard/app.py --server.port 8501)

test:
	@echo "🧪 Running tests..."
	. venv/bin/activate && pytest tests/ -v --cov=app --cov-report=term-missing
	@echo "✅ Tests complete"

lint:
	@echo "🔍 Running linters..."
	. venv/bin/activate && ruff check app/ || true
	. venv/bin/activate && black app/ --check || true
	@echo "✅ Linting complete"

# Docker targets
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t adcamp:latest .
	@echo "✅ Docker image built: adcamp:latest"

docker-up:
	@echo "🐳 Starting Docker Compose services..."
	cd deploy/docker && docker-compose up -d
	@echo "✅ Services started"
	@echo "   API: http://localhost:8000"
	@echo "   Dashboard: http://localhost:8501"

docker-down:
	@echo "🐳 Stopping Docker Compose services..."
	cd deploy/docker && docker-compose down
	@echo "✅ Services stopped"

# Monitoring targets
monitoring-up:
	@echo "📊 Starting monitoring stack..."
	cd deploy/monitoring && docker-compose up -d
	@echo "✅ Monitoring stack started"
	@echo "   Grafana: http://localhost:3000 (admin/admin)"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   AlertManager: http://localhost:9093"

monitoring-down:
	@echo "📊 Stopping monitoring stack..."
	cd deploy/monitoring && docker-compose down
	@echo "✅ Monitoring stack stopped"

# Deployment targets
deploy-gcp:
	@echo "☁️  Deploying to GCP Cloud Run..."
	@if [ -z "$$GCP_PROJECT_ID" ]; then \
		echo "❌ Error: GCP_PROJECT_ID not set"; \
		echo "   Run: export GCP_PROJECT_ID=your-project-id"; \
		exit 1; \
	fi
	./deploy/gcp/deploy-all.sh
	@echo "✅ Deployment complete"

deploy-aws:
	@echo "☁️  AWS deployment not yet implemented"
	@echo "   See: deploy/aws/README.md for manual deployment"

deploy-byteplus:
	@echo "☁️  Deploying to BytePlus VKE..."
	cd deploy/byteplus && ./scripts/deploy.sh
	@echo "✅ Deployment complete"

# Utility targets
clean:
	@echo "🧹 Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf output/*.mp4 2>/dev/null || true
	@echo "✅ Cleaned"

docs:
	@echo "📚 API documentation available at:"
	@echo "   http://localhost:8000/docs (Swagger UI)"
	@echo "   http://localhost:8000/redoc (ReDoc)"
	@echo ""
	@echo "Start the API server with: make dev"

# Multi-stage build for optimized production image
FROM python:3.10-slim AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Production stage
FROM python:3.10-slim

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/
COPY dashboard/ ./dashboard/

# Create output directory with correct ownership
RUN mkdir -p output && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8501

# Set default PORT for Cloud Run compatibility
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

# Run FastAPI server using PORT environment variable
# Cloud Run sets PORT=8080, local Docker uses PORT=8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

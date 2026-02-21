# Multi-stage build for optimized production image
FROM python:3.10-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.10-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY dashboard/ ./dashboard/

# Create output directory
RUN mkdir -p output

# Expose ports
EXPOSE 8000 8501

# Set default PORT for Cloud Run compatibility
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT}/health')"

# Run FastAPI server using PORT environment variable
# Cloud Run sets PORT=8080, local Docker uses PORT=8000
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}

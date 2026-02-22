# Docker Compose Deployment

Deploy AdCamp locally using Docker Compose for development, testing, or running on your own infrastructure.

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ (included with Docker Desktop)
- 2GB available RAM
- 5GB disk space
- ModelArk API key

## Quick Start

1. **Create environment file**:
```bash
cat > .env << EOF
ARK_API_KEY=your_modelark_api_key_here
ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
OUTPUT_DIR=/app/output
LOG_LEVEL=INFO
EOF
```

2. **Start services**:
```bash
docker-compose up -d
```

3. **Verify deployment**:
```bash
# Check API health
curl http://localhost:8000/health

# Check dashboard
open http://localhost:8501
```

4. **View logs**:
```bash
docker-compose logs -f
```

## Configuration

### docker-compose.yml

The configuration deploys two services:

```yaml
services:
  api:        # FastAPI backend on port 8000
  dashboard:  # Streamlit UI on port 8501
```

### Environment Variables

Edit `.env` file to customize:

```bash
# Required
ARK_API_KEY=your_modelark_api_key_here
ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3

# Optional
OUTPUT_DIR=/app/output
LOG_LEVEL=DEBUG                     # DEBUG for development
MAX_CONCURRENT_GENERATIONS=5
HERO_SKU_THRESHOLD=0.20
```

### Persistent Storage

Videos are stored in a Docker volume:

```bash
# View generated videos
docker-compose exec api ls -lh /app/output

# Copy videos to host
docker cp adcamp-api:/app/output ./local-videos
```

## Development Workflow

### Hot Reload

For development with code hot-reload:

```yaml
# Add to docker-compose.yml under api service:
volumes:
  - ../../app:/app/app:ro
  - ../../dashboard:/app/dashboard:ro
command: uvicorn app.main:app --host 0.0.0.0 --reload
```

### Rebuild After Changes

```bash
# Rebuild images
docker-compose build

# Restart services
docker-compose up -d
```

### Execute Commands Inside Container

```bash
# Access API container shell
docker-compose exec api bash

# Run tests
docker-compose exec api pytest

# Check Python packages
docker-compose exec api pip list
```

## Testing

### Generate a Test Video

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Premium organic coffee beans — rich, bold, fair trade certified",
    "sku_id": "COFFEE-001",
    "sku_tier": "catalog",
    "platforms": ["tiktok"],
    "duration": 5
  }'
```

### Check Metrics

```bash
curl http://localhost:8000/metrics | grep video
```

## Troubleshooting

### Port Conflicts

If ports 8000 or 8501 are in use:

```yaml
# Edit docker-compose.yml
ports:
  - "8001:8000"  # Map to different host port
  - "8502:8501"
```

### Container Not Starting

```bash
# View detailed logs
docker-compose logs api

# Check container status
docker-compose ps

# Restart services
docker-compose restart
```

### Out of Memory

Increase Docker memory allocation:
- Docker Desktop → Settings → Resources → Memory → Set to 4GB+

### API Key Issues

```bash
# Verify API key is set
docker-compose exec api env | grep ARK_API_KEY

# Test API key manually
docker-compose exec api curl -H "Authorization: Bearer $ARK_API_KEY" \
  https://ark.ap-southeast.bytepluses.com/api/v3/models
```

## Production Considerations

⚠️ **Docker Compose is NOT recommended for production**. Consider:

- **No built-in load balancing**: Single instance only
- **No auto-scaling**: Manual scaling required
- **No managed SSL**: Requires reverse proxy (nginx, Traefik)
- **No managed backups**: Manual backup strategies needed
- **No health monitoring**: Requires external monitoring

For production, use:
- [GCP Cloud Run](../gcp/) - Serverless, auto-scaling
- [AWS ECS](../aws/) - Managed container orchestration
- [Kubernetes](../kubernetes/) - Full control, advanced features

### Adding Reverse Proxy (nginx)

```yaml
# Add to docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (deletes generated videos)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Resource Usage

Expected resource consumption:

| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| API | 0.5 cores | 512MB | 100MB |
| Dashboard | 0.2 cores | 256MB | 50MB |
| **Total** | **0.7 cores** | **768MB** | **150MB** |

Actual usage varies with load. Peak during video generation: ~1.5GB RAM.

## Next Steps

- **Test locally**: Generate sample videos using the dashboard
- **Deploy to staging**: Use [Railway](../railway/) or [Render](../render/)
- **Deploy to production**: Use [GCP Cloud Run](../gcp/) or [AWS ECS](../aws/)
- **Monitor**: See [deploy/monitoring/](../monitoring/) or check `/metrics` endpoint

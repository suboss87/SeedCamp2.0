# AdCamp Deployment Options

This directory contains deployment configurations for multiple cloud platforms and hosting services. Choose the option that best fits your needs.

## Quick Comparison

| Platform | Free Tier | Setup Time | Best For | Estimated Cost* | Guide |
|----------|-----------|------------|----------|----------------|-------|
| **Docker Compose** | ✅ Yes | 5 min | Local dev & testing | $0 | [docker/](./docker/) |
| **Railway** | ❌ No ($5/mo) | 10 min | Quick demos & prototypes | ~$60/yr | [railway/](./railway/) |
| **Render** | ✅ Yes | 15 min | Side projects & MVPs | Free tier available | [render/](./render/) |
| **GCP Cloud Run** | ✅ Yes (2M req/mo) | 20 min | Production workloads | ~$50/yr | [gcp/](./gcp/) |
| **AWS ECS/Fargate** | ✅ 12mo free tier | 30 min | AWS ecosystem | ~$100/yr | [aws/](./aws/) |
| **Generic Kubernetes** | Varies | 25 min | Multi-cloud, on-prem | Varies | [kubernetes/](./kubernetes/) |
| **BytePlus VKE** | ❌ Pay-as-you-go | 45 min | BytePlus-native stack | ~$200/yr | [byteplus/](./byteplus/) |

*Cost estimates based on 34,500 videos/year (95/day) + ModelArk API costs (~$2,760/yr). Infrastructure only.

## Decision Matrix

### For Development & Testing
- **Local development**: Use [Docker Compose](./docker/)
- **Team collaboration**: Deploy to [Railway](./railway/) or [Render](./render/) for shared staging environments

### For Production

#### Choose **GCP Cloud Run** if you want:
- ✅ Generous free tier (2M requests/month)
- ✅ Serverless auto-scaling (0 → 1000 instances)
- ✅ Pay only for actual usage
- ✅ Simple deployment (single command)
- ✅ Integrated monitoring & logging

#### Choose **AWS ECS/Fargate** if you:
- ✅ Already use AWS services
- ✅ Need advanced VPC networking
- ✅ Want deep integration with AWS ecosystem (ALB, RDS, etc.)
- ✅ Have AWS credits or enterprise agreement

#### Choose **BytePlus VKE** if you:
- ✅ Want to run everything on BytePlus infrastructure
- ✅ Need co-location with ModelArk APIs for ultra-low latency
- ✅ Have BytePlus enterprise support
- ⚠️ Note: No free tier available

#### Choose **Generic Kubernetes** if you:
- ✅ Need multi-cloud portability
- ✅ Already have a Kubernetes cluster (GKE, EKS, AKS, on-prem)
- ✅ Want full control over infrastructure
- ✅ Need advanced deployment patterns (canary, blue-green)

## Deployment Architecture

All deployments share the same core components:

```
┌─────────────────┐
│   FastAPI       │  Port 8000
│   (Main API)    │  - Video generation
└────────┬────────┘  - Script creation
         │           - Cost tracking
         │
         ├──────────> ModelArk API
         │           (Seed 1.8, Seedance)
         │
┌────────┴────────┐
│   Streamlit     │  Port 8501
│   (Dashboard)   │  - Campaign management
└─────────────────┘  - Analytics
```

## Feature Comparison

| Feature | Docker | Railway | Render | GCP | AWS | K8s | BytePlus |
|---------|--------|---------|--------|-----|-----|-----|----------|
| Auto-scaling | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Zero-downtime deploys | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Custom domains | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SSL/HTTPS | ❌ | ✅ (auto) | ✅ (auto) | ✅ (auto) | ✅ (ACM) | ⚠️ (manual) | ✅ |
| Monitoring built-in | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| CI/CD integration | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Infrastructure as Code | N/A | ❌ | ❌ | ✅ (Terraform) | ✅ (Terraform) | ✅ | ✅ (Terraform) |

## Environment Variables

All deployments require these environment variables:

```bash
# Required
ARK_API_KEY=your_modelark_api_key_here
ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3

# Optional
OUTPUT_DIR=/app/output              # Where to store generated videos
LOG_LEVEL=INFO                      # DEBUG, INFO, WARNING, ERROR
MAX_CONCURRENT_GENERATIONS=5        # Rate limiting
HERO_SKU_THRESHOLD=0.20            # Top 20% = hero SKUs
```

### Platform-specific secrets management:
- **GCP**: Use Secret Manager (automatic in Cloud Run)
- **AWS**: Use AWS Secrets Manager or Parameter Store
- **Kubernetes**: Use Kubernetes Secrets
- **Railway/Render**: Use platform's environment variable UI
- **Docker Compose**: Use `.env` file (never commit!)

## Cost Breakdown

### ModelArk API Costs (Shared across all platforms)
- Script generation (Seed 1.8): $0.25 per 1M input tokens, $2.00 per 1M output tokens
- Video generation (Seedance Pro): $1.20 per 1M tokens (~$0.13/video at 5s 720p)
- Video generation (Seedance Pro Fast): $0.70 per 1M tokens (~$0.08/video at 5s 720p)

**Blended average**: ~$0.09/video (20% hero SKUs, 80% catalog SKUs)

### Infrastructure Costs (34,500 videos/year)

| Platform | Compute | Storage | Network | Total/Year |
|----------|---------|---------|---------|-----------|
| Docker Compose | $0 (your hardware) | $0 | $0 | **$0** |
| Railway | $5/mo | Included | Included | **$60** |
| Render | Free tier | Included | Included | **$0-75** |
| GCP Cloud Run | ~$20/yr | ~$10/yr | ~$20/yr | **~$50** |
| AWS ECS | ~$60/yr | ~$15/yr | ~$25/yr | **~$100** |
| BytePlus VKE | ~$150/yr | ~$25/yr | ~$25/yr | **~$200** |

**Total Cost of Ownership** = Infrastructure + ModelArk APIs (~$2,760/yr) + monitoring/logging

## Getting Started

1. Choose your platform from the table above
2. Follow the platform-specific guide in its subdirectory
3. Set environment variables (especially `ARK_API_KEY`)
4. Deploy using the provided scripts or configurations
5. Test your deployment: `curl https://your-domain/health`

## Platform-Specific Guides

- **[Docker Compose](./docker/)** - Local development and testing
- **[Railway](./railway/)** - One-click deploy for quick prototypes
- **[Render](./render/)** - Free tier hosting for side projects
- **[GCP Cloud Run](./gcp/)** - Serverless production deployment
- **[AWS ECS/Fargate](./aws/)** - AWS-native container deployment
- **[Generic Kubernetes](./kubernetes/)** - Portable K8s manifests with Kustomize
- **[BytePlus VKE](./byteplus/)** - BytePlus Kubernetes Engine
- **[Monitoring Stack](./monitoring/)** - Prometheus + Grafana observability

## Monitoring & Observability

A complete monitoring stack is provided in `deploy/monitoring/` with:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Pre-configured dashboards for video generation, cost tracking, and performance
- **AlertManager**: Alert routing with Slack/Email/PagerDuty integration
- **Node Exporter + cAdvisor**: System and container metrics

**Quick start**:
```bash
cd deploy/monitoring
docker-compose up -d
# Access Grafana at http://localhost:3000 (admin/admin)
```

See [deploy/monitoring/README.md](./monitoring/README.md) for full setup guide.

## Terraform Support

Enterprise users can use Infrastructure as Code (Terraform) for:
- **GCP**: `deploy/gcp/terraform/` - Cloud Run + Secret Manager
- **AWS**: `deploy/aws/terraform/` - ECS Fargate + ALB + Secrets Manager
- **BytePlus**: `deploy/byteplus/terraform/` - VKE + ModelArk integration

Each includes `main.tf`, `variables.tf`, `outputs.tf`, and comprehensive README with cost estimates and production best practices.

## CI/CD Integration

A GitHub Actions workflow is provided in `.github/workflows/`:
- `deploy.yml` - Build, test, and deploy on merge to main

Adapt this for GitLab CI, CircleCI, Jenkins, or your preferred CI/CD platform. Add platform-specific deploy steps as needed (GCP Cloud Run, AWS ECS, BytePlus VKE).

## Support

- **Documentation**: See [docs/](../docs/) for detailed guides
- **Issues**: Report bugs at https://github.com/suboss87/adcamp/issues
- **Discussions**: Ask questions at https://github.com/suboss87/adcamp/discussions

## Next Steps

1. Start with [Docker Compose](./docker/) for local development
2. Deploy to [Railway](./railway/) or [Render](./render/) for staging
3. Graduate to [GCP Cloud Run](./gcp/) or [AWS ECS](./aws/) for production
4. Implement monitoring and observability (see [monitoring/](./monitoring/))
5. Set up CI/CD for automated deployments

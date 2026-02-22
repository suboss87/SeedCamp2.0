# GCP Cloud Run Deployment

Deploy AdCamp to Google Cloud Platform's serverless container platform with automatic scaling, HTTPS, and pay-per-use pricing.

## Why Cloud Run?

✅ **Generous free tier**: 2M requests/month, 360,000 GB-seconds/month  
✅ **Serverless**: Scales to zero when idle, no minimum cost  
✅ **Fast deployments**: ~2 minutes from code to production  
✅ **Automatic HTTPS**: Free SSL certificates  
✅ **Integrated monitoring**: Cloud Logging, Cloud Monitoring built-in  

**Estimated cost**: ~$50/year for 34,500 videos (95/day) + ModelArk API costs

## Prerequisites

1. **GCP Account**: [Create free account](https://cloud.google.com/free) ($300 credit)
2. **GCP Project**: Create or select a project
3. **gcloud CLI**: [Install gcloud](https://cloud.google.com/sdk/docs/install)
4. **Docker**: For local builds (optional)
5. **ModelArk API Key**: From BytePlus ModelArk console

## Quick Deploy (5 minutes)

### Option 1: Automated Script

```bash
# From repo root
cd deploy/gcp

# Set your GCP project
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=asia-southeast1

# Run deployment script
./scripts/deploy-gcp.sh
```

The script will:
1. Enable required APIs (Cloud Run, Secret Manager, Cloud Build)
2. Create secret for ModelArk API key
3. Build Docker image using Cloud Build
4. Deploy to Cloud Run
5. Output service URL

### Option 2: Manual Deployment

#### 1. Initialize gcloud

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Set region (choose closest to your users)
gcloud config set run/region asia-southeast1
```

#### 2. Enable APIs

```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com
```

#### 3. Create Secret for API Key

```bash
# Create secret
echo -n "YOUR_ARK_API_KEY" | gcloud secrets create adcamp-ark-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Run access to secret
gcloud secrets add-iam-policy-binding adcamp-ark-api-key \
  --member="serviceAccount:$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 4. Build Image

**Option A: Cloud Build (recommended)**

```bash
# From repo root
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/adcamp \
  --timeout=10m
```

**Option B: Local build + push**

```bash
# Build locally
docker build -t gcr.io/$(gcloud config get-value project)/adcamp .

# Configure Docker for GCR
gcloud auth configure-docker

# Push image
docker push gcr.io/$(gcloud config get-value project)/adcamp
```

#### 5. Deploy to Cloud Run

```bash
gcloud run deploy adcamp-api \
  --image gcr.io/$(gcloud config get-value project)/adcamp:latest \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-secrets=ARK_API_KEY=adcamp-ark-api-key:latest \
  --set-env-vars="ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3,OUTPUT_DIR=/tmp/output" \
  --cpu=2 \
  --memory=2Gi \
  --timeout=300 \
  --min-instances=0 \
  --max-instances=10 \
  --concurrency=80
```

#### 6. Get Service URL

```bash
gcloud run services describe adcamp-api \
  --platform managed \
  --region asia-southeast1 \
  --format 'value(status.url)'
```

## Configuration

### Environment Variables

Set via `--set-env-vars` flag:

```bash
gcloud run services update adcamp-api \
  --set-env-vars="LOG_LEVEL=DEBUG,MAX_CONCURRENT_GENERATIONS=10"
```

Available variables:
- `ARK_BASE_URL`: ModelArk API endpoint (default: https://ark.ap-southeast.bytepluses.com/api/v3)
- `OUTPUT_DIR`: Video storage path (default: /tmp/output)
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `MAX_CONCURRENT_GENERATIONS`: Rate limit (default: 5)
- `HERO_SKU_THRESHOLD`: Hero SKU percentage (default: 0.20)

### Secrets Management

Update API key:

```bash
# Add new version
echo -n "NEW_API_KEY" | gcloud secrets versions add adcamp-ark-api-key \
  --data-file=-

# Cloud Run automatically uses latest version
```

### Resource Limits

Adjust CPU/memory for your workload:

```bash
# Scale up for high traffic
gcloud run services update adcamp-api \
  --cpu=4 \
  --memory=4Gi \
  --max-instances=100

# Scale down for cost optimization
gcloud run services update adcamp-api \
  --cpu=1 \
  --memory=1Gi \
  --max-instances=5
```

### Scaling Configuration

```bash
# Always keep 1 instance warm (reduces cold start latency)
gcloud run services update adcamp-api --min-instances=1

# Handle traffic spikes
gcloud run services update adcamp-api --max-instances=50

# Concurrent requests per instance
gcloud run services update adcamp-api --concurrency=80
```

## Custom Domain

### 1. Map Domain

```bash
# Map your domain to the service
gcloud run domain-mappings create \
  --service adcamp-api \
  --domain api.yourdomain.com \
  --region asia-southeast1
```

### 2. Configure DNS

Follow the instructions from the command output to add DNS records at your domain registrar.

### 3. Verify

SSL certificate is automatically provisioned and may take 10-15 minutes.

```bash
curl https://api.yourdomain.com/health
```

## Monitoring & Logging

### View Logs

**Cloud Console**: [Cloud Run Logs](https://console.cloud.google.com/run)

**CLI**:
```bash
# Tail logs
gcloud run services logs read adcamp-api --follow

# Filter by severity
gcloud run services logs read adcamp-api --log-filter="severity>=ERROR"
```

### View Metrics

```bash
# Request count, latency, error rate
gcloud monitoring dashboards describe adcamp-api
```

**Cloud Console**: Automatic dashboards for request rate, latency, error rate

### Alerts

Create alert for error rate:

```bash
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="AdCamp High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

### Application Performance

Check custom metrics:

```bash
curl https://YOUR_SERVICE_URL/metrics
```

Integrate with Prometheus/Grafana for advanced monitoring.

## Continuous Deployment

### GitHub Actions (Recommended)

See [.github/workflows/deploy-gcp.yml](../../.github/workflows/deploy-gcp.yml)

Required secrets in GitHub:
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCP_SA_KEY`: Service account JSON key with Cloud Run Admin role

### Cloud Build Trigger

```bash
# Connect GitHub repo
gcloud alpha builds triggers create github \
  --repo-name=adcamp \
  --repo-owner=suboss87 \
  --branch-pattern="^main$" \
  --build-config=cloudbuild.yaml
```

Create `cloudbuild.yaml` in repo root:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/adcamp', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/adcamp']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - run
      - deploy
      - adcamp-api
      - --image=gcr.io/$PROJECT_ID/adcamp
      - --region=asia-southeast1
      - --platform=managed
```

## Cost Optimization

### Free Tier Limits
- 2M requests/month
- 360,000 GB-seconds compute time/month
- 1GB network egress/month

### Pricing Beyond Free Tier
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second  
- **Requests**: $0.40 per million requests
- **Network egress**: $0.12 per GB (to internet)

### Tips to Reduce Costs

1. **Scale to zero**: Set `--min-instances=0` for low-traffic periods
2. **Right-size resources**: Start with 1 CPU / 1GB, scale up if needed
3. **Optimize cold starts**: Keep `--min-instances=1` during business hours only
4. **Use Cloud CDN**: Cache video URLs to reduce egress
5. **Regional deployment**: Deploy in region closest to BytePlus ModelArk API

### Example Monthly Cost (34.5K videos)

Assumptions:
- 2,875 API requests/month (1 request per video generation)
- 5 seconds per request
- 2 CPU, 2GB RAM per instance

```
Compute: 2,875 requests × 5s × (2 CPU × $0.000024 + 2GB × $0.0000025) = ~$2.50
Requests: 2,875 / 1M × $0.40 = ~$0.00
Network: 10GB video URLs × $0.12 = ~$1.20
Total: ~$3.70/month (~$44/year)
```

Most usage fits **within free tier**! 🎉

## Terraform

For Infrastructure as Code, see [terraform/](./terraform/)

```bash
cd deploy/gcp/terraform

terraform init
terraform plan -var="project_id=YOUR_PROJECT_ID" -var="ark_api_key=YOUR_API_KEY"
terraform apply
```

## Troubleshooting

### Deployment Fails

```bash
# Check build logs
gcloud builds list --limit=5

# Check service status
gcloud run services describe adcamp-api
```

### Cold Start Latency

First request after idle may take 2-5 seconds. Solutions:
- Set `--min-instances=1` to keep instance warm
- Use Cloud Scheduler to ping `/health` every 5 minutes

### Permission Denied

```bash
# Grant yourself Cloud Run Admin role
gcloud projects add-iam-policy-binding $(gcloud config get-value project) \
  --member="user:YOUR_EMAIL" \
  --role="roles/run.admin"
```

### Secret Access Issues

```bash
# Verify secret exists
gcloud secrets describe adcamp-ark-api-key

# Grant service account access
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gcloud secrets add-iam-policy-binding adcamp-ark-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Testing

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe adcamp-api --format 'value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test video generation
curl -X POST $SERVICE_URL/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Premium headphones with noise cancelling and 40hr battery",
    "sku_id": "HEADPHONES-001",
    "sku_tier": "hero",
    "platforms": ["tiktok"],
    "duration": 5
  }'
```

## Cleanup

```bash
# Delete service
gcloud run services delete adcamp-api --region asia-southeast1

# Delete secret
gcloud secrets delete adcamp-ark-api-key

# Delete images
gcloud container images delete gcr.io/$(gcloud config get-value project)/adcamp
```

## Next Steps

- **Set up custom domain**: [Cloud Run Domain Mapping](https://cloud.google.com/run/docs/mapping-custom-domains)
- **Add Cloud CDN**: Cache video URLs for faster delivery
- **Enable CI/CD**: Use GitHub Actions or Cloud Build triggers
- **Monitor costs**: Set up budget alerts in GCP Console
- **Scale up**: Adjust `--max-instances` for traffic spikes

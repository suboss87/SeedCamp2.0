# AdCamp - Deployment Guide

Quick guide for deploying AdCamp to GCP Cloud Run with the modernized dashboard.

## 🚀 Quick Deploy (GCP Cloud Run)

### Prerequisites

1. **GCP Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **Docker** installed locally
4. **API Key** from BytePlus ModelArk

### One-Command Deployment

```bash
# Set your project ID
export GCP_PROJECT_ID=your-gcp-project-id

# Deploy everything (API + Dashboard)
make deploy-gcp
```

This single command will:
1. ✅ Build API Docker image
2. ✅ Build Dashboard Docker image  
3. ✅ Push images to Google Container Registry
4. ✅ Deploy API to Cloud Run (with secrets)
5. ✅ Deploy Dashboard to Cloud Run (connected to API)
6. ✅ Configure auto-scaling and timeouts
7. ✅ Set up public access

### What Gets Deployed

#### API Service
- **URL**: `https://adcamp-api-[hash].asia-southeast1.run.app`
- **Resources**: 2 vCPU, 2GB RAM
- **Scaling**: 0-10 instances
- **Timeout**: 300 seconds
- **Port**: 8000
- **Secrets**: ARK_API_KEY from Secret Manager

#### Dashboard Service  
- **URL**: `https://adcamp-dashboard-[hash].asia-southeast1.run.app`
- **Resources**: 1 vCPU, 512MB RAM
- **Scaling**: 0-5 instances
- **Timeout**: 120 seconds
- **Port**: 8501
- **Connected to**: Production API (automatic)

## 📊 Access Your Deployment

After deployment completes, you'll see:

```
╔════════════════════════════════════════════════════╗
║          Deployment Successful! 🎉                  ║
╚════════════════════════════════════════════════════╝

Access your services:
  🚀 API:       https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app
  📊 Dashboard: https://adcamp-dashboard-YOUR_PROJECT_HASH.asia-southeast1.run.app
  📖 API Docs:  https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app/docs
```

### Test Your Deployment

```bash
# Test API health
curl https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app/health

# Open dashboard in browser
open https://adcamp-dashboard-YOUR_PROJECT_HASH.asia-southeast1.run.app

# View API documentation
open https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app/docs
```

## 🔧 Configuration

### Dashboard Configuration

The modernized dashboard automatically connects to your production API:

```python
# Default (production)
API_URL = "https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app"

# Override via environment variable
API_URL = os.getenv("API_URL", "https://adcamp-api-...")
```

**To use a different API**:
```bash
# Update deployment
gcloud run services update adcamp-dashboard \
  --region asia-southeast1 \
  --set-env-vars "API_URL=https://your-custom-api-url.com"
```

### API Key Management

The API key is stored in GCP Secret Manager:

```bash
# View secret
gcloud secrets versions access latest --secret="adcamp-ark-api-key"

# Update secret
echo -n "new-api-key" | gcloud secrets versions add adcamp-ark-api-key --data-file=-

# Cloud Run will automatically use the latest version
```

## 📈 Monitoring

### Cloud Run Console
- **Dashboard**: https://console.cloud.google.com/run?project=your-gcp-project-id
- View metrics: requests/second, latency, errors
- Monitor costs and resource usage

### Logs
```bash
# View API logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adcamp-api" --limit 50 --format json

# View Dashboard logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adcamp-dashboard" --limit 50 --format json

# Follow logs in real-time
gcloud logging tail "resource.type=cloud_run_revision"
```

### Prometheus + Grafana (Optional)

For advanced monitoring, deploy the monitoring stack locally:

```bash
make monitoring-up
# Access Grafana at http://localhost:3000

# Configure remote scraping of Cloud Run metrics
# See deploy/monitoring/README.md for details
```

## 🔄 Updates and Rollbacks

### Deploy New Version

```bash
# Make changes to code
# Run deployment again
make deploy-gcp

# Cloud Run automatically performs zero-downtime rollout
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service adcamp-api --region asia-southeast1

# Rollback to previous revision
gcloud run services update-traffic adcamp-api \
  --region asia-southeast1 \
  --to-revisions adcamp-api-00002-abc=100
```

## 💰 Cost Management

### Typical Costs (asia-southeast1)

| Component | Monthly Cost |
|-----------|--------------|
| API (2 vCPU, 2GB) | ~$8-15 (depends on traffic) |
| Dashboard (1 vCPU, 512MB) | ~$3-6 |
| Container Registry | ~$0.50 |
| Secret Manager | $0.40 |
| **Total** | **~$12-22/month** |

**Plus** ModelArk API costs: ~$0.09/video (blended average)

### Optimize Costs

1. **Scale to zero** when not in use (already configured)
2. **Reduce min instances** (currently 0)
3. **Use Terraform** for infrastructure as code
4. **Monitor usage** in Cloud Console

## 🏗️ Alternative: Terraform Deployment

For production environments, use Terraform:

```bash
cd deploy/gcp/terraform

# Create terraform.tfvars
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars

# Deploy
terraform init
terraform plan
terraform apply
```

See `deploy/gcp/terraform/README.md` for full documentation.

## 🔐 Security Best Practices

1. ✅ **API Keys in Secret Manager** (not environment variables)
2. ✅ **HTTPS only** (Cloud Run enforces)
3. ✅ **Least privilege IAM** (service accounts)
4. ✅ **VPC connectors** (optional, for private resources)
5. ⚠️ **Public access** (currently enabled - restrict if needed)

### Restrict Access

To require authentication:

```bash
# Remove public access
gcloud run services remove-iam-policy-binding adcamp-dashboard \
  --region=asia-southeast1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# Add specific users
gcloud run services add-iam-policy-binding adcamp-dashboard \
  --region=asia-southeast1 \
  --member="user:your-email@example.com" \
  --role="roles/run.invoker"
```

## 📚 Additional Resources

- **GCP Cloud Run Docs**: https://cloud.google.com/run/docs
- **Streamlit Deployment**: https://docs.streamlit.io/deploy
- **BytePlus ModelArk**: https://www.byteplus.com/en/product/modelark

## 🆘 Troubleshooting

### Dashboard Can't Connect to API

```bash
# Check dashboard environment
gcloud run services describe adcamp-dashboard --region asia-southeast1 --format="value(spec.template.spec.containers[0].env)"

# Should see: API_URL=https://adcamp-api-...

# Update if needed
gcloud run services update adcamp-dashboard \
  --region asia-southeast1 \
  --set-env-vars "API_URL=https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app"
```

### API Returns 500 Errors

```bash
# Check logs for errors
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=adcamp-api AND severity=ERROR" --limit 10

# Common issues:
# - Invalid API key (check Secret Manager)
# - Cold start timeout (first request takes ~10s)
# - Image validation error (min 300px height)
```

### Deployment Fails

```bash
# Check Cloud Build logs
gcloud builds list --limit 5

# Check IAM permissions
gcloud projects get-iam-policy your-gcp-project-id

# Ensure APIs are enabled
gcloud services list --enabled
```

## 🎉 Success!

Your AdCamp deployment is now live with:
- ✅ Modern, production-ready dashboard
- ✅ Scalable Cloud Run infrastructure  
- ✅ Secure secret management
- ✅ Zero-downtime deployments
- ✅ Auto-scaling (0-10 instances)

**Current Deployment**:
- API: https://adcamp-api-YOUR_PROJECT_HASH.asia-southeast1.run.app
- Dashboard: https://adcamp-dashboard-YOUR_PROJECT_HASH.asia-southeast1.run.app

Start generating videos! 🎬

# Railway Deployment

Deploy SeedCamp to Railway for quick prototyping and demos with zero configuration.

## Why Railway?

✅ **Simple deployment**: Deploy from GitHub in 2 clicks  
✅ **Automatic HTTPS**: SSL certificates included  
✅ **Built-in CI/CD**: Auto-deploy on git push  
✅ **Usage-based billing**: $5/month minimum, scales with usage  

**Cost**: ~$60/year ($5/mo base) for moderate usage

## Prerequisites

- Railway account ([sign up free](https://railway.app))
- GitHub account with seedcamp repo
- ModelArk API key

## Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. **Go to Railway**: [railway.app/new](https://railway.app/new)
2. **Connect GitHub**: Authorize Railway to access your repos
3. **Select repo**: Choose `suboss87/SeedCamp2.0`
4. **Add variables**:
   ```
   ARK_API_KEY=your_modelark_api_key
   ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3
   OUTPUT_DIR=/app/output
   ```
5. **Deploy**: Railway automatically detects `railway.toml` and deploys

### Option 2: CLI Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set variables
railway variables set ARK_API_KEY=your_key_here
railway variables set ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3

# Deploy
railway up
```

## Configuration

### Environment Variables

Set in Railway dashboard under Variables tab:

```bash
ARK_API_KEY=your_key                # Required
ARK_BASE_URL=https://...            # Required
LOG_LEVEL=INFO                      # Optional
MAX_CONCURRENT_GENERATIONS=5        # Optional
```

### Custom Domain

1. Go to Settings → Networking
2. Add custom domain: `api.yourdomain.com`
3. Update DNS with provided CNAME record
4. SSL auto-provisioned in ~10 minutes

## Monitoring

- **Logs**: Dashboard → Deployments → View Logs
- **Metrics**: Dashboard → Metrics (CPU, RAM, network)
- **Alerts**: Configure in Settings → Notifications

## Cost

- **Base**: $5/month (includes $5 credit)
- **Usage**: Additional charges for CPU/RAM/network beyond base
- **Typical**: ~$5-10/month for moderate traffic

## Troubleshooting

### Build Fails

Check `railway.toml` exists in repo root and points to correct Dockerfile:

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"
```

### Service Not Starting

View logs in Railway dashboard → Deployments → Latest → Logs

## Next Steps

- **Monitor usage**: Track costs in Billing tab
- **Scale up**: Adjust resources if needed (auto-scales by default)
- **Add monitoring**: Integrate with external APM tools

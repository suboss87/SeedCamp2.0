# AdCamp — Quick Start (Go Live in 30 Minutes)

This guide gets AdCamp running in production **TODAY** using platforms that work with just your ModelArk API key.

---

## 🚀 **Option 1: Railway (Recommended)**

**Cost**: $5/month | **Time**: 10 minutes | **Best for**: Fast deployment, great DX

### Steps

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and create project**:
   ```bash
   railway login
   railway init
   ```

3. **Add your API key**:
   ```bash
   railway variables set ARK_API_KEY=your-api-key-here
   ```

4. **Deploy**:
   ```bash
   railway up
   ```

5. **Get your URL**:
   ```bash
   railway domain
   ```

That's it! Your API is live at `https://adcamp-production.up.railway.app`

**API Docs**: `https://your-url/docs`

---

## 🌐 **Option 2: Render**

**Cost**: Free tier available | **Time**: 15 minutes | **Best for**: Zero cost testing

### Steps

1. **Go to** [render.com](https://render.com)

2. **Click "New +" → "Web Service"**

3. **Connect GitHub**: `suboss87/adcamp`

4. **Settings**:
   - Name: `adcamp-api`
   - Region: `Singapore`
   - Branch: `main`
   - Runtime: `Docker`
   - Health Check Path: `/health`

5. **Add Environment Variable**:
   ```
   ARK_API_KEY = your-api-key-here
   ```

6. **Deploy** — Render auto-deploys from `render.yaml`

Your API will be live at `https://adcamp-api.onrender.com`

---

## 🐳 **Option 3: Docker Compose (Local Production Test)**

**Cost**: Free | **Time**: 5 minutes | **Best for**: Testing before cloud deploy

```bash
# Set API key
export ARK_API_KEY=your-api-key-here

# Start services
docker-compose up -d

# Test
curl http://localhost:8000/health

# Generate a video
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Summer product launch, energetic vibes",
    "sku_tier": "catalog",
    "sku_id": "TEST-001",
    "platforms": ["tiktok"],
    "duration": 5
  }'
```

---

## ☁️ **Option 4: BytePlus VKE (Full BytePlus Stack)**

**Cost**: Pay-as-you-go | **Time**: 60 minutes | **Best for**: BytePlus-native deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete VKE guide.

**Prerequisites**:
- BytePlus account with VKE access
- kubectl configured
- Docker installed

**Quick deploy**:
```bash
./scripts/deploy-vke.sh production
```

---

## ✅ **Testing Your Deployment**

### 1. Health Check
```bash
curl https://your-url/health
```

Expected response:
```json
{
  "status": "ok",
  "pipeline": "AdCamp Video Generation Pipeline",
  "models": {
    "script": "seed-1-8-251228",
    "video_pro": "seedance-1-5-pro-251215",
    "video_fast": "seedance-1-0-pro-fast-251015"
  }
}
```

### 2. Generate Test Video
```bash
curl -X POST https://your-url/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": "Running shoes, dynamic urban setting, golden hour",
    "sku_tier": "catalog",
    "sku_id": "SHOE-001",
    "platforms": ["tiktok"],
    "duration": 5
  }'
```

You'll get:
```json
{
  "task_id": "cgt-...",
  "status": "Processing",
  "cost": {
    "total_cost_usd": 0.078
  }
}
```

### 3. Check Video Status
```bash
curl https://your-url/api/wait/cgt-YOUR-TASK-ID
```

When done:
```json
{
  "status": "Succeeded",
  "video_url": "https://ark-content-generation...mp4"
}
```

---

## 📊 **Monitoring**

- **Metrics**: `https://your-url/metrics` (Prometheus format)
- **Health**: `https://your-url/health/detailed`
- **API Docs**: `https://your-url/docs` (Swagger UI)
- **Logs**: Check your platform's dashboard

---

## 💰 **Cost Comparison**

| Platform | Monthly Cost | Scaling | Setup Time |
|----------|-------------|---------|------------|
| **Railway** | $5 | Auto | 10 min |
| **Render** | Free-$7 | Auto | 15 min |
| **Docker Local** | $0 | Manual | 5 min |
| **BytePlus VKE** | Pay-as-go | Auto | 60 min |

**ModelArk API costs** (same across all):
- ~$0.09/video blended average
- 34,500 videos/year = ~$3,105/year

---

## 🎯 **Recommended Path**

1. **Today**: Deploy to Railway/Render for immediate production
2. **This week**: Test with real traffic
3. **Later**: Move to VKE if you need BytePlus-native features

---

## 🆘 **Troubleshooting**

### "Invalid API key"
- Check `ARK_API_KEY` is set correctly
- Get key from [ModelArk Console](https://console.byteplus.com/modelark)

### "Video generation timeout"
- Increase `POLL_TIMEOUT` environment variable
- Check ModelArk API status

### "Health check failing"
- Verify `/health` endpoint returns 200
- Check logs for startup errors

---

## 🔗 **Next Steps**

- ✅ Deploy to Railway/Render (production)
- ✅ Test with real videos
- ✅ Monitor metrics and costs
- ⏭️ Scale up if needed
- ⏭️ Add custom domain
- ⏭️ Set up CI/CD

**Questions?** [GitHub Issues](https://github.com/suboss87/adcamp/issues)

# Deploy to Render

One-click deployment using Render's native Docker support.

## Prerequisites

- A [Render](https://render.com) account
- A [BytePlus ModelArk](https://www.byteplus.com/en/product/modelark) API key

## Deploy

1. Fork this repository
2. Go to [Render Dashboard](https://dashboard.render.com) and create a new **Web Service**
3. Connect your fork
4. Render auto-detects the `render.yaml` blueprint
5. Set the `ARK_API_KEY` environment variable in the Render dashboard
6. Deploy

The service will be available at `https://your-service.onrender.com`.

## Configuration

See [`render.yaml`](render.yaml) for the service definition. Key settings:

- **Health check**: `/health`
- **Plan**: Free or Starter ($7/month for always-on)
- **Environment**: `ARK_API_KEY` (required), `DRY_RUN` (optional, set to `true` for testing)

## Verify

```bash
curl https://your-service.onrender.com/health
curl https://your-service.onrender.com/docs   # Swagger UI
```

For full configuration options, see [docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md).

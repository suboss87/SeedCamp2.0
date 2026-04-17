# SeedCamp Deployment Guide

This guide covers deploying the SeedCamp Video Generation Pipeline to production using **BytePlus VKE (Vital Kubernetes Engine)** and other cloud platforms.

## Table of Contents
- [BytePlus VKE Deployment (Recommended)](#byteplus-vke-deployment-recommended)
- [Docker Compose Deployment](#docker-compose-deployment)
- [Local Development](#local-development)
- [Environment Configuration](#environment-configuration)

---

## BytePlus VKE Deployment (Recommended)

BytePlus [VKE (Vital Kubernetes Engine)](https://docs.byteplus.com/en/docs/vke/What-is-Vital-Kubernetes-Engine) is the managed Kubernetes service from BytePlus, providing enterprise-grade container management with native integration to ModelArk APIs.

### Prerequisites

1. **BytePlus Account** with VKE access
2. **ModelArk API Key** (from [ModelArk Console](https://console.byteplus.com/modelark))
3. **kubectl** CLI tool installed
4. **Docker** installed for building images

### Step 1: Build and Push Container Image

#### Option A: Using BytePlus Container Registry (CR)

> Replace `<instance>` below with your CR instance name from [console.byteplus.com/cr](https://console.byteplus.com/cr). See [CR docs](https://docs.byteplus.com/en/docs/cr/what-is-cr).

```bash
# Log in to BytePlus CR
docker login <instance>-ap-southeast-1.cr.bytepluses.com

# Build the Docker image
docker build -t <instance>-ap-southeast-1.cr.bytepluses.com/your-namespace/seedcamp:latest .

# Push to BytePlus CR
docker push <instance>-ap-southeast-1.cr.bytepluses.com/your-namespace/seedcamp:latest
```

#### Option B: Using Docker Hub

```bash
# Build and push to Docker Hub
docker build -t your-dockerhub-username/seedcamp:latest .
docker push your-dockerhub-username/seedcamp:latest
```

### Step 2: Create VKE Cluster

1. Log in to [BytePlus VKE Console](https://console.byteplus.com/vke)
2. Click **Create Cluster**
3. Configure cluster settings:
   - **Region**: ap-southeast-1 (Singapore) — closest to ModelArk API
   - **Cluster Type**: Standard
   - **Node Pool**: 
     - Instance Type: `ecs.g3i.xlarge` (4 vCPU, 16 GB RAM)
     - Nodes: 2-3 nodes for high availability
   - **Network**: VPC with internet access
4. Wait for cluster creation (~5-10 minutes)

### Step 3: Connect to Your Cluster

```bash
# Download kubeconfig from VKE console
# Set KUBECONFIG environment variable
export KUBECONFIG=/path/to/your/kubeconfig.yaml

# Verify connection
kubectl get nodes
```

### Step 4: Create Secret with ModelArk API Key

```bash
# Create secret from command line
kubectl create secret generic seedcamp-secrets \
  --from-literal=ARK_API_KEY=your-api-key-here \
  --from-literal=ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3

# OR edit deploy/kubernetes/base/secret.yaml and apply
kubectl apply -f deploy/kubernetes/base/secret.yaml
```

### Step 5: Update Deployment Manifests

Edit `deploy/kubernetes/base/deployment-api.yaml` and `deploy/kubernetes/base/deployment-dashboard.yaml`:

```yaml
image: <instance>-ap-southeast-1.cr.bytepluses.com/your-namespace/seedcamp:latest
```

### Step 6: Deploy to VKE

```bash
# Apply all manifests
kubectl apply -f deploy/kubernetes/base/

# Check deployment status
kubectl get pods
kubectl get services

# Get external IP (LoadBalancer)
kubectl get svc seedcamp-api
kubectl get svc seedcamp-dashboard
```

### Step 7: Access Your Application

```bash
# Get API external IP
API_IP=$(kubectl get svc seedcamp-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "API: http://$API_IP"

# Get Dashboard external IP
DASHBOARD_IP=$(kubectl get svc seedcamp-dashboard -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
echo "Dashboard: http://$DASHBOARD_IP"
```

### Monitoring and Logs

```bash
# View API logs
kubectl logs -f deployment/seedcamp-api

# View dashboard logs
kubectl logs -f deployment/seedcamp-dashboard

# Check resource usage
kubectl top pods
```

### Scaling

```bash
# Scale API replicas
kubectl scale deployment seedcamp-api --replicas=5

# Enable autoscaling
kubectl autoscale deployment seedcamp-api --cpu-percent=70 --min=2 --max=10
```

---

## Docker Compose Deployment

For quick local or VM deployment using Docker Compose:

### Prerequisites

- Docker and Docker Compose installed
- BytePlus ModelArk API key

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/suboss87/SeedCamp2.0.git
   cd seedcamp
   ```

2. **Set environment variables**:
   ```bash
   export ARK_API_KEY=your-api-key-here
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Dashboard: http://localhost:8501

5. **View logs**:
   ```bash
   docker-compose logs -f
   ```

6. **Stop services**:
   ```bash
   docker-compose down
   ```

---

## Local Development

### Prerequisites

- Python 3.10+
- FFmpeg (optional, for video post-processing if extended)
- BytePlus ModelArk API key

### Setup

1. **Clone and navigate to the project**:
   ```bash
   git clone https://github.com/suboss87/SeedCamp2.0.git
   cd seedcamp
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ARK_API_KEY
   ```

5. **Run the API server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. **Run the dashboard** (in a separate terminal):
   ```bash
   source venv/bin/activate
   streamlit run dashboard/app.py --server.port 8501
   ```

7. **Access the application**:
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Dashboard: http://localhost:8501

---

## Environment Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ARK_API_KEY` | BytePlus ModelArk API key | **(Required)** |
| `ARK_BASE_URL` | ModelArk API base URL | `https://ark.ap-southeast.bytepluses.com/api/v3` |
| `OUTPUT_DIR` | Directory for generated videos | `./output` |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SCRIPT_MODEL` | Script generation model | `seed-1-8-251228` |
| `VIDEO_MODEL_PRO` | Hero SKU video model | `dreamina-seedance-2-0-260128` |
| `VIDEO_MODEL_FAST` | Catalog SKU video model | `dreamina-seedance-2-0-fast-260128` |
| `POLL_TIMEOUT` | Video generation timeout (seconds) | `300` |
| `POLL_INTERVAL` | Polling interval (seconds) | `5` |

### Production Environment Files

For different environments, create separate config files:

- `.env.production` — Production settings
- `.env.staging` — Staging environment
- `.env.development` — Local development

---

## Cost Optimization

### BytePlus VKE Cost Optimization

1. **Use appropriate instance types**:
   - Start with `ecs.g3i.large` (2 vCPU, 8 GB) for API
   - Scale up only if needed

2. **Enable cluster autoscaling**:
   - Automatically scale nodes based on workload
   - Reduce costs during low-traffic periods

3. **Use spot instances** (if available):
   - Save up to 70% on compute costs
   - Suitable for non-critical workloads

4. **Monitor ModelArk API costs**:
   - Blended average: ~$0.09/video (20/80 premium/standard split)
   - Use Catalog SKUs (Pro Fast) for 80% of videos
   - Reserve Hero SKUs (Pro) for top 20% products

---

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Common issues:
# - Image pull errors: Verify image URL and registry auth
# - Resource limits: Adjust CPU/memory requests in deployment
# - Secret not found: Verify secret creation
```

### API health check failing

```bash
# Test health endpoint
kubectl exec -it <pod-name> -- curl http://localhost:8000/health

# Check environment variables
kubectl exec -it <pod-name> -- env | grep ARK
```

### Video generation timeout

- Increase `POLL_TIMEOUT` environment variable
- Check ModelArk API status at [status.byteplus.com](https://status.byteplus.com)
- Verify API key has sufficient quota

---

## Support

For issues or questions:

- **BytePlus VKE**: [VKE Documentation](https://docs.byteplus.com/vke)
- **ModelArk**: [ModelArk Documentation](https://docs.byteplus.com/modelark)
- **Project Issues**: [GitHub Issues](https://github.com/suboss87/SeedCamp2.0/issues)

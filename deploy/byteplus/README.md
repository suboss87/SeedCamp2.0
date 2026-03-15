# BytePlus VKE Deployment (Recommended)

Deploy SeedCamp to [BytePlus VKE (Vital Kubernetes Engine)](https://docs.byteplus.com/en/docs/vke/What-is-Vital-Kubernetes-Engine) — the managed Kubernetes service from BytePlus. Co-locating with ModelArk gives you the lowest possible API latency and a single-vendor stack.

## Why BytePlus VKE?

- **Co-located with ModelArk** — Same network as the Seed/Seedance API. Lowest latency, no cross-cloud egress fees.
- **Unified platform** — Compute, container registry, Kubernetes, and AI inference on one console ([console.byteplus.com](https://console.byteplus.com)).
- **Enterprise Kubernetes** — Managed control plane, HPA, cluster autoscaler, Karpenter, VCI (serverless pods).
- **Integrated observability** — Built-in pod monitoring, log collection, and resource metrics via VKE console.

**Estimated cost**: ~$200/year infrastructure (excludes ModelArk API usage).

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| BytePlus account | [console.byteplus.com](https://console.byteplus.com) with VKE enabled |
| `kubectl` | [Install guide](https://kubernetes.io/docs/tasks/tools/) |
| Docker | For building container images |
| ModelArk API key | From [ModelArk Console](https://console.byteplus.com/modelark) |
| BytePlus CR instance | [Container Registry](https://docs.byteplus.com/en/docs/cr/what-is-cr) in ap-southeast-1 |

## Architecture

```
BytePlus Cloud — ap-southeast-1 (Singapore)
┌──────────────────────────────────────────────┐
│  VKE Cluster (Vital Kubernetes Engine)       │
│  ┌────────────────────────────────────────┐  │
│  │  Namespace: seedcamp                     │  │
│  │                                        │  │
│  │  seedcamp-api (2 replicas)               │  │
│  │    ├── Script gen  → Seed 1.8          │──┼──> ModelArk API
│  │    └── Video gen   → Seedance Pro/Fast │  │    ark.ap-southeast.bytepluses.com
│  │                                        │  │    (same-region, ultra-low latency)
│  │  seedcamp-dashboard (1 replica)          │  │
│  │    └── Streamlit UI                    │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  BytePlus CR (Container Registry)            │
│    <instance>-ap-southeast-1.cr.bytepluses.com│
└──────────────────────────────────────────────┘
```

## Quick Deploy

### 1. Create VKE Cluster

**Via [VKE Console](https://console.byteplus.com/vke):**

1. Click **Create Cluster**
2. Region: `ap-southeast-1` (Singapore) — same region as ModelArk
3. Kubernetes version: 1.28+ (1.30 recommended)
4. Node pool: 2 nodes, `ecs.g3i.xlarge` (4 vCPU / 16 GB)
5. Network: VPC with internet access enabled

### 2. Connect kubectl

```bash
# Download kubeconfig from VKE Console → Cluster → Connection Info
export KUBECONFIG=~/.kube/config-vke

# Verify
kubectl get nodes
```

### 3. Build and Push Image to BytePlus CR

```bash
# Log in to your BytePlus Container Registry instance
# Replace <instance> with your CR instance name (from CR Console)
docker login <instance>-ap-southeast-1.cr.bytepluses.com

# Build
docker build -t <instance>-ap-southeast-1.cr.bytepluses.com/seedcamp/api:latest .

# Push
docker push <instance>-ap-southeast-1.cr.bytepluses.com/seedcamp/api:latest
```

> **CR URL format**: `<instance>-<region>.cr.bytepluses.com/<namespace>/<repo>:<tag>`
> Create your CR instance and namespace at [console.byteplus.com/cr](https://console.byteplus.com/cr).
> See [CR docs](https://docs.byteplus.com/en/docs/cr/what-is-cr) for setup.

### 4. Create Namespace and Secret

```bash
# Create namespace
kubectl apply -f vke/namespace.yaml

# Create secret with your ModelArk API key
kubectl create secret generic seedcamp-secrets \
  --from-literal=ARK_API_KEY=your_modelark_api_key_here \
  --from-literal=ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3 \
  --namespace=seedcamp
```

### 5. Update Image URL and Deploy

```bash
# Edit vke/deployment-api.yaml and vke/deployment-dashboard.yaml
# Replace <instance> with your CR instance name

# Deploy all manifests
kubectl apply -f vke/

# Watch rollout
kubectl rollout status deployment/seedcamp-api -n seedcamp --timeout=5m
kubectl rollout status deployment/seedcamp-dashboard -n seedcamp --timeout=5m
```

### 6. Get Service URL

```bash
# Get LoadBalancer external IP (may take 1-2 minutes)
kubectl get svc -n seedcamp

# Test
API_IP=$(kubectl get svc seedcamp-api -n seedcamp -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl http://$API_IP/health
```

### One-Command Deploy (Alternative)

```bash
# Set your CR instance name and deploy
export REGISTRY_INSTANCE=your-cr-instance
./scripts/deploy-vke.sh production
```

## Manifest Reference

| File | Purpose |
|------|---------|
| `vke/namespace.yaml` | Creates `seedcamp` namespace |
| `vke/secret.yaml` | API key template (use `kubectl create secret` instead) |
| `vke/deployment-api.yaml` | API server — 2 replicas, health checks, resource limits |
| `vke/deployment-dashboard.yaml` | Streamlit dashboard — 1 replica |
| `vke/service-api.yaml` | LoadBalancer for API (port 80 → 8000) |
| `vke/service-dashboard.yaml` | LoadBalancer for dashboard (port 80 → 8501) |
| `vke/ingress.yaml` | Optional — custom domain routing |

## Operations

### Scaling

```bash
# Manual scale
kubectl scale deployment seedcamp-api --replicas=5 -n seedcamp

# Horizontal Pod Autoscaler (CPU-based)
kubectl autoscale deployment seedcamp-api \
  --cpu-percent=70 --min=2 --max=10 -n seedcamp
```

### Rolling Updates

```bash
# Update image tag
kubectl set image deployment/seedcamp-api \
  api=<instance>-ap-southeast-1.cr.bytepluses.com/seedcamp/api:v2 \
  -n seedcamp

# Watch rollout
kubectl rollout status deployment/seedcamp-api -n seedcamp

# Rollback if needed
kubectl rollout undo deployment/seedcamp-api -n seedcamp
```

### Logs and Monitoring

```bash
# API logs
kubectl logs -f deployment/seedcamp-api -n seedcamp

# Dashboard logs
kubectl logs -f deployment/seedcamp-dashboard -n seedcamp

# Resource usage
kubectl top pods -n seedcamp
kubectl top nodes
```

VKE also provides built-in monitoring via the console: **VKE Console → Cluster → Monitoring**.

## Cost Breakdown

| Component | Monthly | Annual |
|-----------|---------|--------|
| VKE control plane | ~$0 (free for standard clusters) | $0 |
| Worker nodes (2 x ecs.g3i.xlarge) | ~$120 | ~$1,440 |
| LoadBalancer (2 services) | ~$20 | ~$240 |
| Container Registry | ~$5 | ~$60 |
| Network egress | Variable | Variable |
| **Infrastructure total** | **~$145** | **~$1,740** |

> ModelArk API costs are separate: ~$0.09/video blended average. At 34,500 videos/year = ~$3,105/year.

### Cost Optimization Tips

1. **Right-size nodes** — Start with `ecs.g3i.large` (2 vCPU / 8 GB) if traffic is low
2. **Cluster autoscaler** — Scale nodes down during off-hours
3. **Spot instances** — Use for non-production workloads (up to 70% savings)
4. **VCI (serverless pods)** — Burst to [Vital Container Instance](https://docs.byteplus.com/en/docs/vke/VCI-benefits) for spiky workloads without pre-provisioning nodes

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <POD_NAME> -n seedcamp
kubectl get events -n seedcamp --sort-by='.lastTimestamp'
```

### Image Pull Errors

Verify your CR instance is accessible and image exists:
```bash
docker pull <instance>-ap-southeast-1.cr.bytepluses.com/seedcamp/api:latest
```

If pulling from VKE nodes fails, ensure the VKE cluster VPC can reach the CR instance. See [CR FAQ](https://docs.byteplus.com/en/docs/cr/How-do-I-address-a-Docker-login-failure).

### LoadBalancer Stuck in Pending

VKE automatically provisions a CLB (Cloud Load Balancer). Allow 1-3 minutes. Check:
```bash
kubectl describe service seedcamp-api -n seedcamp
```

### ModelArk API Unreachable

Verify DNS resolution from inside the cluster:
```bash
kubectl exec -it deployment/seedcamp-api -n seedcamp -- \
  curl -s https://ark.ap-southeast.bytepluses.com/api/v3
```

If DNS fails, check VPC internet access settings in VKE console.

## Documentation

- [VKE Overview](https://docs.byteplus.com/en/docs/vke/What-is-Vital-Kubernetes-Engine)
- [VKE Regions](https://docs.byteplus.com/en/docs/vke/Regions-and-Availability-Zones)
- [Container Registry](https://docs.byteplus.com/en/docs/cr/what-is-cr)
- [ModelArk Quick Start](https://docs.byteplus.com/en/docs/ModelArk/1399008)
- [VKE Node Pools](https://docs.byteplus.com/en/docs/vke/NodePool-overview)
- [VKE Terraform](https://docs.byteplus.com/en/docs/vke/Managing-clusters-created-using-Terraform)

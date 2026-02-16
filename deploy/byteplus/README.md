# BytePlus VKE Deployment

Deploy AdCamp to BytePlus VKE (Volcano Engine Kubernetes) for a fully BytePlus-native stack with co-location benefits.

## Why BytePlus VKE?

✅ **Co-located with ModelArk**: Ultra-low latency to ModelArk APIs  
✅ **Unified platform**: Single vendor for compute + AI services  
✅ **Enterprise support**: Direct BytePlus support for full stack  
⚠️ **No free tier**: Pay-as-you-go pricing  

**Cost**: ~$200/year for cluster + workload

## Prerequisites

- BytePlus account with VKE enabled
- `kubectl` CLI tool ([install](https://kubernetes.io/docs/tasks/tools/))
- `volc` CLI (BytePlus CLI) or VKE web console access
- ModelArk API key
- Container registry (BytePlus CR or external)

## Architecture

```
BytePlus Cloud (Same Region)
┌─────────────────────────────────┐
│  VKE Cluster                    │
│  ┌───────────────────────────┐  │
│  │  adcamp-api (2 replicas)  │──┼──> ModelArk API
│  │  adcamp-dashboard (1 rep) │  │    (ultra-low latency)
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

## Quick Deploy

### 1. Create VKE Cluster

**Via Console**:
1. Go to VKE Console → Create Cluster
2. Choose region: `ap-southeast-1` (same as ModelArk)
3. Node spec: 2 nodes, 4 vCPU / 8GB each
4. Enable public access for API server

**Via CLI** (if available):
```bash
volc vke create-cluster \
  --cluster-name adcamp-cluster \
  --region ap-southeast-1 \
  --node-count 2 \
  --node-type ecs.g2.large
```

### 2. Configure kubectl

```bash
# Download kubeconfig from VKE console
# Or via CLI:
volc vke get-kubeconfig --cluster-name adcamp-cluster > ~/.kube/config-vke

# Set as default
export KUBECONFIG=~/.kube/config-vke

# Verify
kubectl get nodes
```

### 3. Create Secret for API Key

```bash
kubectl create secret generic adcamp-secrets \
  --from-literal=ARK_API_KEY=your_modelark_api_key_here \
  --namespace=default
```

### 4. Build and Push Image

**Option A: BytePlus CR**

```bash
# Login to BytePlus Container Registry
docker login cr-ap-southeast-1.bytepluses.com

# Build image
docker build -t cr-ap-southeast-1.bytepluses.com/adcamp/api:latest \
  -f ../../docker/Dockerfile ../../..

# Push
docker push cr-ap-southeast-1.bytepluses.com/adcamp/api:latest
```

**Option B: Use existing GCR/ECR image**

Update `vke/deployment.yaml` with your image URL.

### 5. Deploy to VKE

```bash
# Apply all manifests
kubectl apply -f vke/

# Or use automated script
./scripts/deploy.sh
```

### 6. Get Service URL

```bash
# Get LoadBalancer IP
kubectl get service adcamp-api -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Test
curl http://<EXTERNAL-IP>/health
```

## Configuration

### Manifests in `vke/`

- `namespace.yaml`: Creates `adcamp` namespace
- `secret.yaml`: Stores API key (template - populate before apply)
- `deployment.yaml`: API and dashboard deployments
- `service.yaml`: LoadBalancer services
- `ingress.yaml`: Ingress for custom domain (optional)

### Update Deployment

```bash
# Edit deployment
kubectl edit deployment adcamp-api -n adcamp

# Or apply updated manifest
kubectl apply -f vke/deployment.yaml

# Rollout status
kubectl rollout status deployment/adcamp-api -n adcamp
```

### Scaling

```bash
# Scale API replicas
kubectl scale deployment adcamp-api --replicas=5 -n adcamp

# Auto-scaling (HPA)
kubectl autoscale deployment adcamp-api \
  --cpu-percent=70 \
  --min=2 \
  --max=10 \
  -n adcamp
```

## Monitoring

### Logs

```bash
# View API logs
kubectl logs -f deployment/adcamp-api -n adcamp

# View dashboard logs
kubectl logs -f deployment/adcamp-dashboard -n adcamp
```

### Metrics

```bash
# Resource usage
kubectl top pods -n adcamp
kubectl top nodes
```

**Enable VKE Monitoring**: Configure in VKE console → Monitoring

## Cost Optimization

### VKE Cluster Costs
- **Control plane**: ~$50/month
- **Worker nodes**: 2 × 4vCPU/8GB ≈ ~$120/month
- **LoadBalancer**: ~$10/month
- **Network egress**: Variable

**Total**: ~$180-220/month base cost

### Tips
1. Use spot/preemptible instances for non-prod
2. Scale down during off-hours
3. Use HPA for auto-scaling
4. Enable cluster auto-scaler

## Terraform

For IaC deployment, see [terraform/](./terraform/)

```bash
cd deploy/byteplus/terraform

terraform init
terraform plan
terraform apply
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <POD_NAME> -n adcamp

# Check events
kubectl get events -n adcamp --sort-by='.lastTimestamp'
```

### Image Pull Errors

Ensure image is accessible:
```bash
# Test image pull locally
docker pull cr-ap-southeast-1.bytepluses.com/adcamp/api:latest
```

### LoadBalancer Pending

VKE provisions LoadBalancer automatically. May take 2-3 minutes.

```bash
# Check service
kubectl describe service adcamp-api -n adcamp
```

## Next Steps

- **Custom domain**: Configure ingress with your domain
- **SSL/TLS**: Add cert-manager for automatic HTTPS
- **Monitoring**: Set up Prometheus + Grafana
- **CI/CD**: Integrate with BytePlus CI/CD pipelines

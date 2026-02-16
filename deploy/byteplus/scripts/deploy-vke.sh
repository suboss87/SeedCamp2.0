#!/bin/bash
set -euo pipefail

# AdCamp - One-Command Deployment to BytePlus VKE
# Usage: ./scripts/deploy-vke.sh [environment]
# Example: ./scripts/deploy-vke.sh production

ENVIRONMENT=${1:-staging}
NAMESPACE=${NAMESPACE:-$ENVIRONMENT}
REGISTRY=${REGISTRY:-cr-ap-southeast-1.bytepluses.com}
REGISTRY_NAMESPACE=${REGISTRY_NAMESPACE:-your-namespace}
IMAGE_TAG=${IMAGE_TAG:-latest}

echo "🚀 Deploying AdCamp to BytePlus VKE..."
echo "   Environment: $ENVIRONMENT"
echo "   Namespace: $NAMESPACE"
echo "   Image: $REGISTRY/$REGISTRY_NAMESPACE/adcamp:$IMAGE_TAG"
echo ""

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl not found. Please install kubectl."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker not found. Please install Docker."; exit 1; }

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    echo "❌ kubectl is not configured. Please set KUBECONFIG or run 'kubectl config use-context <context>'"
    exit 1
fi

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -t $REGISTRY/$REGISTRY_NAMESPACE/adcamp:$IMAGE_TAG .

# Step 2: Push to registry
echo "📤 Pushing image to BytePlus Container Registry..."
docker push $REGISTRY/$REGISTRY_NAMESPACE/adcamp:$IMAGE_TAG

# Step 3: Create namespace if it doesn't exist
echo "📁 Creating namespace $NAMESPACE if it doesn't exist..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Create or update secret
if [ -f ".env" ]; then
    echo "🔐 Creating/updating secrets from .env file..."
    kubectl create secret generic adcamp-secrets \
        --from-env-file=.env \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "⚠️  No .env file found. Make sure secrets are configured manually."
fi

# Step 5: Update image in deployment manifests
echo "📝 Updating deployment manifests..."
sed "s|image: adcamp:latest|image: $REGISTRY/$REGISTRY_NAMESPACE/adcamp:$IMAGE_TAG|g" k8s/deployment-api.yaml > /tmp/deployment-api.yaml
sed "s|image: adcamp:latest|image: $REGISTRY/$REGISTRY_NAMESPACE/adcamp:$IMAGE_TAG|g" k8s/deployment-dashboard.yaml > /tmp/deployment-dashboard.yaml

# Step 6: Apply Kubernetes manifests
echo "☸️  Applying Kubernetes manifests..."
kubectl apply -f /tmp/deployment-api.yaml -n $NAMESPACE
kubectl apply -f /tmp/deployment-dashboard.yaml -n $NAMESPACE
kubectl apply -f k8s/service-api.yaml -n $NAMESPACE
kubectl apply -f k8s/service-dashboard.yaml -n $NAMESPACE

# Step 7: Wait for rollout
echo "⏳ Waiting for deployment to complete..."
kubectl rollout status deployment/adcamp-api -n $NAMESPACE --timeout=5m
kubectl rollout status deployment/adcamp-dashboard -n $NAMESPACE --timeout=5m

# Step 8: Get service endpoints
echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Endpoints:"
kubectl get svc -n $NAMESPACE

echo ""
echo "🔍 Pods:"
kubectl get pods -n $NAMESPACE

echo ""
echo "📝 To view logs:"
echo "   kubectl logs -f deployment/adcamp-api -n $NAMESPACE"
echo "   kubectl logs -f deployment/adcamp-dashboard -n $NAMESPACE"

echo ""
echo "🌐 To access the application, get the LoadBalancer external IP:"
echo "   API: kubectl get svc adcamp-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
echo "   Dashboard: kubectl get svc adcamp-dashboard -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"

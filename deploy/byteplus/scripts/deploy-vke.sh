#!/bin/bash
set -euo pipefail

# SeedCamp - One-Command Deployment to BytePlus VKE (Vital Kubernetes Engine)
# Usage: ./scripts/deploy-vke.sh [environment]
# Example: ./scripts/deploy-vke.sh production
#
# Required environment variables:
#   REGISTRY_INSTANCE  - Your BytePlus CR instance name
#
# Optional environment variables:
#   NAMESPACE          - Kubernetes namespace (default: environment name)
#   IMAGE_TAG          - Image tag (default: latest)
#   REGION             - BytePlus region (default: ap-southeast-1)

ENVIRONMENT=${1:-staging}
NAMESPACE=${NAMESPACE:-$ENVIRONMENT}
REGION=${REGION:-ap-southeast-1}
IMAGE_TAG=${IMAGE_TAG:-latest}

# BytePlus CR URL format: <instance>-<region>.cr.bytepluses.com
# See: https://docs.byteplus.com/en/docs/cr/what-is-cr
if [ -z "${REGISTRY_INSTANCE:-}" ]; then
    echo "Error: REGISTRY_INSTANCE is required."
    echo "Set it to your BytePlus Container Registry instance name."
    echo "Example: export REGISTRY_INSTANCE=my-cr-instance"
    echo "Create one at: https://console.byteplus.com/cr"
    exit 1
fi

REGISTRY="${REGISTRY_INSTANCE}-${REGION}.cr.bytepluses.com"
CR_NAMESPACE=${CR_NAMESPACE:-seedcamp}
IMAGE_URL="${REGISTRY}/${CR_NAMESPACE}/api:${IMAGE_TAG}"

echo "Deploying SeedCamp to BytePlus VKE (Vital Kubernetes Engine)"
echo "   Environment: $ENVIRONMENT"
echo "   Namespace:   $NAMESPACE"
echo "   Image:       $IMAGE_URL"
echo "   Region:      $REGION"
echo ""

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl not found. Install: https://kubernetes.io/docs/tasks/tools/"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Error: docker not found. Install Docker first."; exit 1; }

# Check if kubectl is configured
if ! kubectl cluster-info &>/dev/null; then
    echo "Error: kubectl is not configured."
    echo "Download kubeconfig from VKE Console: https://console.byteplus.com/vke"
    echo "Then: export KUBECONFIG=~/.kube/config-vke"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VKE_DIR="${SCRIPT_DIR}/vke"

# Step 1: Build Docker image
echo "[1/8] Building Docker image..."
docker build -t "$IMAGE_URL" -f "${SCRIPT_DIR}/../../Dockerfile" "${SCRIPT_DIR}/../.."

# Step 2: Push to BytePlus Container Registry
echo "[2/8] Pushing image to BytePlus CR ($REGISTRY)..."
docker push "$IMAGE_URL"

# Step 3: Create namespace
echo "[3/8] Creating namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Step 4: Create or update secret
if [ -f "${SCRIPT_DIR}/../../.env" ]; then
    echo "[4/8] Creating secrets from .env file..."
    kubectl create secret generic seedcamp-secrets \
        --from-env-file="${SCRIPT_DIR}/../../.env" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "[4/8] No .env file found. Ensure secrets are configured:"
    echo "   kubectl create secret generic seedcamp-secrets \\"
    echo "     --from-literal=ARK_API_KEY=your-key \\"
    echo "     --from-literal=ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3 \\"
    echo "     --namespace=$NAMESPACE"
fi

# Step 5: Update image URL in manifests and apply
echo "[5/8] Preparing manifests with image: $IMAGE_URL"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

for manifest in "$VKE_DIR"/*.yaml; do
    filename=$(basename "$manifest")
    sed "s|<instance>-ap-southeast-1.cr.bytepluses.com/seedcamp/api:latest|${IMAGE_URL}|g" \
        "$manifest" > "$TEMP_DIR/$filename"
done

# Step 6: Apply Kubernetes manifests
echo "[6/8] Applying VKE manifests..."
kubectl apply -f "$TEMP_DIR" -n "$NAMESPACE"

# Step 7: Wait for rollout
echo "[7/8] Waiting for deployments to be ready..."
kubectl rollout status deployment/seedcamp-api -n "$NAMESPACE" --timeout=5m
kubectl rollout status deployment/seedcamp-dashboard -n "$NAMESPACE" --timeout=5m

# Step 8: Show status
echo ""
echo "[8/8] Deployment complete!"
echo ""
echo "Services:"
kubectl get svc -n "$NAMESPACE"

echo ""
echo "Pods:"
kubectl get pods -n "$NAMESPACE"

echo ""
echo "Access:"
echo "  API:       kubectl get svc seedcamp-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
echo "  Dashboard: kubectl get svc seedcamp-dashboard -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"

echo ""
echo "Logs:"
echo "  kubectl logs -f deployment/seedcamp-api -n $NAMESPACE"
echo "  kubectl logs -f deployment/seedcamp-dashboard -n $NAMESPACE"

#!/bin/bash
set -e

# AdCamp - Complete GCP Cloud Run Deployment
# Deploys both API and Dashboard to GCP Cloud Run

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     AdCamp - GCP Cloud Run Deployment             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if GCP_PROJECT_ID is set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo "Usage: export GCP_PROJECT_ID=your-project-id && ./deploy-all.sh"
    exit 1
fi

PROJECT_ID=$GCP_PROJECT_ID
REGION="asia-southeast1"
API_SERVICE="adcamp-api"
DASHBOARD_SERVICE="adcamp-dashboard"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  API Service: $API_SERVICE"
echo "  Dashboard Service: $DASHBOARD_SERVICE"
echo ""

# Set GCP project
echo -e "${BLUE}[1/6] Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Build API image
echo -e "${BLUE}[2/6] Building API Docker image...${NC}"
docker build -t gcr.io/$PROJECT_ID/adcamp:latest -f Dockerfile .

# Build Dashboard image
echo -e "${BLUE}[3/6] Building Dashboard Docker image...${NC}"
docker build -t gcr.io/$PROJECT_ID/adcamp-dashboard:latest -f deploy/docker/Dockerfile.dashboard .

# Push API image
echo -e "${BLUE}[4/6] Pushing API image to GCR...${NC}"
docker push gcr.io/$PROJECT_ID/adcamp:latest

# Push Dashboard image
echo -e "${BLUE}[5/6] Pushing Dashboard image to GCR...${NC}"
docker push gcr.io/$PROJECT_ID/adcamp-dashboard:latest

# Deploy API
echo -e "${BLUE}[6/6] Deploying services to Cloud Run...${NC}"
echo ""
echo -e "${GREEN}Deploying API...${NC}"
gcloud run deploy $API_SERVICE \
  --image gcr.io/$PROJECT_ID/adcamp:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 2 \
  --memory 2Gi \
  --timeout 300 \
  --set-env-vars "ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3,OUTPUT_DIR=/app/output" \
  --set-secrets "ARK_API_KEY=adcamp-ark-api-key:latest" \
  --port 8000

# Get API URL
API_URL=$(gcloud run services describe $API_SERVICE --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✓ API deployed: $API_URL${NC}"
echo ""

# Deploy Dashboard with API URL
echo -e "${GREEN}Deploying Dashboard...${NC}"
gcloud run deploy $DASHBOARD_SERVICE \
  --image gcr.io/$PROJECT_ID/adcamp-dashboard:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 5 \
  --cpu 1 \
  --memory 512Mi \
  --timeout 120 \
  --set-env-vars "API_URL=$API_URL" \
  --port 8501

# Get Dashboard URL
DASHBOARD_URL=$(gcloud run services describe $DASHBOARD_SERVICE --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✓ Dashboard deployed: $DASHBOARD_URL${NC}"
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Deployment Successful! 🎉                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Access your services:${NC}"
echo "  🚀 API:       $API_URL"
echo "  📊 Dashboard: $DASHBOARD_URL"
echo "  📖 API Docs:  $API_URL/docs"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Test API health: curl $API_URL/health"
echo "  2. Open dashboard in browser: $DASHBOARD_URL"
echo "  3. View logs: gcloud logging read 'resource.type=cloud_run_revision' --limit 50"
echo ""
echo -e "${BLUE}Monitoring:${NC}"
echo "  • Cloud Run Console: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "  • Logs: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
echo "  • Metrics: https://console.cloud.google.com/monitoring?project=$PROJECT_ID"
echo ""

#!/bin/bash
set -e

# SeedCamp - GCP Cloud Build Deployment (No local Docker needed)
# Uses Google Cloud Build to build images in the cloud

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SeedCamp - Cloud Build Deployment               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if GCP_PROJECT_ID is set
if [ -z "$GCP_PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable is not set${NC}"
    echo "Usage: export GCP_PROJECT_ID=your-project-id && ./deploy-cloudbuild.sh"
    exit 1
fi

PROJECT_ID=$GCP_PROJECT_ID
REGION="asia-southeast1"
API_SERVICE="seedcamp-api"
DASHBOARD_SERVICE="seedcamp-dashboard"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Region: $REGION"
echo "  API Service: $API_SERVICE"
echo "  Dashboard Service: $DASHBOARD_SERVICE"
echo ""

# Set GCP project
echo -e "${BLUE}[1/4] Setting GCP project...${NC}"
gcloud config set project $PROJECT_ID

# Build API image using Cloud Build
echo -e "${BLUE}[2/4] Building API image with Cloud Build...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/seedcamp:latest --timeout=20m .

# Build Dashboard image using Cloud Build  
echo -e "${BLUE}[3/4] Building Dashboard image with Cloud Build...${NC}"
cat > /tmp/cloudbuild-dashboard.yaml <<EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/seedcamp-dashboard:latest', '-f', 'deploy/docker/Dockerfile.dashboard', '.']
images:
- 'gcr.io/$PROJECT_ID/seedcamp-dashboard:latest'
timeout: 1200s
EOF
gcloud builds submit --config /tmp/cloudbuild-dashboard.yaml .

# Deploy API
echo -e "${BLUE}[4/4] Deploying services to Cloud Run...${NC}"
echo ""
echo -e "${GREEN}Deploying API...${NC}"
gcloud run deploy $API_SERVICE \
  --image gcr.io/$PROJECT_ID/seedcamp:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 10 \
  --cpu 2 \
  --memory 2Gi \
  --timeout 300 \
  --set-env-vars "ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3,OUTPUT_DIR=/app/output" \
  --set-secrets "ARK_API_KEY=seedcamp-ark-api-key:latest" \
  --port 8000

# Get API URL
API_URL=$(gcloud run services describe $API_SERVICE --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✓ API deployed: $API_URL${NC}"
echo ""

# Deploy Dashboard with API URL
echo -e "${GREEN}Deploying Dashboard...${NC}"
gcloud run deploy $DASHBOARD_SERVICE \
  --image gcr.io/$PROJECT_ID/seedcamp-dashboard:latest \
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
echo -e "${GREEN}║          🎉 DEPLOYMENT SUCCESSFUL! 🎉              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}🌐 YOUR PRODUCTION URLS:${NC}"
echo ""
echo -e "  ${BLUE}🚀 API:${NC}       $API_URL"
echo -e "  ${BLUE}📊 Dashboard:${NC} $DASHBOARD_URL"
echo -e "  ${BLUE}📖 API Docs:${NC}  $API_URL/docs"
echo ""
echo -e "${YELLOW}🎬 Ready to use! Open the dashboard:${NC}"
echo -e "  ${GREEN}$DASHBOARD_URL${NC}"
echo ""
echo -e "${YELLOW}📈 Monitor your deployment:${NC}"
echo "  • Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo "  • Logs: https://console.cloud.google.com/logs?project=$PROJECT_ID"
echo ""

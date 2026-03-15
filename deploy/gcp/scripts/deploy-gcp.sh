#!/bin/bash
set -euo pipefail

# SeedCamp - Deploy to GCP Cloud Run
# Usage: ./scripts/deploy-gcp.sh

PROJECT_ID=${GCP_PROJECT_ID:-""}
REGION=${GCP_REGION:-"asia-southeast1"}
SERVICE_NAME="seedcamp-api"

echo "🚀 Deploying SeedCamp to GCP Cloud Run..."
echo "   Region: $REGION"
echo ""

# Check prerequisites
command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud not found. Install: https://cloud.google.com/sdk/docs/install"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker not found. Please install Docker."; exit 1; }

# Get project ID if not set
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$(gcloud config get-value project)
    if [ -z "$PROJECT_ID" ]; then
        echo "❌ No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
        exit 1
    fi
fi

echo "📁 Using GCP Project: $PROJECT_ID"
echo ""

# Enable required APIs
echo "🔧 Enabling required GCP APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    --project=$PROJECT_ID

# Create secret for API key
echo "🔐 Creating secret for ModelArk API key..."
if [ -f ".env" ]; then
    ARK_API_KEY=$(grep ARK_API_KEY .env | cut -d '=' -f2)
else
    echo "⚠️  No .env file found."
    read -p "Enter your ModelArk API key: " ARK_API_KEY
fi

echo -n "$ARK_API_KEY" | gcloud secrets create seedcamp-ark-api-key \
    --data-file=- \
    --replication-policy="automatic" \
    --project=$PROJECT_ID 2>/dev/null || \
echo -n "$ARK_API_KEY" | gcloud secrets versions add seedcamp-ark-api-key \
    --data-file=- \
    --project=$PROJECT_ID

# Build and push Docker image
echo "📦 Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/seedcamp:latest .

echo "📤 Pushing image to GCR..."
docker push gcr.io/$PROJECT_ID/seedcamp:latest

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/seedcamp:latest \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets=ARK_API_KEY=seedcamp-ark-api-key:latest \
    --set-env-vars="ARK_BASE_URL=https://ark.ap-southeast.bytepluses.com/api/v3,OUTPUT_DIR=/app/output" \
    --cpu=2 \
    --memory=2Gi \
    --timeout=300 \
    --min-instances=0 \
    --max-instances=10 \
    --concurrency=80 \
    --project=$PROJECT_ID

# Get service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --format 'value(status.url)' \
    --project=$PROJECT_ID)

echo "🌐 Your API is live at:"
echo "   $SERVICE_URL"
echo ""
echo "📊 Endpoints:"
echo "   Health: $SERVICE_URL/health"
echo "   API Docs: $SERVICE_URL/docs"
echo "   Metrics: $SERVICE_URL/metrics"
echo ""
echo "🧪 Test it:"
echo "   curl $SERVICE_URL/health"

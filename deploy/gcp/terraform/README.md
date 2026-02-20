# GCP Cloud Run Terraform Configuration

This directory contains Terraform configuration for deploying AdCamp to Google Cloud Run.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- GCP Project with billing enabled
- Docker images built and pushed to GCR

## Quick Start

### 1. Authenticate with GCP

```bash
gcloud auth application-default login
gcloud config set project your-gcp-project-id
```

### 2. Configure Variables

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your actual values
```

Required variables:
- `project_id`: Your GCP project ID
- `ark_api_key`: Your BytePlus ModelArk API key

### 3. Initialize Terraform

```bash
terraform init
```

### 4. Plan Deployment

```bash
terraform plan
```

### 5. Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 6. Get Outputs

```bash
terraform output
```

This will show:
- `api_url`: Your deployed API endpoint
- `dashboard_url`: Your deployed dashboard endpoint

## Configuration

### Resource Sizing

Adjust in `terraform.tfvars`:

```hcl
# For production with higher traffic
api_cpu           = "4"
api_memory        = "4Gi"
api_min_instances = "1"  # Keep 1 warm instance
api_max_instances = "50"

# For development/testing
api_cpu           = "1"
api_memory        = "1Gi"
api_min_instances = "0"  # Scale to zero when idle
api_max_instances = "5"
```

### Custom Docker Images

Update image references in `terraform.tfvars`:

```hcl
api_image       = "gcr.io/your-project/adcamp:v1.0.0"
dashboard_image = "gcr.io/your-project/adcamp-dashboard:v1.0.0"
```

## Managing Infrastructure

### Update Existing Deployment

```bash
# After updating terraform.tfvars or *.tf files
terraform plan
terraform apply
```

### View Current State

```bash
terraform show
```

### Destroy Resources

```bash
terraform destroy
```

⚠️ **Warning**: This will delete all Cloud Run services and secrets.

## Cost Optimization

### Free Tier Usage

With default settings (min_instances=0), you should stay within GCP's free tier:
- 2M requests/month
- 360,000 GB-seconds/month

### Estimated Costs (beyond free tier)

For 34,500 videos/year (~95/day):
- **Compute**: ~$2-5/month
- **Networking**: ~$1/month
- **Total**: **~$3-6/month** (~$36-72/year)

Most usage fits within the free tier! 🎉

## Terraform State Management

### Local State (Default)

State is stored locally in `terraform.tfstate`. **Do not commit this file**.

### Remote State (Recommended for Teams)

Use GCS backend:

```hcl
# Add to main.tf
terraform {
  backend "gcs" {
    bucket = "adcamp-terraform-state"
    prefix = "terraform/state"
  }
}
```

Create the bucket:
```bash
gsutil mb gs://adcamp-terraform-state
gsutil versioning set on gs://adcamp-terraform-state
```

## Troubleshooting

### Permission Denied

Grant required roles:
```bash
gcloud projects add-iam-policy-binding your-gcp-project-id \
  --member="user:YOUR_EMAIL" \
  --role="roles/run.admin"
```

### API Not Enabled

Terraform will enable required APIs automatically, but you can do it manually:
```bash
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com
```

### Secret Already Exists

If the secret already exists from manual deployment:
```bash
# Import existing secret
terraform import google_secret_manager_secret.ark_api_key projects/your-gcp-project-id/secrets/adcamp-ark-api-key

# Or delete and recreate
gcloud secrets delete adcamp-ark-api-key
```

## Files

- `main.tf`: Main Terraform configuration
- `variables.tf`: Input variable definitions
- `outputs.tf`: Output value definitions
- `terraform.tfvars.example`: Example variables file
- `README.md`: This file

## Next Steps

After deployment:
1. Test the API: `curl https://YOUR_API_URL/health`
2. Open the dashboard: `https://YOUR_DASHBOARD_URL`
3. Set up monitoring in GCP Console
4. Configure custom domain (optional)
5. Set up CI/CD for automated deployments

## Resources

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [AdCamp Deployment Guide](../README.md)

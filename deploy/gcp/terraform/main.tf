terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "containerregistry.googleapis.com",
    "firestore.googleapis.com"
  ])
  
  service            = each.value
  disable_on_destroy = false
}

# Secret Manager for API Key
resource "google_secret_manager_secret" "ark_api_key" {
  secret_id = "seedcamp-ark-api-key"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.required_apis]
}

resource "google_secret_manager_secret_version" "ark_api_key_version" {
  secret      = google_secret_manager_secret.ark_api_key.id
  secret_data = var.ark_api_key
}

# IAM binding for Cloud Run to access secrets
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.ark_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Get project data
data "google_project" "project" {
  project_id = var.project_id
}

# Firestore Database (Native mode)
resource "google_firestore_database" "seedcamp" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.required_apis]
}

# IAM binding for Cloud Run SA to access Firestore
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Cloud Run Service - API
resource "google_cloud_run_service" "seedcamp_api" {
  name     = "seedcamp-api"
  location = var.region
  
  template {
    spec {
      containers {
        image = var.api_image
        
        env {
          name  = "ARK_BASE_URL"
          value = "https://ark.ap-southeast.bytepluses.com/api/v3"
        }
        
        env {
          name  = "OUTPUT_DIR"
          value = "/tmp/output"
        }
        
        env {
          name = "ARK_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.ark_api_key.secret_id
              key  = "latest"
            }
          }
        }
        
        resources {
          limits = {
            cpu    = var.api_cpu
            memory = var.api_memory
          }
        }
      }
      
      container_concurrency = 80
      timeout_seconds       = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.api_min_instances
        "autoscaling.knative.dev/maxScale" = var.api_max_instances
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_secret_manager_secret_version.ark_api_key_version
  ]
}

# Cloud Run Service - Dashboard
resource "google_cloud_run_service" "seedcamp_dashboard" {
  name     = "seedcamp-dashboard"
  location = var.region
  
  template {
    spec {
      containers {
        image = var.dashboard_image
        
        env {
          name  = "API_URL"
          value = google_cloud_run_service.seedcamp_api.status[0].url
        }
        
        resources {
          limits = {
            cpu    = var.dashboard_cpu
            memory = var.dashboard_memory
          }
        }
      }
      
      timeout_seconds = 300
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.dashboard_min_instances
        "autoscaling.knative.dev/maxScale" = var.dashboard_max_instances
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [google_project_service.required_apis]
}

# IAM policy for public access
resource "google_cloud_run_service_iam_member" "api_public" {
  service  = google_cloud_run_service.seedcamp_api.name
  location = google_cloud_run_service.seedcamp_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_service_iam_member" "dashboard_public" {
  service  = google_cloud_run_service.seedcamp_dashboard.name
  location = google_cloud_run_service.seedcamp_dashboard.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

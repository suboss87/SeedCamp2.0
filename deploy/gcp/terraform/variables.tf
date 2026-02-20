variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for Cloud Run deployment"
  type        = string
  default     = "asia-southeast1"
}

variable "ark_api_key" {
  description = "BytePlus ModelArk API key"
  type        = string
  sensitive   = true
}

variable "api_image" {
  description = "Docker image for the API service"
  type        = string
  default     = "gcr.io/your-gcp-project-id/adcamp:latest"
}

variable "dashboard_image" {
  description = "Docker image for the dashboard service"
  type        = string
  default     = "gcr.io/your-gcp-project-id/adcamp-dashboard:latest"
}

variable "api_cpu" {
  description = "CPU allocation for API service"
  type        = string
  default     = "2"
}

variable "api_memory" {
  description = "Memory allocation for API service"
  type        = string
  default     = "2Gi"
}

variable "api_min_instances" {
  description = "Minimum number of API instances"
  type        = string
  default     = "0"
}

variable "api_max_instances" {
  description = "Maximum number of API instances"
  type        = string
  default     = "10"
}

variable "dashboard_cpu" {
  description = "CPU allocation for dashboard service"
  type        = string
  default     = "1"
}

variable "dashboard_memory" {
  description = "Memory allocation for dashboard service"
  type        = string
  default     = "512Mi"
}

variable "dashboard_min_instances" {
  description = "Minimum number of dashboard instances"
  type        = string
  default     = "0"
}

variable "dashboard_max_instances" {
  description = "Maximum number of dashboard instances"
  type        = string
  default     = "3"
}

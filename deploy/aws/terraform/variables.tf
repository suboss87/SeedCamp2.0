variable "region" {
  description = "AWS region for deployment"
  type        = string
  default     = "ap-southeast-1"
}

variable "ark_api_key" {
  description = "BytePlus ModelArk API key"
  type        = string
  sensitive   = true
}

variable "api_image" {
  description = "Docker image for API service"
  type        = string
  default     = "your-registry/seedcamp-api:latest"
}

variable "dashboard_image" {
  description = "Docker image for Dashboard service"
  type        = string
  default     = "your-registry/seedcamp-dashboard:latest"
}

variable "api_cpu" {
  description = "CPU units for API task (1024 = 1 vCPU)"
  type        = string
  default     = "1024"
}

variable "api_memory" {
  description = "Memory for API task in MB"
  type        = string
  default     = "2048"
}

variable "api_desired_count" {
  description = "Number of API tasks to run"
  type        = number
  default     = 1
}

variable "dashboard_cpu" {
  description = "CPU units for Dashboard task (256 = 0.25 vCPU)"
  type        = string
  default     = "256"
}

variable "dashboard_memory" {
  description = "Memory for Dashboard task in MB"
  type        = string
  default     = "512"
}

variable "dashboard_desired_count" {
  description = "Number of Dashboard tasks to run"
  type        = number
  default     = 1
}

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The primary region for resources"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "The primary zone for Spot VMs"
  type        = string
  default     = "europe-west1-b"
}

variable "registry_repo_name" {
  description = "Name of Artifact Registry repository"
  type        = string
  default     = "vertex-quant-registry"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "vertex-quant-backend"
}

variable "billing_account_id" {
  description = "The GCP Billing Account ID for budget alerts"
  type        = string
  default     = ""
}

variable "budget_amount_gbp" {
  description = "Monthly budget limit in GBP"
  type        = number
  default     = 200
}

variable "gcs_lifecycle_age_days" {
  description = "Number of days before temporary GCS assets are automatically deleted (0 to disable)"
  type        = number
  default     = 90
}

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.80.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ------------------------------------------------------------------------------
# GCP Services Activation
# ------------------------------------------------------------------------------
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudtasks.googleapis.com",
    "pubsub.googleapis.com",
    "aiplatform.googleapis.com",
    "billingbudgets.googleapis.com",
    "compute.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# ------------------------------------------------------------------------------
# Artifact Registry for Docker Containers
# ------------------------------------------------------------------------------
resource "google_artifact_registry_repository" "repo" {
  depends_on    = [google_project_service.services]
  location      = var.region
  repository_id = var.registry_repo_name
  description   = "Docker repository for Vertex Quant Core backend"
  format        = "DOCKER"
}

# ------------------------------------------------------------------------------
# Cloud Storage Buckets (GCS)
# ------------------------------------------------------------------------------
# GCS Bucket for audio sequences, DSP assets, and logs
resource "google_storage_bucket" "assets_bucket" {
  depends_on                  = [google_project_service.services]
  name                        = "${var.project_id}-vertex-quant-assets"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  dynamic "lifecycle_rule" {
    for_each = var.gcs_lifecycle_age_days > 0 ? [1] : []
    content {
      condition {
        age = var.gcs_lifecycle_age_days
      }
      action {
        type = "Delete"
      }
    }
  }
}

# ------------------------------------------------------------------------------
# Google Cloud Tasks Queue (Rate-Limited Background Jobs)
# ------------------------------------------------------------------------------
resource "google_cloud_tasks_queue" "jobs_queue" {
  depends_on = [google_project_service.services]
  name       = "vertex-quant-jobs-queue"
  location   = var.region

  rate_limits {
    max_concurrent_dispatches = 10
    max_dispatches_per_second = 2.0
  }

  retry_config {
    max_attempts       = 5
    max_retry_duration = "3600s"
    max_backoff        = "300s"
    min_backoff        = "5s"
    max_doublings      = 5
  }
}

# ------------------------------------------------------------------------------
# Google Pub/Sub (Event Streaming & Telemetry)
# ------------------------------------------------------------------------------
resource "google_pubsub_topic" "telemetry_topic" {
  depends_on = [google_project_service.services]
  name       = "vertex-quant-telemetry"
}

resource "google_pubsub_subscription" "telemetry_sub" {
  name  = "vertex-quant-telemetry-sub"
  topic = google_pubsub_topic.telemetry_topic.name

  # Retain unacknowledged messages for 7 days
  message_retention_duration = "604800s"
  retain_acked_messages      = false
  ack_deadline_seconds       = 20
}

# ------------------------------------------------------------------------------
# Google Cloud Run (Autoscaling Web Server & Main API)
# ------------------------------------------------------------------------------
# Dummy configuration to initialize Cloud Run. Cloud Build overrides this on deploy.
resource "google_cloud_run_service" "backend_service" {
  depends_on = [google_project_service.services, google_artifact_registry_repository.repo]
  name       = var.service_name
  location   = var.region

  template {
    spec {
      containers {
        image = "us-docker.pkg.dev/cloudrun/container/hello:latest"
        ports {
          container_port = 8001
        }
        resources {
          limits = {
            memory = "512Mi"
            cpu    = "1000m"
          }
        }
        # Inject standard GCP metadata environments
        env {
          name  = "GCP_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GCS_BUCKET_NAME"
          value = google_storage_bucket.assets_bucket.name
        }
        env {
          name  = "CLOUD_TASKS_QUEUE"
          value = google_cloud_tasks_queue.jobs_queue.id
        }
      }
    }
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0" # Scales down to 0 to save credits!
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Allow unauthenticated (public) traffic to the main Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend_service.name
  location = google_cloud_run_service.backend_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ------------------------------------------------------------------------------
# GCE Spot VM (Cost-Optimized Heavy Compute Engine for Audio DSP)
# ------------------------------------------------------------------------------
resource "google_compute_instance" "spot_worker" {
  depends_on   = [google_project_service.services]
  name         = "vertex-quant-dsp-spot-worker"
  machine_type = "e2-medium" # Balanced price/performance
  zone         = var.zone

  scheduling {
    preemptible                 = true # Use spot VM pricing (saves up to 80% credits!)
    automatic_restart           = false
    provisioning_model          = "SPOT"
    instance_termination_action = "TERMINATE"
  }

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20 # 20GB disk is sufficient
    }
  }

  network_interface {
    network = "default"
    access_config {
      # Include Ephemeral external IP to allow outbound updates
    }
  }

  metadata = {
    startup-script = <<-EOT
      #!/bin/bash
      apt-get update
      apt-get install -y python3-pip git curl
      echo "Vertex Quant Heavy DSP Spot Engine Initialized"
    EOT
  }

  service_account {
    scopes = ["cloud-platform"]
  }
}

# ------------------------------------------------------------------------------
# Google Cloud Billing Budgets (Automatic Credit Protection)
# ------------------------------------------------------------------------------
resource "google_billing_budget" "credit_protection_budget" {
  depends_on      = [google_project_service.services]
  count           = var.billing_account_id != "" ? 1 : 0
  billing_account = var.billing_account_id
  display_name    = "Vertex Quant GCP Credit Budget"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "GBP"
      units         = var.budget_amount_gbp
    }
  }

  threshold_rules {
    threshold_percent = 0.5
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 0.75
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 0.9
    spend_basis       = "CURRENT_SPEND"
  }
  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    # Send pubsub alerts so our backend can react by turning off compute!
    pubsub_topic                     = google_pubsub_topic.telemetry_topic.id
    schema_version                   = "1.0"
    disable_default_iam_recipients   = false
  }
}

# ------------------------------------------------------------------------------
# Terraform Outputs
# ------------------------------------------------------------------------------
output "cloud_run_url" {
  value       = google_cloud_run_service.backend_service.status[0].url
  description = "The URL of the deployed Cloud Run service"
}

output "gcs_bucket_name" {
  value       = google_storage_bucket.assets_bucket.name
  description = "Google Cloud Storage bucket for digital asset files"
}

output "tasks_queue_id" {
  value       = google_cloud_tasks_queue.jobs_queue.id
  description = "Google Cloud Tasks Queue resource ID"
}

output "pubsub_topic_id" {
  value       = google_pubsub_topic.telemetry_topic.id
  description = "Pub/Sub Telemetry and Billing alerts topic ID"
}

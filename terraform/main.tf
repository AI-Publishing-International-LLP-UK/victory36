# Victory36 Diamond SAO Production Infrastructure
# Classification: DIAMOND SAO ONLY
# Multi-region deployment: MOCOA, MOCORIX, MOCORIX2

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.84"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID for ASOOS Production"
  type        = string
  default     = "api-for-warp-drive"
}

variable "region" {
  description = "Target region for deployment"
  type        = string
  default     = "us-west1"
}

variable "environment" {
  description = "Environment (production only for Victory36)"
  type        = string
  default     = "production"
}

variable "max_agents" {
  description = "Maximum number of AI agents per region"
  type        = number
  default     = 6666667 # 20M / 3 regions
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Data sources
data "google_client_config" "default" {}

# Determine zone based on region and deployment type
locals {
  deployment_type = "MOCOA" # Simplified for initial deployment
  zone            = "us-west1-b"
  cluster_name    = "victory36-mocoa"
}

# API Services
resource "google_project_service" "compute_api" {
  project = var.project_id
  service = "compute.googleapis.com"
}

resource "google_project_service" "container_api" {
  project = var.project_id
  service = "container.googleapis.com"
}

resource "google_project_service" "monitoring_api" {
  project = var.project_id
  service = "monitoring.googleapis.com"
}

resource "google_project_service" "logging_api" {
  project = var.project_id
  service = "logging.googleapis.com"
}

# VPC Network
resource "google_compute_network" "victory36_network" {
  name                    = "victory36-network"
  auto_create_subnetworks = false
  mtu                     = 1460

  depends_on = [
    google_project_service.compute_api,
    google_project_service.container_api
  ]
}

# Subnet for MOCOA region
resource "google_compute_subnetwork" "victory36_subnet" {
  name          = "victory36-subnet-mocoa"
  ip_cidr_range = "10.1.0.0/16"
  region        = var.region
  network       = google_compute_network.victory36_network.name

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.4.0.0/14"
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.16.0.0/20"
  }
}

# Cloud NAT for outbound connectivity
resource "google_compute_router" "victory36_router" {
  name    = "victory36-router-mocoa"
  region  = var.region
  network = google_compute_network.victory36_network.id
}

resource "google_compute_router_nat" "victory36_nat" {
  name                               = "victory36-nat-mocoa"
  router                             = google_compute_router.victory36_router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# GKE Autopilot Cluster for MOCOA
resource "google_container_cluster" "victory36_cluster" {
  name     = local.cluster_name
  location = var.region

  # Use autopilot for simplicity and security
  enable_autopilot = true

  # Network configuration
  network    = google_compute_network.victory36_network.name
  subnetwork = google_compute_subnetwork.victory36_subnet.name

  # IP allocation policy
  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  # Workload Identity
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Network policy
  network_policy {
    enabled = true
  }

  # Logging and monitoring
  logging_service    = "logging.googleapis.com/kubernetes"
  monitoring_service = "monitoring.googleapis.com/kubernetes"

  # Maintenance window
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00" # 3 AM UTC
    }
  }

  # Resource labels
  resource_labels = {
    environment     = var.environment
    component       = "victory36"
    deployment_type = lower(local.deployment_type)
    classification  = "diamond-sao"
    managed_by      = "terraform"
  }

  depends_on = [
    google_project_service.container_api,
    google_project_service.compute_api,
  ]
}

# Service Account for Victory36 workloads
resource "google_service_account" "victory36_sa" {
  account_id   = "victory36-mocoa"
  display_name = "Victory36 MOCOA Service Account"
  description  = "Diamond SAO service account for Victory36 connection pool manager"
}

# IAM binding for service account
resource "google_project_iam_member" "victory36_sa_roles" {
  for_each = toset([
    "roles/monitoring.metricWriter",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent"
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.victory36_sa.email}"
}

# Workload Identity binding
resource "google_service_account_iam_member" "victory36_workload_identity" {
  service_account_id = google_service_account.victory36_sa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[victory36/victory36-connection-pool]"
}

# Outputs
output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.victory36_cluster.name
}

output "cluster_endpoint" {
  description = "Cluster endpoint"
  value       = google_container_cluster.victory36_cluster.endpoint
  sensitive   = true
}

output "region" {
  description = "Deployment region"
  value       = var.region
}

output "deployment_type" {
  description = "Victory36 deployment type"
  value       = local.deployment_type
}

output "service_account_email" {
  description = "Victory36 service account email"
  value       = google_service_account.victory36_sa.email
}

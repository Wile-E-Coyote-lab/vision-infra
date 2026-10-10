terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
  # Partial config: bucket/prefix are supplied by `terraform init -backend-config=...`
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

locals {
  apis = [
    "compute.googleapis.com",
    "iap.googleapis.com",
    "oslogin.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]
  operator_roles = var.operator_member == "" ? [] : [
    "roles/iap.tunnelResourceAccessor",
    "roles/compute.osAdminLogin",
    "roles/compute.viewer",
  ]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.key
  disable_on_destroy = false
}

# ---------- Network: private VPC, IAP-only ingress, NAT for egress ----------
resource "google_compute_network" "vpc" {
  name                    = "android-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

resource "google_compute_subnetwork" "subnet" {
  name                     = "android-subnet"
  region                   = var.region
  network                  = google_compute_network.vpc.id
  ip_cidr_range            = "10.10.0.0/24"
  private_ip_google_access = true
}

resource "google_compute_firewall" "allow_iap" {
  name          = "allow-iap-ssh-adb"
  network       = google_compute_network.vpc.name
  direction     = "INGRESS"
  source_ranges = ["35.235.240.0/20"] # Google IAP TCP forwarding range
  target_tags   = ["android-host"]

  allow {
    protocol = "tcp"
    ports    = ["22", "5555"]
  }
}

resource "google_compute_router" "router" {
  name    = "android-router"
  region  = var.region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "android-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# ---------- VM identity ----------
resource "google_service_account" "vm" {
  account_id   = "android-vm-sa"
  display_name = "Android host VM"
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "vm_roles" {
  for_each = toset(["roles/logging.logWriter", "roles/monitoring.metricWriter"])
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.vm.email}"
}

# ---------- Android host (Redroid in Docker) ----------
resource "google_compute_instance" "android_host" {
  name                      = var.instance_name
  machine_type              = var.machine_type
  zone                      = var.zone
  tags                      = ["android-host"]
  allow_stopping_for_update = true

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.disk_gb
      type  = "pd-balanced"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
    # no access_config: no public IP; reach it via IAP
  }

  shielded_instance_config {
    enable_secure_boot          = false
    enable_vtpm                 = true
    enable_integrity_monitoring = true
  }

  service_account {
    email  = google_service_account.vm.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  metadata_startup_script = templatefile("${path.module}/startup.sh.tpl", {
    redroid_image = var.redroid_image
  })

  depends_on = [
    google_project_iam_member.vm_roles,
    google_compute_router_nat.nat,
  ]
}

# ---------- Human operator access (IAP tunnel + OS Login) ----------
resource "google_project_iam_member" "operator" {
  for_each = toset(local.operator_roles)
  project  = var.project_id
  role     = each.key
  member   = var.operator_member
}

resource "google_service_account_iam_member" "operator_sa_user" {
  count              = var.operator_member == "" ? 0 : 1
  service_account_id = google_service_account.vm.name
  role               = "roles/iam.serviceAccountUser"
  member             = var.operator_member
}

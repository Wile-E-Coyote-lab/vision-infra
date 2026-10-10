variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "instance_name" {
  type    = string
  default = "android-host"
}

variable "machine_type" {
  type    = string
  default = "n2-standard-4"
}

variable "disk_gb" {
  type    = number
  default = 60
}

variable "operator_member" {
  type        = string
  default     = ""
  description = "IAM member allowed to tunnel/SSH, e.g. user:you@gmail.com"
}

variable "redroid_image" {
  type    = string
  default = "redroid/redroid:13.0.0-latest"
}

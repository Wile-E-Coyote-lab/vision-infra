output "instance_name" {
  value = google_compute_instance.android_host.name
}

output "zone" {
  value = var.zone
}

output "internal_ip" {
  value = google_compute_instance.android_host.network_interface[0].network_ip
}

output "connect_hint" {
  value = "./termux/connect.sh  (IAP tunnel to ${var.instance_name}:5555, then adb connect localhost:5555)"
}

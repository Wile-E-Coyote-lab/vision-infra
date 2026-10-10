#!/usr/bin/env bash
# Idempotent: runs on every boot. Log: /var/log/android-setup.log
set -euo pipefail
exec > >(tee -a /var/log/android-setup.log) 2>&1
export DEBIAN_FRONTEND=noninteractive
echo "== android host setup $(date -u) =="

if ! command -v docker >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y docker.io android-tools-adb
fi

# binder_linux ships in linux-modules-extra on Ubuntu
if ! dpkg -s "linux-modules-extra-$(uname -r)" >/dev/null 2>&1; then
  apt-get update -y
  apt-get install -y "linux-modules-extra-$(uname -r)" || echo "WARN: no modules-extra package for running kernel"
fi

cat >/etc/modprobe.d/binder.conf <<'CONF'
options binder_linux devices=binder,hwbinder,vndbinder
CONF
printf 'binder_linux\n' >/etc/modules-load.d/android.conf

modprobe binder_linux devices=binder,hwbinder,vndbinder || true
modprobe ashmem_linux 2>/dev/null || true   # absent on newer kernels; Redroid 13 does not need it

if ! lsmod | grep -q binder_linux; then
  echo "ERROR: binder_linux not loaded. Try: sudo reboot (kernel/modules mismatch)"
  exit 1
fi

systemctl enable --now docker
mkdir -p /var/lib/redroid-data

if ! docker ps -a --format '{{.Names}}' | grep -qx redroid; then
  docker run -d --name redroid --privileged --restart unless-stopped \
    -v /var/lib/redroid-data:/data \
    -p 5555:5555 \
    ${redroid_image} \
    androidboot.redroid_gpu_mode=guest \
    androidboot.redroid_width=720 \
    androidboot.redroid_height=1280 \
    androidboot.redroid_dpi=320
fi
docker start redroid >/dev/null 2>&1 || true
echo "== setup complete =="

#!/usr/bin/env bash
# Runs ON the VM (as root). Idempotent: pulls the image and recreates the container.
set -euo pipefail
IMAGE="${REDROID_IMAGE:-redroid/redroid:13.0.0-latest}"
mkdir -p /var/lib/redroid-data
docker pull "$IMAGE"
docker rm -f redroid 2>/dev/null || true
docker run -d --name redroid --privileged --restart unless-stopped \
  -v /var/lib/redroid-data:/data -p 5555:5555 "$IMAGE" \
  androidboot.redroid_gpu_mode=guest \
  androidboot.redroid_width=720 androidboot.redroid_height=1280 androidboot.redroid_dpi=320
docker ps --filter name=redroid --format 'redroid: {{.Status}}'

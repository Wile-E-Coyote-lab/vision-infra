#!/usr/bin/env bash
# Open IAP tunnel to the VM's ADB port and adb connect. Needs gcloud + adb in PATH
# (run inside proot-distro Debian: apt install android-tools-adb).
# Usage: PROJECT_ID=my-proj [ZONE=us-central1-a] [INSTANCE=android-host] ./termux/connect.sh
set -euo pipefail
: "${PROJECT_ID:?set PROJECT_ID}"
ZONE="${ZONE:-us-central1-a}"; INSTANCE="${INSTANCE:-android-host}"; PORT="${PORT:-5555}"

gcloud compute start-iap-tunnel "$INSTANCE" 5555 --local-host-port="localhost:$PORT" \
  --zone "$ZONE" --project "$PROJECT_ID" &
TUNNEL=$!
trap 'adb disconnect "localhost:$PORT" >/dev/null 2>&1 || true; kill $TUNNEL 2>/dev/null || true' EXIT
sleep 6
adb connect "localhost:$PORT"
adb devices
echo "Connected. Ctrl-C to close the tunnel."
wait $TUNNEL

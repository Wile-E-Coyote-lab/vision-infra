#!/usr/bin/env bash
set -euo pipefail

JOB_ID="${1:?Pass JOB_ID as argument 1}"
API_URL="${LTX_API_URL:-https://api.ltx.io/v2/text-to-video}"
: "${LTXV_API_KEY:?Set LTXV_API_KEY in the shell}"

VIDEO_URL=""
for attempt in $(seq 1 120); do
  sleep 5
  RESP=$(curl -sf --max-time 20 \
    "${API_URL}/${JOB_ID}" \
    -H "Authorization: Bearer ${LTXV_API_KEY}") || continue

  PARSED=$(printf '%s\n' "$RESP" | python3 -c '
import json, sys
d = json.load(sys.stdin)
status = d.get("status", "")
res = d.get("result") if isinstance(d.get("result"), dict) else {}
url = res.get("video_url") or d.get("video_url") or ""
print(f"{status}\t{url}")
')

  STATE="${PARSED%%	*}"
  VIDEO_URL="${PARSED#*	}"
  echo "[${attempt}] job=${JOB_ID} state=${STATE}" >&2

  case "$STATE" in
    completed)
      [[ -n "$VIDEO_URL" ]] && break
      ;;
    failed)
      echo "Job ${JOB_ID} failed: $RESP" >&2
      exit 1
      ;;
  esac
done

[[ -n "$VIDEO_URL" ]] || { echo "Timed out waiting for job ${JOB_ID}" >&2; exit 1; }
printf '%s\n' "$VIDEO_URL"

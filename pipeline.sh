#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

PROMPT="${1:?Usage: ./pipeline.sh 'your scene prompt' [duration_secs]}"
DURATION="${2:-8}"
LTX_RES="${LTX_RES:-1280x720}"
LTX_MODEL="${LTX_MODEL:-ltx-2-5-pro}"
LTX_API_URL="${LTX_API_URL:-https://api.ltx.io/v2/text-to-video}"

: "${LTXV_API_KEY:?Set LTXV_API_KEY in the shell before running}"

PAYLOAD_JSON="$(mktemp /tmp/ltx-payload-XXXXXXXX.json)"
cleanup() { rm -f "$PAYLOAD_JSON"; }
trap cleanup EXIT

python3 - "$PROMPT" "$LTX_MODEL" "$LTX_RES" "$DURATION" "$PAYLOAD_JSON" << 'PYEOF'
import json, re, sys

prompt_text, model_name, res, raw_dur, out_path = sys.argv[1:6]
m = re.search(r"\d+", raw_dur or "")
dur = max(1, min(int(m.group(0)) if m else 8, 60))

with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({
        "prompt": prompt_text,
        "model": model_name,
        "resolution": res,
        "duration": dur,
    }, fh, ensure_ascii=False)
PYEOF

echo "[*] Transmitting screened prompt to LTX V2 API endpoint..."
echo "[*] Target URL: ${LTX_API_URL} (model=${LTX_MODEL}, res=${LTX_RES})"

RESPONSE=$(curl -sS -X POST "$LTX_API_URL" \
  -H "Authorization: Bearer ${LTXV_API_KEY}" \
  -H "Content-Type: application/json" \
  --data-binary "@${PAYLOAD_JSON}")

echo "[*] API Response Raw: $RESPONSE"

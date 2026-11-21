#!/usr/bin/env bash
set -euo pipefail

: "${LTXV_API_KEY:?Set LTXV_API_KEY in the shell}"
API_URL="${LTX_API_URL:-https://api.ltx.io/v2/text-to-video}"
PROMPT="${1:-Equirectangular 360 panorama video, 2:1 aspect ratio, seamless wraparound}"
RES="${LTX_RES:-1280x720}"
DUR="${DURATION:-6}"

CANDIDATE_MODELS=("ltx-2-3-fast" "ltx-2-3-pro" "ltx-2-5-fast" "ltx-2-5-pro")

SELECTED_MODEL=""
SELECTED_JOB=""

for MODEL in "${CANDIDATE_MODELS[@]}"; do
  PAYLOAD="$(mktemp /tmp/ltx-probe-XXXXXXXX.json)"
  python3 - "$PROMPT" "$MODEL" "$RES" "$DUR" "$PAYLOAD" << 'PYEOF'
import json, sys
p, m, r, d, out = sys.argv[1:6]
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"prompt": p, "model": m, "resolution": r, "duration": int(d)}, fh, ensure_ascii=False)
PYEOF

  HTTP_CODE=$(curl -sS --max-time 25 -o /tmp/ltx-resp.body -w "%{http_code}" \
    -X POST "$API_URL" \
    -H "Authorization: Bearer ${LTXV_API_KEY}" \
    -H "Content-Type: application/json" \
    --data-binary "@${PAYLOAD}" || echo "000")
  rm -f "$PAYLOAD"
  RESP=$(cat /tmp/ltx-resp.body 2>/dev/null || true)
  rm -f /tmp/ltx-resp.body

  CHECK=$(printf '%s' "$RESP" | python3 - "$HTTP_CODE" << 'PYEOF'
import json, sys
code = sys.argv[1]
raw = sys.stdin.read().strip()
if not raw:
    print(f"REJECTED\tempty_response (HTTP {code})")
    sys.exit(0)
try:
    d = json.loads(raw)
except Exception as exc:
    snippet = raw[:120].replace("\n", " ")
    print(f"REJECTED\tnon_json (HTTP {code}): {snippet} ({exc})")
    sys.exit(0)

if isinstance(d, dict) and "id" in d:
    print("ACCEPTED\t" + str(d["id"]))
else:
    err = d.get("error", {}) if isinstance(d, dict) and isinstance(d.get("error"), dict) else {}
    etype = err.get("type", f"http_{code}")
    emsg = err.get("message", raw[:160])
    print(f"REJECTED\t{etype}: {emsg}")
PYEOF
)
  STATUS_TAG="${CHECK%%	*}"
  DETAIL="${CHECK#*	}"

  if [[ "$STATUS_TAG" == "ACCEPTED" ]]; then
    sleep 3
    POLL=$(curl -sS --max-time 20 "${API_URL}/${DETAIL}" \
      -H "Authorization: Bearer ${LTXV_API_KEY}" || true)
    BILLING_ERR=$(printf '%s' "$POLL" | python3 - << 'PYEOF'
import json, sys
raw = sys.stdin.read().strip()
if not raw:
    sys.exit(0)
try:
    d = json.loads(raw)
except Exception:
    sys.exit(0)
if isinstance(d, dict) and d.get("status") == "failed":
    err = d.get("error", {}) if isinstance(d.get("error"), dict) else {}
    etype = err.get("type", "failed")
    emsg = err.get("message", "")
    print(f"{etype}: {emsg}")
PYEOF
)
    if [[ -z "$BILLING_ERR" ]]; then
      SELECTED_MODEL="$MODEL"
      SELECTED_JOB="$DETAIL"
      echo "CAPABILITY_OK model=${SELECTED_MODEL} job_id=${SELECTED_JOB}"
      break
    else
      echo "CAPABILITY_SKIP model=${MODEL} reason=${BILLING_ERR}" >&2
    fi
  else
    echo "CAPABILITY_SKIP model=${MODEL} reason=${DETAIL}" >&2
  fi
done

if [[ -z "$SELECTED_MODEL" ]]; then
  echo "NO_FUNDED_MODEL_AVAILABLE — falling back to zero-cost local equirectangular generator" >&2
  exit 2
fi

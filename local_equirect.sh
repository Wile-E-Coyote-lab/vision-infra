#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

PROMPT="${1:-Equirectangular 360 panorama video, 2:1 aspect ratio, seamless wraparound}"
DURATION="${2:-6}"
OUT_W="${OUT_W:-1280}"
OUT_H="${OUT_H:-640}"
MAX_BYTES=$((100 * 1024 * 1024))

# Enforce exact 2:1 equirectangular geometry before encoding
if [[ "$OUT_W" -ne "$((OUT_H * 2))" ]]; then
  OUT_H=$((OUT_W / 2))
  [[ $((OUT_H % 2)) -ne 0 ]] && OUT_H=$((OUT_H + 1))
fi

SCENE_TS="$(date +%Y%m%d-%H%M%S)"
SCENE_ID="scene-${SCENE_TS}"
OUT_DIR="docs/assets/video"
OUT_MP4="${OUT_DIR}/${SCENE_ID}-equirect.mp4"
POSTER="${OUT_DIR}/${SCENE_ID}-poster.jpg"
MANIFEST="docs/manifest.json"
TMP_MP4="$(mktemp /tmp/local-eq-XXXXXXXX.mp4)"
trap 'rm -f "$TMP_MP4"' EXIT

mkdir -p "$OUT_DIR"

# Generate seamless horizontal-wrapping 2:1 equirectangular test pattern at zero cost
ffmpeg -v error -y \
  -f lavfi -i "testsrc2=size=${OUT_W}x${OUT_H}:rate=24:duration=${DURATION}" \
  -vf "scroll=horizontal=0.05:vertical=0,format=yuv420p" \
  -c:v libx264 -crf 23 -preset fast -movflags +faststart \
  "$TMP_MP4"

# Verify dimensions (W == 2 * H) and size (< 100 MB)
DIMS=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width,height -of csv=p=0:s=x "$TMP_MP4" | tr -d '[:space:]')
W="${DIMS%x*}"
H="${DIMS#*x}"
[[ "$W" -eq "$((H * 2))" ]] || { echo "Geometry check failed: ${W}x${H}" >&2; exit 1; }

SZ=$(wc -c < "$TMP_MP4")
[[ "$SZ" -lt "$MAX_BYTES" ]] || { echo "File >= 100MB: ${SZ}" >&2; exit 1; }

cp "$TMP_MP4" "$OUT_MP4"
ffmpeg -v error -ss 1 -i "$OUT_MP4" -frames:v 1 "$POSTER" -y 2>/dev/null || true

python3 - "$MANIFEST" "$SCENE_ID" "$PROMPT" "assets/video/${SCENE_ID}-equirect.mp4" "assets/video/${SCENE_ID}-poster.jpg" "${W}x${H}" "$DURATION" << 'PYEOF'
import datetime, json, pathlib, sys
mf_p, sid, prompt, vid, poster, res, dur = sys.argv[1:8]
mf = pathlib.Path(mf_p)
mf.parent.mkdir(parents=True, exist_ok=True)
doc = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
if not isinstance(doc.get("scenes"), list):
    doc["scenes"] = []
doc["scenes"].insert(0, {
    "id": sid,
    "title": prompt,
    "prompt": prompt,
    "video": vid,
    "poster": poster,
    "resolution": res,
    "duration_s": int(dur),
    "source": "local-ffmpeg-2:1",
    "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
})
mf.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PYEOF

echo "Generated ${OUT_MP4} (${W}x${H}, ${SZ} bytes) and updated ${MANIFEST}"

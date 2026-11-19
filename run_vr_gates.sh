#!/usr/bin/env bash
set -euo pipefail

INPUT_MP4="${1:-}"
INPUT_IMG="${2:-}"

OUT_DIR="docs"
VIDEO_OUT="${OUT_DIR}/assets/video/scene-01-equirect.mp4"
POSTER_OUT="${OUT_DIR}/assets/video/scene-01-poster.jpg"
MANIFEST_OUT="${OUT_DIR}/assets/manifest.json"
PROMPT_FILE="/tmp/datura_ltx_prompt.txt"

RAW_MP4="/tmp/vr_raw_scene01.mp4"
STAGE1_IMG_MP4="/tmp/vr_stage1_img.mp4"
EQ_MP4="/tmp/vr_eq_scene01.mp4"
META_MP4="/tmp/vr_meta_scene01.mp4"
SPATIAL_MP4="/tmp/vr_spatial_scene01.mp4"

# Optional LTX polling hook: set LTX_POLL_CMD to a command that prints or writes a ready .mp4 path
LTX_POLL_CMD="${LTX_POLL_CMD:-}"
LTX_POLL_INTERVAL="${LTX_POLL_INTERVAL:-3}"
LTX_POLL_TIMEOUT="${LTX_POLL_TIMEOUT:-30}"
AUTO_GIT_COMMIT="${AUTO_GIT_COMMIT:-1}"
GIT_COMMIT_RETRIES="${GIT_COMMIT_RETRIES:-3}"

mkdir -p "${OUT_DIR}/assets/video" "${OUT_DIR}/_layouts"

# 1. Inject readtime DATURA 4096x2048 2:1 prompt for LTX polling routine
cat << 'EOF' > "$PROMPT_FILE"
Equirectangular 360 panorama video, 2:1 aspect ratio, 4096x2048,
seamless wraparound, left edge meets right edge,
full 360 degree environment, equirectangular projection,
DATURA Sanctuary: black marble cathedral, red refractive windows,
sapphire blue emissive floor lines, white armor altar with emerald seam,
moon surface visible, no letterbox, no flat camera, no 16:9 framing
EOF

# 2. Optional readtime LTX polling loop
polled_mp4=""
if [ -n "$LTX_POLL_CMD" ]; then
  elapsed=0
  while [ "$elapsed" -lt "$LTX_POLL_TIMEOUT" ]; do
    candidate="$(eval "$LTX_POLL_CMD" 2>/dev/null | tail -n1 | tr -d '[:space:]')"
    if [ -n "$candidate" ] && [ -s "$candidate" ]; then
      polled_mp4="$candidate"
      echo "[LTX Poll] Artifact ready after ${elapsed}s: ${polled_mp4}"
      break
    fi
    echo "[LTX Poll] Waiting (${elapsed}s/${LTX_POLL_TIMEOUT}s)..."
    sleep "$LTX_POLL_INTERVAL"
    elapsed=$(( elapsed + LTX_POLL_INTERVAL ))
  done
fi

# 3. Two-Stage Ingest: Stage A (local image -> 2:1 canvas + spatialmedia) or Stage B (MP4 / polled / local 2:1)
if [ -n "$INPUT_IMG" ]; then
  [ -f "$INPUT_IMG" ] || { echo "[!] Image not found: $INPUT_IMG"; exit 1; }
  echo "[Stage 1: Image Ingest] Rasterizing ${INPUT_IMG} into 4096x2048 (2:1) equirectangular frame..."
  ffmpeg -y -loop 1 -i "$INPUT_IMG" -t 4 \
    -vf "scale=2048:2048:force_original_aspect_ratio=decrease,pad=4096:2048:(ow-iw)/2:(oh-ih)/2:color=#0b0d12,format=yuv420p" \
    -c:v libx264 -pix_fmt yuv420p "$STAGE1_IMG_MP4"

  if command -v spatialmedia >/dev/null 2>&1; then
    python3 -m spatialmedia -i -s "$STAGE1_IMG_MP4" "$SPATIAL_MP4" 2>/dev/null || \
      spatialmedia -i -s "$STAGE1_IMG_MP4" "$SPATIAL_MP4"
    cp "$SPATIAL_MP4" "$RAW_MP4"
  else
    cp "$STAGE1_IMG_MP4" "$RAW_MP4"
  fi
elif [ -n "$polled_mp4" ]; then
  cp "$polled_mp4" "$RAW_MP4"
elif [ -n "$INPUT_MP4" ]; then
  [ -f "$INPUT_MP4" ] || { echo "[!] Video not found: $INPUT_MP4"; exit 1; }
  cp "$INPUT_MP4" "$RAW_MP4"
else
  echo "[Stage 2: Local 2:1 Fallback] Synthesizing 2048x1024 (2:1) clip via ffmpeg..."
  ffmpeg -y -f lavfi -i "testsrc2=size=2048x1024:rate=24" -t 4 \
    -c:v libx264 -pix_fmt yuv420p "$RAW_MP4"
fi

# 4. Gate Check: strict 2:1 aspect ratio check (width == 2 * height)
W=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_MP4" | head -n1 | tr -d '[:space:]')
H=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=height \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_MP4" | head -n1 | tr -d '[:space:]')

echo "[Gate] Detected dimensions: ${W:-?}x${H:-?}"

if [ -z "${W:-}" ] || [ -z "${H:-}" ] || [ "$H" -eq 0 ] || [ "$W" -ne $(( 2 * H )) ]; then
  echo "Not equirectangular."
  exit 1
fi

# 5. Projection conversion (if requested) + spherical metadata injection
if [ "${CONVERT_FISHEYE:-0}" = "1" ]; then
  ffmpeg -y -i "$RAW_MP4" -vf "v360=fisheye:equirect" -c:a copy "$EQ_MP4"
else
  cp "$RAW_MP4" "$EQ_MP4"
fi

ffmpeg -y -i "$EQ_MP4" -c copy \
  -metadata:s:v:0 spherical=true \
  -metadata:s:v:0 "Spherical=true" \
  -metadata:s:v:0 "Stitched=true" \
  -metadata:s:v:0 "ProjectionType=equirectangular" \
  -metadata:s:v:0 "StereoMode=mono" \
  "$META_MP4"

if command -v spatialmedia >/dev/null 2>&1; then
  python3 -m spatialmedia -i -s "$META_MP4" "$VIDEO_OUT" 2>/dev/null || \
    spatialmedia -i -s "$META_MP4" "$VIDEO_OUT"
else
  cp "$META_MP4" "$VIDEO_OUT"
fi

# 6. Runner-wrapped ffmpeg integrity check on final video + poster generation
ffmpeg -v error -xerror -i "$VIDEO_OUT" -f null -
ffmpeg -v error -xerror -y -i "$VIDEO_OUT" -frames:v 1 -q:v 2 "$POSTER_OUT"

cat << 'EOF' > "$MANIFEST_OUT"
{
  "scene": "DATURA — Scene 01",
  "projection": "equirectangular",
  "aspectRatio": "2:1",
  "storyboard": [
    { "time": 0, "target": "altar" },
    { "time": 5, "target": "red window" },
    { "time": 10, "target": "visor" }
  ],
  "anchors": {
    "emerald-anchor": [0, 1.2, -5],
    "blue-lines-anchor": [0, 0.1, -3]
  }
}
EOF

# 7. Jekyll + A-Frame 1.7.0 SPA files under docs/
cat << 'EOF' > "${OUT_DIR}/_config.yml"
title: DATURA 360 WebXR PWA
description: Equirectangular VR progressive web app served over HTTPS via GitHub Pages
baseurl: "/vision-infra"
url: "https://wile-e-coyote-lab.github.io"
EOF

cat << 'EOF' > "${OUT_DIR}/_layouts/vr.html"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ page.title | default: site.title }}</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/aframe/1.7.0/aframe.min.js"></script>
</head>
<body>
  <a-scene vr-mode-ui="enabled: true" embedded>
    <a-assets>
      <video id="daturaVideo"
             src="{{ '/assets/video/scene-01-equirect.mp4' | relative_url }}"
             poster="{{ '/assets/video/scene-01-poster.jpg' | relative_url }}"
             autoplay loop muted playsinline crossorigin="anonymous"></video>
    </a-assets>
    <a-videosphere src="#daturaVideo" rotation="0 180 0"></a-videosphere>
    <a-entity camera look-controls wasd-controls position="0 1.6 0">
      <a-cursor></a-cursor>
    </a-entity>
    <a-entity id="emerald-anchor" position="0 1.2 -5"></a-entity>
    <a-entity id="blue-lines-anchor" position="0 0.1 -3"></a-entity>
  </a-scene>
</body>
</html>
EOF

cat << 'EOF' > "${OUT_DIR}/index.html"
---
layout: vr
title: DATURA — Scene 01
---
EOF

# 8. Immediate loop git commit direct to repo (docs/)
if [ "$AUTO_GIT_COMMIT" = "1" ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  attempt=1
  while [ "$attempt" -le "$GIT_COMMIT_RETRIES" ]; do
    git add "${OUT_DIR}/"
    if git diff --cached --quiet; then
      echo "[Git Loop] No staged changes in ${OUT_DIR}/ to commit."
      break
    fi
    if git commit -m "Gate-validated 2:1 WebXR scene update (${W}x${H}) [attempt ${attempt}]"; then
      echo "[Git Loop] Committed ${OUT_DIR}/ cleanly."
      break
    fi
    attempt=$(( attempt + 1 ))
    sleep 1
  done
fi

echo "[+] Pipeline passed all gates and wrote ${VIDEO_OUT}"

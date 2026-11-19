#!/usr/bin/env bash
set -euo pipefail

INPUT_MP4="${1:-}"
RAW_MP4="/tmp/free_raw_scene01.mp4"
EQ_MP4="/tmp/free_eq_scene01.mp4"
OUT_DIR="docs"
VIDEO_OUT="${OUT_DIR}/assets/video/scene-01-equirect.mp4"
POSTER_OUT="${OUT_DIR}/assets/video/scene-01-poster.jpg"
MANIFEST_OUT="${OUT_DIR}/assets/manifest.json"

mkdir -p "${OUT_DIR}/assets/video" "${OUT_DIR}/_layouts"

# 1. Free Source Stage: use supplied MP4 or synthesize a free 2048x1024 (2:1) test video
if [ -n "$INPUT_MP4" ]; then
  if [ ! -f "$INPUT_MP4" ]; then
    echo "[!] Input file not found: $INPUT_MP4"
    exit 1
  fi
  cp "$INPUT_MP4" "$RAW_MP4"
else
  echo "[Free Source] Generating local 2048x1024 (2:1) test video via ffmpeg..."
  ffmpeg -y -f lavfi -i "testsrc2=size=2048x1024:rate=24" -t 6 \
    -c:v libx264 -pix_fmt yuv420p "$RAW_MP4"
fi

# 2. Gate 2: Parse W and H cleanly via ffprobe default writer (no CSV option error)
W=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=width \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_MP4" | head -n1 | tr -d '[:space:]')

H=$(ffprobe -v error -select_streams v:0 \
  -show_entries stream=height \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_MP4" | head -n1 | tr -d '[:space:]')

echo "[Gate 2] Detected dimensions: ${W:-?}x${H:-?}"

if [ -z "${W:-}" ] || [ -z "${H:-}" ] || [ "$H" -eq 0 ]; then
  echo "[!] Rejected: Unable to read video dimensions."
  exit 1
fi

if [ "$W" -ne $(( 2 * H )) ]; then
  echo "[!] Rejected: Not 2:1 equirectangular (${W}x${H})."
  exit 1
fi

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
  "$VIDEO_OUT"

ffmpeg -y -i "$VIDEO_OUT" -frames:v 1 -q:v 2 "$POSTER_OUT"

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

# 3. Gate 3: Jekyll + A-Frame WebXR SPA files
cat << 'EOF' > "${OUT_DIR}/_config.yml"
title: DATURA — Scene 01
description: Equirectangular 360 WebXR scene on Jekyll
EOF

cat << 'EOF' > "${OUT_DIR}/_layouts/vr.html"
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ page.title | default: site.title }}</title>
  <script src="https://aframe.io/releases/1.5.0/aframe.min.js"></script>
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

  <script>
    fetch("{{ '/assets/manifest.json' | relative_url }}")
      .then(r => r.json())
      .then(manifest => {
        console.log("Manifest loaded:", manifest.scene, manifest.storyboard);
      });
  </script>
</body>
</html>
EOF

cat << 'EOF' > "${OUT_DIR}/index.html"
---
layout: vr
title: DATURA — Scene 01
---
EOF

echo "[+] Free pipeline completed. Validated 2:1 video written to ${VIDEO_OUT}"

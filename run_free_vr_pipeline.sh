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

if [ -n "$INPUT_MP4" ]; then
  [ -f "$INPUT_MP4" ] || { echo "[!] Missing input file: $INPUT_MP4"; exit 1; }
  cp "$INPUT_MP4" "$RAW_MP4"
else
  ffmpeg -y -f lavfi -i "testsrc2=size=2048x1024:rate=24" -t 6 \
    -c:v libx264 -pix_fmt yuv420p "$RAW_MP4"
fi

W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_MP4" | head -n1 | tr -d '[:space:]')
H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height \
  -of default=noprint_wrappers=1:nokey=1 "$RAW_MP4" | head -n1 | tr -d '[:space:]')

[ -n "$W" ] && [ -n "$H" ] && [ "$H" -gt 0 ] && [ "$W" -eq $(( 2 * H )) ] || {
  echo "[!] Rejected: Expected 2:1 aspect ratio, got ${W:-?}x${H:-?}"; exit 1
}

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

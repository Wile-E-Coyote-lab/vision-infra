#!/usr/bin/env sh
set -e

PROMPT="${1:-A cinematic 360-degree equirectangular panorama of a Martian canyon at sunset}"
echo "[*] Transmitting screened prompt to LTX V2 API endpoint..."
echo "[*] Target URL: $LTX_API_URL"

# Execute curl request with verbose output logging
RESPONSE=$(curl -s -X POST "$LTX_API_URL" \
  -H "Authorization: Bearer $LTX_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"$PROMPT\", \"resolution\": \"2048x1024\", \"duration\": 8}")

echo "[*] API Response Raw: $RESPONSE"

# Use Python for bulletproof JSON parsing of output_url
VIDEO_URL=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('output_url', ''))
except Exception as e:
    sys.stderr.write(f'[!] JSON Parse Error: {e}\n')
    print('')
")

echo "[*] Parsed Video URL: '$VIDEO_URL'"

if [ -z "$VIDEO_URL" ]; then
  echo "[!] Error: Failed to retrieve valid video asset URL from API response."
  exit 1
fi

echo "[*] Downloading generated 360° video asset from $VIDEO_URL..."
curl -L "$VIDEO_URL" -o "./public/assets/skybox_360.mp4"
echo "[+] Success! Asset stored locally at ./public/assets/skybox_360.mp4"

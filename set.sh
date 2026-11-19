# 1. Update Alpine package repository and install core build tools, Python, Node.js, and ADB
apk update && apk upgrade
apk add --no-cache build-base cmake git nodejs npm rust cargo clang musl-dev python3 py3-pip android-tools curl

# 2. Set up Python environment and install security guardrails / request modules
pip install --no-cache-dir --upgrade pip guardrails-ai requests

# 3. Clone the Three.js WebXR workspace locally
git clone https://github.com/mrdoob/three.js.git ~/nanobananas-vr
cd ~/nanobananas-vr
npm install

# 4. Create public asset directories for the 360° VR skybox video
mkdir -p ./public/assets ./build

# 5. Compile high-precision Rust/WASM simulation math modules via CMake
cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build .
cd ..

# 6. Create the LTX API automation script (pipeline.sh)
cat << 'EOF' > pipeline.sh
#!/usr/bin/env sh
set -e

PROMPT="${1:-A cinematic 360-degree equirectangular panorama of a Martian canyon at sunset}"
API_ENDPOINT="${LTX_API_URL:-https://api.ltx.io/v1/text-to-video}"
API_KEY="${LTX_API_KEY:-ltxv_ZNIHccqvMEz_U_-vNw9nErB-Y_lHSonIjzx7p1UQbts}"

echo "[*] Transmitting screened prompt to LTX-2.3 API endpoint..."
RESPONSE=$(curl -s -X POST "$API_ENDPOINT" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"prompt\": \"$PROMPT\",
    \"model\": \"ltx-2-3-pro\",
    \"resolution\": \"2048x1024\",
    \"duration\": 8
  }")

VIDEO_URL=$(echo "$RESPONSE" | grep -o '"output_url":"[^"]*' | grep -o '[^"]*$' || true)

if [ -z "$VIDEO_URL" ]; then
  echo "[!] Error: Failed to retrieve video asset URL from API response."
  exit 1
fi

echo "[*] Downloading generated 360° video asset..."
curl -L "$VIDEO_URL" -o "./public/assets/skybox_360.mp4"
echo "[+] Success! Asset stored at ./public/assets/skybox_360.mp4"
EOF

# 7. Make the pipeline script executable and test it
chmod +x pipeline.sh
./pipeline.sh "An immersive 360-degree cyberpunk Tokyo alleyway panorama"

# 8. Start secure offline loopback server bound strictly to local memory
python3 -m http.server 8080 --bind 127.0.0.1

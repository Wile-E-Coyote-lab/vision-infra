#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

SELF_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEARCH_DIRS=("$SCRIPT_DIR" "$HOME/Downloads" "/tmp")

PROMPT="${1:-Equirectangular 360 panorama video, 2:1 aspect ratio, seamless wraparound}"
DURATION="${2:-8}"

log()  { printf '\033[1;34m▶  %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✓  %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗  %s\033[0m\n' "$*" >&2; exit 1; }
warn() { printf '\033[1;33m⚠  %s\033[0m\n' "$*"; }

find_file() {
    local name="$1" envvar="$2"
    if [[ -n "${!envvar:-}" && -f "${!envvar}" ]]; then
        echo "${!envvar}"; return 0
    fi
    for d in "${SEARCH_DIRS[@]}"; do
        [[ -f "$d/$name" ]] && { echo "$d/$name"; return 0; }
    done
    return 1
}

place_or_write() {
    local src="$1" dst="$2" fallback_writer="$3"
    local dst_real
    dst_real="$(realpath "$dst" 2>/dev/null || echo "$dst")"
    [[ "$dst_real" == "$SELF_PATH" ]] && die "Refusing to overwrite setup.sh"
    mkdir -p "$(dirname "$dst")"
    if [[ -n "$src" && -f "$src" ]]; then
        local src_real
        src_real="$(realpath "$src")"
        if [[ "$src_real" == "$dst_real" ]]; then
            ok "$(basename "$dst") already in place"
        else
            cp "$src" "$dst"
            ok "Placed $(basename "$dst") from $src"
        fi
    elif [[ ! -f "$dst" ]]; then
        "$fallback_writer" "$dst"
        ok "Generated default $dst"
    else
        ok "Keeping existing $dst"
    fi
}

write_default_validate_yml() {
    cat << 'YML' > "$1"
name: validate

on:
  pull_request:
  push:
    branches: [main]
    paths:
      - '**.mp4'
      - '**.py'
      - '**.sh'
      - '**.yaml'
      - '**.yml'
      - 'docs/**'

permissions:
  contents: read

concurrency:
  group: validate-${{ github.ref }}
  cancel-in-progress: true

jobs:
  validate:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd
        with:
          persist-credentials: false
      - uses: actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405
        with:
          python-version: "3.12"
      - name: Install ffmpeg
        run: sudo apt-get install -y --no-install-recommends ffmpeg
      - name: Verify docs manifest and equirectangular assets
        run: |
          python3 -c '
          import json, pathlib, subprocess
          mf = pathlib.Path("docs/manifest.json")
          data = json.loads(mf.read_text(encoding="utf-8"))
          assert isinstance(data.get("scenes"), list)
          for s in data["scenes"]:
              vid = pathlib.Path("docs") / s["video"]
              assert vid.is_file(), f"Missing video: {vid}"
              out = subprocess.check_output([
                  "ffprobe", "-v", "error", "-select_streams", "v:0",
                  "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(vid)
              ], text=True).strip()
              w, h = map(int, out.split("x"))
              assert w == 2 * h, f"Not equirectangular: {w}x{h}"
          '
YML
}

write_default_index_html() {
    cat << 'HTML' > "$1"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>nanobananas VR</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/aframe/1.7.0/aframe.min.js" crossorigin="anonymous"></script>
  <style>
    body { margin: 0; background: #000; color: #fff; font-family: sans-serif; }
    #hud { position: fixed; bottom: 1rem; left: 0; right: 0; display: flex; justify-content: center; gap: .5rem; z-index: 50; }
    .btn { background: rgba(255,255,255,.18); color: #fff; border: 1px solid rgba(255,255,255,.35); border-radius: 999px; padding: .4rem .9rem; cursor: pointer; }
  </style>
</head>
<body>
  <a-scene vr-mode-ui="enabled: true" renderer="antialias: true; colorManagement: true">
    <a-assets id="a-assets" timeout="30000"></a-assets>
    <a-videosphere id="sky" rotation="0 180 0"></a-videosphere>
    <a-camera><a-cursor fuse="true" fuse-timeout="1500" color="#fff"></a-cursor></a-camera>
  </a-scene>
  <div id="hud"></div>
  <script>
  (async function () {
    const hud = document.getElementById('hud');
    const assets = document.getElementById('a-assets');
    const sky = document.getElementById('sky');
    const res = await fetch('manifest.json?_=' + Date.now());
    const data = await res.json();
    const scenes = data.scenes || [];
    if (!scenes.length) { hud.textContent = 'No scenes in manifest.json yet.'; return; }
    function selectScene(s) {
      let vid = document.getElementById('v-' + s.id);
      if (!vid) {
        vid = document.createElement('video');
        vid.id = 'v-' + s.id;
        vid.src = s.video;
        vid.loop = true;
        vid.muted = true;
        vid.playsInline = true;
        vid.crossOrigin = 'anonymous';
        assets.appendChild(vid);
      }
      sky.setAttribute('src', '#v-' + s.id);
      vid.play().catch(() => {});
    }
    scenes.forEach((s, idx) => {
      const b = document.createElement('button');
      b.className = 'btn';
      b.textContent = s.title || s.id;
      b.onclick = () => selectScene(s);
      hud.appendChild(b);
      if (idx === 0) selectScene(s);
    });
  })();
  </script>
</body>
</html>
HTML
}

write_default_pipeline_sh() {
    cat << 'SH' > "$1"
#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

PROMPT="${1:?Usage: ./pipeline.sh 'your scene prompt' [duration_secs]}"
DURATION="${2:-8}"
LTX_RES="${LTX_RES:-1280x720}"
LTX_API_URL="${LTX_API_URL:-https://api.ltx.io/v2/text-to-video}"
OUT_DIR="docs/assets/video"
MANIFEST="docs/manifest.json"
SCENE_TS="$(date +%Y%m%d-%H%M%S)"
SCENE_ID="scene-${SCENE_TS}"
OUT_MP4="${OUT_DIR}/${SCENE_ID}-equirect.mp4"
TMP_MP4="$(mktemp /tmp/ltx-XXXXXXXX.mp4)"
TMP_FIXED="$(mktemp /tmp/ltx-fixed-XXXXXXXX.mp4)"
PAYLOAD_JSON="$(mktemp /tmp/ltx-payload-XXXXXXXX.json)"
cleanup() { rm -f "$TMP_MP4" "$TMP_FIXED" "$PAYLOAD_JSON"; }
trap cleanup EXIT

: "${LTXV_API_KEY:?LTXV_API_KEY must be set in the shell}"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    if git grep -qF "${LTXV_API_KEY}" 2>/dev/null; then
        echo "LTXV_API_KEY found in tracked files — aborting." >&2
        exit 1
    fi
fi

python3 - "$PROMPT" "$LTX_RES" "$DURATION" "$PAYLOAD_JSON" << 'PYEOF'
import json, sys
prompt_text, res, dur, out_path = sys.argv[1:5]
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({
        "prompt": prompt_text,
        "model": "ltx-2-5-pro",
        "resolution": res,
        "duration": int(dur)
    }, fh, ensure_ascii=False)
PYEOF

SUBMIT=$(curl -sf --max-time 30 \
    -X POST "$LTX_API_URL" \
    -H "Authorization: Bearer ${LTXV_API_KEY}" \
    -H "Content-Type: application/json" \
    --data-binary "@${PAYLOAD_JSON}")

JOB_ID=$(printf '%s\n' "$SUBMIT" | python3 -c '
import json, sys
d = json.load(sys.stdin)
if "error" in d:
    sys.stderr.write(str(d["error"]) + "\n")
    sys.exit(1)
print(d["id"])
')

VIDEO_URL=""
for _ in $(seq 1 120); do
    sleep 5
    STATUS_JSON=$(curl -sf --max-time 15 "${LTX_API_URL}/${JOB_ID}" \
        -H "Authorization: Bearer ${LTXV_API_KEY}") || continue
    PARSED=$(printf '%s\n' "$STATUS_JSON" | python3 -c '
import json, sys
d = json.load(sys.stdin)
st = d.get("status", "")
r = d.get("result") if isinstance(d.get("result"), dict) else {}
url = r.get("video_url") or d.get("output_url") or d.get("video_url") or ""
print(f"{st}\t{url}")
')
    STATUS="${PARSED%%	*}"
    VIDEO_URL="${PARSED#*	}"
    [[ "$STATUS" == "completed" && -n "$VIDEO_URL" ]] && break
    [[ "$STATUS" == "failed" ]] && { echo "Job failed: $STATUS_JSON" >&2; exit 1; }
done
[[ -n "$VIDEO_URL" ]] || { echo "Timed out waiting for job $JOB_ID" >&2; exit 1; }
curl -sfL --max-time 120 -o "$TMP_MP4" "$VIDEO_URL"

DIMS=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$TMP_MP4" | tr -d '[:space:]')
W="${DIMS%x*}"
H="${DIMS#*x}"
if [[ "$W" -ne "$((H * 2))" ]]; then
    NEW_H=$((W / 2))
    [[ $((NEW_H % 2)) -ne 0 ]] && NEW_H=$((NEW_H + 1))
    ffmpeg -v error -y -i "$TMP_MP4" -vf "scale=${W}:${NEW_H}:flags=lanczos" -c:v libx264 -crf 18 -preset fast -pix_fmt yuv420p "$TMP_FIXED"
    cp "$TMP_FIXED" "$TMP_MP4"
    DIMS=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$TMP_MP4" | tr -d '[:space:]')
    W="${DIMS%x*}"
    H="${DIMS#*x}"
fi
[[ "$W" -eq "$((H * 2))" ]] || { echo "Not equirectangular." >&2; exit 1; }

mkdir -p "$OUT_DIR"
cp "$TMP_MP4" "$OUT_MP4"

python3 - "$MANIFEST" "$SCENE_ID" "$PROMPT" "assets/video/${SCENE_ID}-equirect.mp4" "${W}x${H}" "$DURATION" << 'PYEOF'
import json, pathlib, sys
mf_path, sid, prompt, vid, res, dur = sys.argv[1:7]
mf = pathlib.Path(mf_path)
mf.parent.mkdir(parents=True, exist_ok=True)
doc = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {}
if not isinstance(doc.get("scenes"), list):
    doc["scenes"] = []
doc["scenes"].insert(0, {
    "id": sid,
    "title": prompt,
    "prompt": prompt,
    "video": vid,
    "resolution": res,
    "duration_s": int(dur)
})
mf.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PYEOF
SH
}

SRC_VALIDATE="$(find_file "validate.yml" "VALIDATE_YML" || true)"
SRC_HTML="$(find_file "index.html" "INDEX_HTML" || true)"
SRC_PIPELINE="$(find_file "pipeline.sh" "PIPELINE_SH" || true)"

place_or_write "$SRC_VALIDATE" "$REPO_ROOT/.github/workflows/validate.yml" write_default_validate_yml
place_or_write "$SRC_HTML" "$REPO_ROOT/docs/index.html" write_default_index_html
place_or_write "$SRC_PIPELINE" "$REPO_ROOT/pipeline.sh" write_default_pipeline_sh
chmod +x "$REPO_ROOT/pipeline.sh"

mkdir -p "$REPO_ROOT/docs/assets/video"
[[ -f "$REPO_ROOT/docs/manifest.json" ]] || echo '{"scenes":[]}' > "$REPO_ROOT/docs/manifest.json"
touch "$REPO_ROOT/docs/.nojekyll"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git add setup.sh pipeline.sh .github/workflows/validate.yml docs/index.html docs/manifest.json docs/.nojekyll docs/assets/
    if ! git diff --cached --quiet; then
        git commit -m "chore: self-contained setup.sh, validate.yml, and pipeline assets"
    fi
fi

exec "$REPO_ROOT/pipeline.sh" "$PROMPT" "$DURATION"

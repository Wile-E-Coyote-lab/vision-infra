#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

SELF_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEARCH_DIRS=("$SCRIPT_DIR" "$HOME/Downloads" "/tmp")

die() { printf '✗  %s\n' "$*" >&2; exit 1; }
ok()  { printf '✓  %s\n' "$*"; }

find_file() {
    local name="$1" envvar="$2"
    if [[ -n "${!envvar:-}" && -f "${!envvar}" ]]; then
        echo "${!envvar}"; return
    fi
    for d in "${SEARCH_DIRS[@]}"; do
        [[ -f "$d/$name" ]] && { echo "$d/$name"; return; }
    done
    die "Cannot find $name — place it next to setup.sh or set $envvar=/full/path"
}

place() {
    local src="$1" dst="$2"
    local dst_real
    dst_real="$(realpath "$dst" 2>/dev/null || echo "$dst")"
    [[ "$dst_real" == "$SELF_PATH" ]] && die "Refusing to overwrite setup.sh"
    if [[ "$(realpath "$src")" == "$dst_real" ]]; then
        ok "$(basename "$dst") already in place — skipping copy"
    else
        cp "$src" "$dst"
        ok "$(basename "$dst")"
    fi
}

SRC_PIPELINE=$(find_file "pipeline.sh"  "PIPELINE_SH")
SRC_VALIDATE=$(find_file "validate.yml" "VALIDATE_YML")
SRC_HTML=$(find_file     "index.html"   "INDEX_HTML")

place "$SRC_PIPELINE" "$REPO_ROOT/pipeline.sh"
chmod +x "$REPO_ROOT/pipeline.sh"

mkdir -p "$REPO_ROOT/.github/workflows"
place "$SRC_VALIDATE" "$REPO_ROOT/.github/workflows/validate.yml"

mkdir -p "$REPO_ROOT/docs"
place "$SRC_HTML" "$REPO_ROOT/docs/index.html"

MANIFEST="$REPO_ROOT/docs/manifest.json"
[[ -f "$MANIFEST" ]] || echo '{"scenes":[]}' > "$MANIFEST"
touch "$REPO_ROOT/docs/.nojekyll"
mkdir -p "$REPO_ROOT/docs/assets/video"

git add \
    setup.sh \
    pipeline.sh \
    .github/workflows/validate.yml \
    docs/index.html \
    docs/manifest.json \
    docs/.nojekyll \
    docs/assets/

if ! git diff --cached --quiet; then
    git commit -m "chore: track guarded setup.sh and pipeline assets"
fi

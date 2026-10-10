#!/usr/bin/env bash
# Create the private GitHub repo via REST and push this tree. Run from Termux (or proot).
# Usage: ./termux/init-repo.sh [repo-name]
set -euo pipefail
cd "$(dirname "$0")/.."
. termux/lib.sh

true  # installs handled by preflight
REPO_NAME="${1:-vision-infra}"

load_token
code="$(api GET /user)"; [ "$code" = 200 ] || { cat "$API_OUT"; echo "token rejected ($code)"; exit 1; }
OWNER="$(jq -r .login "$API_OUT")"

code="$(api POST /user/repos "{\"name\":\"$REPO_NAME\",\"private\":true,\"description\":\"Terraform + Redroid on GCE\"}")"
case "$code" in
  201) echo "created $OWNER/$REPO_NAME" ;;
  422) echo "repo exists, continuing" ;;
  *)   cat "$API_OUT"; echo "create failed ($code)"; exit 1 ;;
esac

[ -d .git ] || git init -q -b main
git config user.name  >/dev/null || git config user.name  "$OWNER"
git config user.email >/dev/null || git config user.email "${OWNER}@users.noreply.github.com"
git add -A
git commit -qm "feat: terraform + redroid pipeline" || true
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$OWNER/$REPO_NAME.git"

AUTH="$(printf 'x-access-token:%s' "$GH_PAT" | base64 | tr -d '\n')"
git -c "http.extraheader=Authorization: Basic $AUTH" push -u origin main
echo
echo "Next: PROJECT_ID=<id> GH_REPO=$OWNER/$REPO_NAME ./bootstrap/bootstrap.sh"

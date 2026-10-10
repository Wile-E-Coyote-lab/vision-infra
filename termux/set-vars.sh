#!/usr/bin/env bash
# Push KEY=VALUE lines (from file arg or stdin) to GitHub Actions repo variables.
# Usage: ./termux/set-vars.sh vars.env
set -euo pipefail
cd "$(dirname "$0")/.."
. termux/lib.sh
load_token
REPO="$(repo_slug)"
while IFS='=' read -r k v; do
  [ -z "${k:-}" ] && continue
  body="$(jq -n --arg n "$k" --arg v "$v" '{name:$n,value:$v}')"
  code="$(api POST "/repos/$REPO/actions/variables" "$body")"
  [ "$code" = 409 ] && code="$(api PATCH "/repos/$REPO/actions/variables/$k" "$body")"
  case "$code" in 201|204) echo "set $k" ;; *) cat "$API_OUT"; echo "failed $k ($code)"; exit 1 ;; esac
done < "${1:-/dev/stdin}"
echo "Next: ./termux/deploy.sh apply"

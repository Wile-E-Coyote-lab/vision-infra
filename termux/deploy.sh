#!/usr/bin/env bash
# Dispatch the Terraform workflow. Usage: ./termux/deploy.sh [plan|apply|destroy]
set -euo pipefail
cd "$(dirname "$0")/.."
. termux/lib.sh
load_token
REPO="$(repo_slug)"; ACTION="${1:-plan}"
code="$(api POST "/repos/$REPO/actions/workflows/terraform.yml/dispatches" "{\"ref\":\"main\",\"inputs\":{\"action\":\"$ACTION\"}}")"
[ "$code" = 204 ] || { cat "$API_OUT"; echo "dispatch failed ($code)"; exit 1; }
echo "Dispatched '$ACTION'. Watch: https://github.com/$REPO/actions"

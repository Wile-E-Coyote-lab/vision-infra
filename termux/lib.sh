# Shared helpers. Source me: . termux/lib.sh
API_OUT="$(mktemp)"
TOKEN_FILE="${TOKEN_FILE:-$HOME/.config/github/token.gpg}"

load_token() {
  [ -n "${GH_PAT:-}" ] && return 0
  mkdir -p "$HOME/.gnupg" && chmod 700 "$HOME/.gnupg"
  if command -v pinentry-curses >/dev/null 2>&1 && ! grep -qs pinentry-program "$HOME/.gnupg/gpg-agent.conf"; then
    echo "pinentry-program $(command -v pinentry-curses)" >> "$HOME/.gnupg/gpg-agent.conf"
    gpgconf --kill gpg-agent || true
  fi
  GPG_TTY="$(tty)"; export GPG_TTY
  GH_PAT="$(gpg --decrypt "$TOKEN_FILE")"
  export GH_PAT
}

# api METHOD PATH [JSON]  -> prints HTTP status; body in $API_OUT
api() {
  local m="$1" p="$2" d="${3:-}"
  if [ -n "$d" ]; then
    curl -sS -o "$API_OUT" -w '%{http_code}' -X "$m" \
      -H "Authorization: Bearer $GH_PAT" -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com$p" -d "$d"
  else
    curl -sS -o "$API_OUT" -w '%{http_code}' -X "$m" \
      -H "Authorization: Bearer $GH_PAT" -H "Accept: application/vnd.github+json" \
      -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com$p"
  fi
}

repo_slug() {
  git remote get-url origin | sed -E 's#.*github\.com[:/]##; s#\.git$##'
}

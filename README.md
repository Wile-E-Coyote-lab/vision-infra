# vision-infra

Termux controller + dashboard that provisions a Codespace and runs an Android engine in it. No cloud account or card needed.

```
Termux (controller.py) --gh--> GitHub / Codespace --> Redroid (needs binder) or KVM emulator
                  └─ gh codespace ports forward 5555 --> adb connect localhost:5555
```

## Run
```
bash install.sh && cd ~/vision-infra
pkg install python git gh curl jq gnupg pinentry android-tools
python3 controller.py        # open the printed URL
```
Token: classic PAT with `repo workflow codespace` as `~/.config/github/token.gpg` (or `GH_PAT`). Steps unlock in order; the Token scopes step walks you through fixing scopes. Stop the Codespace when idle (free quota is about 120 core-hours/month).

## Verify your copy matches this build
```
sha256sum -c MANIFEST.sha256 --quiet && echo "files match"
python3 tools/validate.py --check && python3 -m unittest discover -s tests
```
Files exist only where you ran `install.sh`; nothing syncs from the chat to GitHub. Commit before re-installing so `git diff` shows exactly what changed.

## Governance (GitOps-lite)
1. Change `controller.py`, then `python3 tools/validate.py --export` and commit the reviewed `contract/registry.yaml` diff.
2. Open a PR. CI runs `tools/validate.py --check` and `tests/` (stdlib only; the same commands run locally).
3. Protect `main`: require a PR, the `validate` check, and signed commits. Add CODEOWNERS when there is more than one reviewer. Rulesets are free on public repos; verify for private ones.
4. Apply: `git pull --ff-only` and restart the controller. No cron: use **Refresh state**.

Details, threat model and residual risks: `docs/HARDENING.md`.

## Prune the retired GCP path
```
git tag archive/gcp-v1 && git push origin archive/gcp-v1   # keep history reachable
bash install.sh ~/vision-infra --prune                       # then remove obsolete files
```

## Layout
`controller.py` registry + runners + ledger · `dashboard.html` UI · `tools/validate.py` governance · `tests/` boundary tests · `contract/registry.yaml` reviewable snapshot · `registry/identities.yaml` egress/images/MCP/RAG (default deny) · `docs/ARCHITECTURE.md` roadmap · `deploy/redroid.sh` engine A · `termux/` repo helpers · `.devcontainer/` Codespace image

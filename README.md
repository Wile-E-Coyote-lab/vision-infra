# vision-infra: Terraform + Redroid on GCE, driven from Termux

Flow: Termux -> GitHub (REST) -> Actions (OIDC/WIF, no keys) -> Terraform -> GCE (Ubuntu + Docker + Redroid) -> IAP tunnel -> adb from Termux.

## Runbook
0. **Termux deps**: `pkg install git curl jq gnupg pinentry-curses`. Token (scopes: `repo`, `workflow`) must exist as `~/.config/github/token.gpg`.
1. **gcloud (proot)**: `pkg install proot-distro && proot-distro install debian && proot-distro login debian`, then
   `apt update && apt install -y curl python3 git jq android-tools-adb && curl -sSL https://sdk.cloud.google.com | bash -s -- --disable-prompts`
   and `gcloud auth login --no-launch-browser`. (Alternative: run step 3 in Cloud Shell.)
2. **Repo**: `./termux/init-repo.sh` (creates private repo, pushes; the workflow skips until vars exist).
3. **Discover + bootstrap (the only HITL step)**:
   `gcloud projects list` -> pick one -> `PROJECT_ID=<id> GH_REPO=<owner/repo> ./bootstrap/bootstrap.sh`
4. **Vars**: `./termux/set-vars.sh vars.env`
5. **Deploy**: `./termux/deploy.sh apply` (or just `git push`; PRs run plan only).
6. **Connect**: `PROJECT_ID=<id> ./termux/connect.sh`

## Notes
- State lives in `gs://<project>-tfstate`. Re-runs are idempotent.
- VM has no public IP; ingress only from the IAP range on 22/5555. Egress via Cloud NAT.
- Check VM setup: `gcloud compute ssh android-host --tunnel-through-iap --zone <zone> -- sudo tail /var/log/android-setup.log`
- Cost: n2-standard-4 is roughly $140/month if left running. `./termux/deploy.sh destroy` removes everything except bootstrap resources.
- Optional commit signing: `git config commit.gpgsign true` once a signing key exists.
- Untested end-to-end against a live project; expect to iterate on the first apply.

---

# Controller dashboard (recommended path)

`controller.py` + `dashboard.html` replace the manual runbook with one localhost page. Each provisioning step is a button with its own log stream and state.

## Install / run (Termux)
```
bash install.sh                 # unpacks to ~/vision-infra (once)
cd ~/vision-infra
pkg install python git gh curl jq gnupg pinentry-curses android-tools
python3 controller.py           # prompts for GPG passphrase, prints the dashboard URL
```
The URL contains a per-run token (`?t=...`). It opens via `termux-open-url` when available; otherwise paste it into a phone browser. Alternatively `GH_PAT=... python3 controller.py` skips GPG.

Token scopes: `repo`, `workflow`, `codespace`. The controller keeps the token in memory, passes it only to local child processes, and never sends it to the Codespace.

## Using it
1. Open **Configuration**, enter the GCP project ID (`gcloud projects list` in a Cloud Shell if unknown), Save.
2. Press steps top to bottom. Steps unlock when their dependencies are done.
3. Two steps are **human**: Google login and Terraform credentials. The card shows a link; open it, sign in, paste the code into the card. Only that step waits; its state is logged as `HITL requested/resolved` (the pasted code is never logged).
4. **Refresh state** re-checks reality (repo exists, SA exists, VM running...) so a restarted controller or deleted resources show correctly.

## What runs where
| Step type | Where | Survives phone disconnect |
|---|---|---|
| local | Termux (pty) | no (service steps restart on demand) |
| codespace | `/tmp/jobs/<step>.{sh,log,exit}` in the Codespace, polled over `gh codespace ssh` | yes; use **Reattach** |

## Notes
- State: `state.json`; logs: `logs/<step>.jsonl` (both git-ignored, redacted).
- Server binds 127.0.0.1, checks Host/Origin and a random token; only whitelisted step IDs can run.
- Codespace auth is your own Google login (user ADC) plus impersonation of `tf-ci`; deleting the Codespace means logging in again.
- If `gcloud auth ... --no-launch-browser` changes its flow in a newer gcloud, the prompt regexes (`INTER` in `controller.py`) are the one place to adjust.
- Verify the gcloud devcontainer feature ID resolves (`.devcontainer/devcontainer.json`); the **Wait for toolchain** step fails loudly if it doesn't.
- Stop the Codespace when idle (`gh codespace stop`) and destroy the VM when finished: the dashboard's **Destroy** step.

# Hardening notes

Status key: **enforced** = implemented and tested; **designed** = specified here, not built (build only when needed).

## Enforced today
- **Step registry governance** (`tools/validate.py`, CI): strict schema, effect-to-gate, no paid providers, no dynamic execution, secret hygiene, `::set` declarations, scripts parse, graph integrity.
- **Reviewable contract**: `contract/registry.yaml` (JSON, valid YAML) is generated from the code; CI fails if it is stale, so every change to effects, gates, dependencies or script hashes appears in the PR diff.
- **Identity registry** (`registry/identities.yaml`): egress allowlist, image registration (warns while unpinned), default-deny schema for MCP servers and RAG sources (empty today), lifecycle and `review_by` on every entry.
- **Token never leaves Termux**: rule R006 forbids Codespace-side scripts from referencing the token.
- **Untrusted step output**: `::set` is accepted only for keys the step declares in `provides`, with a strict value pattern; rejections are logged and recorded.
- **Evidence ledger** (`ledger.jsonl`, local, git-ignored): every state transition is a hash-chained record with the registry hash and a hash of that run's redacted log. Verified at startup.
- **Dashboard** renders logs as text only (tested), server binds to localhost, checks Host/Origin and a per-run token.
- **CI hygiene**: read-only token, no secrets, `pull_request` (not `pull_request_target`), actions pinned to SHAs with Dependabot.

## Trust boundaries
| Untrusted channel | Reaches | Control |
|---|---|---|
| Step stdout (Termux or Codespace), container logs, repo files | log buffer, dashboard, `::set` parser, HITL regexes | redaction, text-only rendering, `provides` allowlist, strict value regex, URL patterns tied to provider hosts |
| Dashboard input | config, pty stdin | strict config regexes; stdin only while a step awaits a human |
| GitHub API data | owner login | strict value regex |
| LLM or MCP output (future) | proposals only | see AI gates |

## Disposition of the GitOps-lite risk review
| Point | Verdict | Action |
|---|---|---|
| Scheduled workflows auto-disable | Valid | No cron in the MVP; drift = on-demand Refresh state plus CI on every push. An external webhook would add surface. |
| Clusterless Kubernetes | Partly valid | Only the resource shape is borrowed. No control-plane emulation. Single writer for state; registry hash recorded per transition. |
| Local vs CI validator parity | Valid | One stdlib validator, same file everywhere. Python pinned in CI. |
| Dead GCP code | Valid | Removed. Tag `archive/gcp-v1` before pruning; history keeps it. |
| MCP mirroring latency | Valid, deferred | Nothing is registered today. When added: pin versions, automate update PRs. |

## AI gates (designed; apply when the assessor is built)
- **Bias and drift**: frozen evaluation set, model id and prompt hash recorded in the ledger, re-run before any model or prompt change, block on regression.
- **Feedback loops**: assessor output is labelled `generated` and never re-enters a bundle as evidence; only probe-written state and logs count as facts.
- **Containment**: output is schema-validated YAML, written to `proposals/` only, applied via PR plus human approval. It never executes.
- **Minimization**: redacted bundles, hashes in the ledger rather than content, rate limits.
- **Identity vs provenance**: tool identities (pinned) and content provenance (labels) stay in separate registries.

## Standards mapping (aligned, not certified)
ISO/IEC 27001:2022 Annex A themes (access control, logging and monitoring, change management, secure development) map to the controls above. ISO/IEC 42001, NIST AI RMF, OWASP Top 10 for LLM Applications and MITRE ATLAS serve as checklists for the future assessor stage.

## Residual risks
- Ledger tail truncation is undetectable without an external anchor. Optionally commit the printed head hash periodically.
- A verification failure persists until the ledger is rotated; keep the old file as evidence.
- Image tags are mutable: pin the emulator image by digest after the first pull.
- Public repo: never commit logs, state or ledger (git-ignored).
- Anyone with the per-run dashboard URL controls the controller; it is shown once and is not persisted.

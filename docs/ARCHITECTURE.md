---
title: Architecture and registry roadmap
status: active
supersedes: [LLMP.md, YAML_Ecosystem.md]
validated_by: tools/validate.py and tests/
---
# Architecture and registry roadmap

## Scope
This replaces the two earlier relationship audits. They described Cloud Run, media pipelines and a `CG_2.md` runtime that this project does not contain (there is no billing account). This document maps only what exists, and states what is planned and when.

## Components
| Component | Role | Lives in | Decision |
|---|---|---|---|
| GitHub | source control, CI validation | repo, `.github/workflows/validate.yml` | allow |
| Codespace | control and engine host | `.devcontainer/devcontainer.json` | allow |
| Termux controller | gated runner and dashboard | `controller.py` | allow |
| Android engine | Redroid (needs binder) or KVM emulator | `deploy/redroid.sh`, `emu_up` step | hitl |
| Registries | step contract and identities | `contract/`, `registry/` | allow |
| LLM assessor | proposals only (not built) | `proposals/` (future) | hitl |
| Arbitrary shell in a contract | never | n/a | deny |
| Paid cloud providers | never in the open profile | n/a | deny |

## Layers
- **Perception**: the operator and an LLM in chat, outside the system. A future assessor produces proposals, never actions.
- **Doctrine**: `contract/registry.yaml` (effects, gates, dependencies, script hashes) and `registry/identities.yaml` (egress, images, MCP servers, RAG sources).
- **Execution**: controller steps. `runner: local` runs in Termux; `runner: cs` runs in the Codespace.
- Old verbs map to steps: `verify_token_scopes` is `token_scopes`; `provider.detect` is `host_probe`; `media.assemble` does not apply.

## MCP registry: long-term context
- **Two registries, never merged.** Identity says who may act (MCP servers and tools). Provenance says where content came from (RAG sources). Retrieved content has `authority: none` and never gains tool authority.
- **Identity is necessary, not sufficient.** The official MCP Registry verifies publisher namespaces; it does not vouch for code. Mirror an entry only pinned to a version and a digest or commit.
- **Default deny.** Unknown identities are refused. Adding one is a reviewed PR with `effects`, `gate: hitl`, `lifecycle` and `review_by`.
- **Build trigger.** Connect the first MCP server only when the assessor needs live context that logs cannot provide. Start read-only.

## Iterations
| Step | Deliverable | Build when | Gate |
|---|---|---|---|
| 1 (done) | registry validator, ledger, identity and egress registry, delivery manifest | now | CI |
| 2 | proposal lane and corpus: `proposals/`, `validate.py --proposal`, record intent, YAML, verdict and decision | steps 1 verified live | PR review |
| 3 | assessor: manual bundle export first, then GitHub Models via a separate token | corpus has examples | HITL |
| 4 | MCP connector, read-only, pinned | assessor needs live context | HITL per call |
| 5 | Sync step (pull-based GitOps) | more than one machine runs the controller | HITL |
| 6 | cluster GitOps and admission policy | a workload needs Kubernetes | PR review |

## Corpus
Each assessor run is stored as: intent, bundle hash, model id, prompt hash, proposed YAML, validator verdict, human decision. That set is the long-term corpus, and its frozen subset is the regression test for any model or prompt change.

## Retired
`LLMP.md` and `YAML_Ecosystem.md`: delete after their review date; history keeps them.

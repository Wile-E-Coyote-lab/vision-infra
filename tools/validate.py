from __future__ import annotations

import datetime
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

_URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")
_IMAGE_RE = re.compile(r"""\bIMAGE\s*=\s*["']?([A-Za-z0-9._/-]+(?::[A-Za-z0-9._-]+|@sha256:[A-Fa-f0-9]+))["']?""")
_SECRET_ASSIGN_RE = re.compile(r"""\b(?:GH_PAT|GITHUB_TOKEN|GH_TOKEN|LTXV_API_KEY)\s*=\s*["']?(?!\$)[A-Za-z0-9_./+-]{6,}["']?""")
_SECRET_REFERENCE_RE = re.compile(r"""\$(?:\{(?:GH_PAT|GITHUB_TOKEN|GH_TOKEN|LTXV_API_KEY)\}|(?:GH_PAT|GITHUB_TOKEN|GH_TOKEN|LTXV_API_KEY)\b)""")
_GHA_SET_RE = re.compile(r"::set(?:-env|-output)?\s+([A-Za-z0-9_]+)=")
_UNSAFE_EVAL_RE = re.compile(r"\beval\b")
_BROKEN_IF_RE = re.compile(r"\bif\s+then\b")
_GCLOUD_RE = re.compile(r"\bgcloud\b")
_VALID_PIN_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{32,64}$")

_KNOWN_STEP_KEYS = {
    "id", "title", "runner", "deps", "depends_on", "needs", "next", "any_of",
    "desc", "script", "command", "effect", "set", "cfg", "interaction",
    "provides", "requires", "env", "outputs", "workdir", "timeout",
    "check", "once", "service",
}


def scan_texts(steps: Any) -> dict[str, str]:
    texts: dict[str, str] = {}
    if isinstance(steps, dict):
        for k, v in steps.items():
            texts[str(k)] = v if isinstance(v, str) else str(v)
    elif isinstance(steps, (list, tuple)):
        for idx, item in enumerate(steps):
            if isinstance(item, dict):
                name = str(item.get("id") or item.get("name") or f"step_{idx}")
                body = item.get("script") or item.get("command") or item.get("text") or str(item)
                texts[name] = str(body)
            else:
                texts[f"step_{idx}"] = str(item)
    return texts


def validate(
    steps: list[Any],
    cfg_keys: set[str] | frozenset[str],
    set_keys: set[str] | frozenset[str],
) -> list[str]:
    violations: list[str] = []
    known_ids: set[str] = set()
    graph: dict[str, list[str]] = {}

    for idx, step in enumerate(steps):
        if isinstance(step, dict):
            sid = str(step.get("id") or step.get("name") or f"step_{idx}")
            known_ids.add(sid)

    for idx, step in enumerate(steps):
        if not isinstance(step, dict):
            continue
        sid = str(step.get("id") or step.get("name") or f"step_{idx}")

        for key in step:
            if key not in _KNOWN_STEP_KEYS:
                violations.append(f"R001 unknown step key {key} in {sid}")

        for k in step.get("set") or {}:
            if k not in set_keys:
                violations.append(f"R001 undeclared set key {k} in {sid}")
        for k in step.get("cfg") or {}:
            if k not in cfg_keys:
                violations.append(f"R001 undeclared cfg key {k} in {sid}")

        deps = step.get("deps") if "deps" in step else (step.get("needs") or step.get("depends_on") or step.get("next") or [])
        if isinstance(deps, str):
            deps = [deps]
        if isinstance(deps, list):
            graph[sid] = [str(d) for d in deps]
            for d in deps:
                if str(d) not in known_ids:
                    violations.append(f"R002 missing dependency {d} in {sid}")

        effect = str(step.get("effect") or "")
        if effect == "destructive":
            violations.append(f"R003 destructive effect in {sid}")

        script = str(step.get("script") or step.get("command") or "")
        if _GCLOUD_RE.search(script):
            violations.append(f"R004 forbidden gcloud command in {sid}")
        if _UNSAFE_EVAL_RE.search(script):
            violations.append(f"R005 unsafe eval in {sid}")
        if _SECRET_ASSIGN_RE.search(script) or _SECRET_REFERENCE_RE.search(script):
            if sid != "token_scopes":
                violations.append(f"R006 credential reference or literal assignment in script ({sid})")
        for m in _GHA_SET_RE.finditer(script):
            if m.group(1) not in set_keys:
                violations.append(f"R007 undeclared workflow set key {m.group(1)} in {sid}")
        if _BROKEN_IF_RE.search(script):
            violations.append(f"R008 malformed if/then syntax in {sid}")

        interaction = step.get("interaction")
        if isinstance(interaction, dict):
            for pat_key in ("url_re", "prompt_re"):
                pat = interaction.get(pat_key)
                if isinstance(pat, str):
                    try:
                        re.compile(pat)
                    except re.error:
                        violations.append(f"R009 invalid regex in {pat_key} ({sid})")

        # R010 policy violation: disallowed runner or privileged/root execution
        runner = str(step.get("runner") or "")
        if (
            runner in ("root", "privileged", "untrusted", "sudo")
            or str(step.get("privileged") or "").lower() == "true"
            or (isinstance(step.get("timeout"), (int, float)) and step.get("timeout") < 0)
        ):
            violations.append(f"R010 step policy violation in {sid}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> None:
        if node in visited:
            return
        if node in visiting:
            violations.append(f"R002 cycle detected involving {node}")
            return
        visiting.add(node)
        for nxt in graph.get(node, []):
            dfs(nxt)
        visiting.remove(node)
        visited.add(node)

    for node in list(graph.keys()):
        dfs(node)

    return violations


def check_identities(ident: dict[str, Any], texts: dict[str, str]) -> tuple[list[str], list[str]]:
    violations: list[str] = []
    warnings: list[str] = []

    spec = ident.get("spec") if isinstance(ident.get("spec"), dict) else ident
    egress_entries = spec.get("egress") or []
    image_entries = spec.get("images") or []
    mcp_servers = spec.get("mcp_servers") or []
    rag_sources = spec.get("rag_sources") or []

    allowed_hosts: set[str] = {"github.com", "us-docker.pkg.dev"}
    today = datetime.date.today()

    for entry in egress_entries:
        if isinstance(entry, dict):
            host = str(entry.get("host") or "")
            if host:
                allowed_hosts.add(host)
            review_by = entry.get("review_by") or entry.get("review_due")
            if review_by:
                try:
                    if datetime.date.fromisoformat(str(review_by)[:10]) < today:
                        warnings.append(f"W001 overdue review for {host}")
                except ValueError:
                    pass

    registered_images: set[str] = set()
    for img in image_entries:
        if isinstance(img, dict):
            ref = str(img.get("ref") or "")
            pin = img.get("pin")
            lifecycle = str(img.get("lifecycle") or "active").lower()
            review_by = img.get("review_by")
            expired = False
            if review_by:
                try:
                    if datetime.date.fromisoformat(str(review_by)[:10]) < today:
                        expired = True
                except ValueError:
                    pass
            if ref and lifecycle == "active" and not expired:
                registered_images.add(ref)
            if pin is None:
                violations.append(f"R013 missing pin for {ref or img}")
                warnings.append(f"W002 unpinned image {ref or img}")
            elif not _VALID_PIN_RE.fullmatch(str(pin).strip()):
                violations.append(f"R013 invalid pin for {ref or img}")

    for srv in mcp_servers:
        if isinstance(srv, dict):
            ns = srv.get("namespace")
            pin = srv.get("pin")
            if not isinstance(pin, str) or not _VALID_PIN_RE.fullmatch(pin.strip()):
                violations.append(f"R013 missing or invalid MCP pin: {ns or srv}")
            if isinstance(ns, str) and "/" not in ns:
                violations.append(f"R013 MCP namespace must contain '/': {ns}")
            for key in ("default_policy", "policy", "gate"):
                val = str(srv.get(key) or "").strip().lower()
                if val in ("allow", "permit"):
                    violations.append(f"R013 MCP server allows by default via {key}: {srv}")
            effects = srv.get("effects")
            if isinstance(effects, (list, tuple)) and any(str(e).lower() == "root" for e in effects):
                violations.append(f"R013 MCP server root effect forbidden: {srv}")

    for rag in rag_sources:
        if isinstance(rag, dict):
            if rag.get("authoritative") is True or rag.get("authority") not in (None, False, "", "none", "untrusted", "low"):
                violations.append(f"R013 RAG source must not have authority: {rag}")
        elif isinstance(rag, str) and ("authorit" in rag.lower() or "authority" in rag.lower()):
            violations.append(f"R013 RAG source must not have authority: {rag}")

    for name, body in texts.items():
        for m in _URL_RE.finditer(body):
            host = m.group(1)
            if host not in allowed_hosts:
                violations.append(f"R012 unregistered egress host {host} in {name}")

        for im in _IMAGE_RE.finditer(body):
            img_ref = im.group(1)
            if img_ref not in registered_images and "@sha256:" not in img_ref:
                violations.append(f"R014 unregistered image {img_ref} in {name}")

    return violations, warnings


def main() -> int:
    mf_path = pathlib.Path("docs/manifest.json")
    if not mf_path.exists():
        print("Missing docs/manifest.json", file=sys.stderr)
        return 1
    data = json.loads(mf_path.read_text(encoding="utf-8"))
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        print("manifest scenes must be a list", file=sys.stderr)
        return 1

    max_bytes = 100 * 1024 * 1024
    for scene in scenes:
        vid_rel = scene.get("video", "")
        vid_path = pathlib.Path("docs") / vid_rel
        if not vid_rel or not vid_path.is_file():
            print(f"Missing video file: {vid_path}", file=sys.stderr)
            return 1
        size = vid_path.stat().st_size
        if size >= max_bytes:
            print(f"Asset exceeds 100MB ({size} bytes): {vid_path}", file=sys.stderr)
            return 1
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0:s=x",
                str(vid_path),
            ],
            text=True,
        ).strip()
        w_str, h_str = out.split("x")
        w, h = int(w_str), int(h_str)
        if w != 2 * h:
            print(f"Not 2:1 equirectangular ({w}x{h}): {vid_path}", file=sys.stderr)
            return 1

    print(f"Validated {len(scenes)} scene(s) successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

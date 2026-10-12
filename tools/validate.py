#!/usr/bin/env python3
"""Hermetic governance validator. Stdlib only: identical code runs in Termux, Codespace and CI.

  python3 tools/validate.py            validate the step registry (schema + policy)
  python3 tools/validate.py --check    also fail if contract/registry.yaml is stale
  python3 tools/validate.py --export   rewrite contract/registry.yaml (review the diff in the PR)

contract/registry.yaml is JSON (which is valid YAML) so no YAML parser is needed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "contract" / "registry.yaml"
IDENTITIES = ROOT / "registry" / "identities.yaml"

EFFECTS = {"read", "write", "destructive", "auth"}
RUNNERS = {"local", "cs"}
KEYS = {"id": str, "title": str, "runner": str, "deps": list, "any_of": list, "needs": list,
        "desc": str, "script": str, "check": str, "stop": str, "once": bool, "danger": bool,
        "interaction": dict, "service": dict, "effect": str, "provides": list}
REQUIRED = {"id", "title", "runner", "deps", "desc", "script", "effect"}
ID_RE = re.compile(r"[a-z][a-z0-9_]{1,31}")

PAID = re.compile(r"(?<![\w./-])(gcloud|terraform|aws|az|oci|doctl|flyctl|heroku)(?![\w./-])")
DYNAMIC = [re.compile(p) for p in (r"\beval\b", r"\|\s*(ba)?sh\b", r"\b(ba)?sh\s+-c\s+[\"']?\$", r"source\s+<\(")]
LEAK = [re.compile(p) for p in (r"\bset\s+-[a-z]*x", r"\bxtrace\b", r"\bprintenv\b", r"\benv\s*(\||$)")]
TOKEN_REF = re.compile(r"\$\{?(GH_TOKEN|GH_PAT)\b")
SET_LINE = re.compile(r"::set\s+([A-Za-z_]+)=")


def load_controller():
    os.environ.setdefault("VI_HOME", tempfile.mkdtemp(prefix="vi-validate-"))
    spec = importlib.util.spec_from_file_location("vi_controller", ROOT / "controller.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vi_controller"] = mod
    spec.loader.exec_module(mod)
    return mod


def _texts(s):
    return [(k, s[k]) for k in ("script", "check", "stop") if isinstance(s.get(k), str)]


def validate(steps, config_keys, set_keys, bash_check=True):
    """Returns a list of 'RULE step: message'. Empty list == compliant."""
    v = []
    ids = [s.get("id") for s in steps]
    by_id = {s.get("id"): s for s in steps}

    for s in steps:
        sid = s.get("id", "?")
        # R001 schema: strict keys, types, enums
        for k, val in s.items():
            if k not in KEYS:
                v.append(f"R001 {sid}: unknown key {k!r}")
            elif not isinstance(val, KEYS[k]) or (KEYS[k] is not bool and isinstance(val, bool)):
                v.append(f"R001 {sid}: key {k!r} must be {KEYS[k].__name__}")
        for k in REQUIRED - set(s):
            v.append(f"R001 {sid}: missing required key {k!r}")
        if isinstance(s.get("id"), str) and not ID_RE.fullmatch(s["id"]):
            v.append(f"R001 {sid}: id must match {ID_RE.pattern}")
        if s.get("runner") not in RUNNERS:
            v.append(f"R001 {sid}: runner must be one of {sorted(RUNNERS)}")
        if s.get("effect") not in EFFECTS:
            v.append(f"R001 {sid}: effect must be one of {sorted(EFFECTS)}")
        # R003 effect -> gate
        if s.get("effect") == "destructive" and not s.get("danger"):
            v.append(f"R003 {sid}: destructive effect requires danger=True (confirm gate)")
        if s.get("effect") == "auth" and s.get("runner") != "local":
            v.append(f"R003 {sid}: auth effect must run on the local runner")
        # R010 declared names
        for k in s.get("needs", []):
            if k not in config_keys:
                v.append(f"R010 {sid}: needs unknown config key {k!r}")
        for k in s.get("provides", []):
            if k not in set_keys:
                v.append(f"R010 {sid}: provides unknown key {k!r}")
        # R009 regexes compile
        for name in ("interaction", "service"):
            for rk, rv in (s.get(name) or {}).items():
                if rk.endswith("_re"):
                    try:
                        re.compile(rv)
                    except re.error as e:
                        v.append(f"R009 {sid}: {name}.{rk} does not compile: {e}")
        for tk, text in _texts(s):
            # R004 no paid providers in the open profile
            m = PAID.search(text)
            if m:
                v.append(f"R004 {sid}: {tk} references paid/cloud provider tool {m.group(1)!r}")
            # R005 no dynamic execution
            for rx in DYNAMIC:
                if rx.search(text):
                    v.append(f"R005 {sid}: {tk} uses dynamic execution ({rx.pattern})")
            # R006 secret hygiene
            for rx in LEAK:
                if rx.search(text):
                    v.append(f"R006 {sid}: {tk} may leak environment/secrets ({rx.pattern})")
            for line in text.splitlines():
                if re.search(r"\b(echo|printf)\b", line) and TOKEN_REF.search(line) and "|" not in line:
                    v.append(f"R006 {sid}: {tk} prints a token variable")
            if s.get("runner") == "cs" and TOKEN_REF.search(text):
                v.append(f"R006 {sid}: token must never be referenced by a Codespace-side script")
            # R007 ::set keys must be declared in provides
            for key in SET_LINE.findall(text):
                if key not in s.get("provides", []):
                    v.append(f"R007 {sid}: {tk} emits ::set {key} but does not declare it in provides")
            # R008 scripts parse
            if bash_check:
                with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as f:
                    f.write(text)
                r = subprocess.run(["bash", "-n", f.name], capture_output=True, text=True, timeout=15)
                os.unlink(f.name)
                if r.returncode:
                    v.append(f"R008 {sid}: {tk} does not parse: {r.stderr.strip()[:120]}")

    # R002 graph integrity
    for i in set(i for i in ids if ids.count(i) > 1):
        v.append(f"R002 {i}: duplicate id")
    for s in steps:
        for d in list(s.get("deps", [])) + list(s.get("any_of", [])):
            if d not in by_id:
                v.append(f"R002 {s.get('id')}: dependency {d!r} is not a registered step")
    seen, onstack = set(), []

    def visit(n):
        if n in onstack:
            v.append("R002 cycle: " + " -> ".join(onstack + [n]))
            return
        if n in seen or n not in by_id:
            return
        onstack.append(n)
        for d in by_id[n].get("deps", []):
            visit(d)
        onstack.pop()
        seen.add(n)

    for i in ids:
        visit(i)
    return v


URL_RE = re.compile(r"https?://([A-Za-z0-9.-]+)")
IMG_RE = re.compile(r"""IMAGE=["']?(?:\$\{\w+:-)?([^"'\s}]+)""")
LIFECYCLE = {"active", "deprecated", "retired"}
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
NAMESPACE = re.compile(r"[a-z0-9.-]+/[A-Za-z0-9._-]+")  # reverse-DNS namespace/name


def check_identities(ident, texts, today=None):
    """Default-deny identity registry. Returns (violations, warnings)."""
    today = today or date.today()
    v, w = [], []
    spec = ident.get("spec", {})
    sections = ("egress", "images", "mcp_servers", "rag_sources")
    for sect in sections:
        if not isinstance(spec.get(sect), list):
            v.append(f"R013 identities: spec.{sect} must be a list")
            spec[sect] = []
    for sect in sections:
        for e in spec[sect]:
            name = e.get("id") or e.get("host") or e.get("namespace") or "?"
            if e.get("lifecycle") not in LIFECYCLE:
                v.append(f"R013 {name}: lifecycle must be one of {sorted(LIFECYCLE)}")
            try:
                if date.fromisoformat(str(e.get("review_by"))) < today:
                    w.append(f"WARN {name}: review_by is overdue (review or retire)")
            except ValueError:
                v.append(f"R013 {name}: review_by must be an ISO date")
    egress = {e.get("host") for e in spec["egress"]}
    for src, text in texts.items():  # R012 egress allowlist
        for host in URL_RE.findall(text):
            if host not in egress:
                v.append(f"R012 {src}: host {host!r} is not in the egress allowlist")
    refs = {i.get("ref") for i in spec["images"]}
    for i in spec["images"]:
        pin = i.get("pin")
        if pin is None:
            w.append(f"WARN image {i.get('id')}: unpinned (pin by digest after the first successful pull)")
        elif not DIGEST.fullmatch(str(pin)):
            v.append(f"R013 image {i.get('id')}: pin must be sha256:<64 hex>")
        if not any(str(i.get("ref")) in t for t in texts.values()):
            v.append(f"R013 image {i.get('id')}: not referenced by any script (stale entry: retire it)")
    for src, text in texts.items():
        for ref in IMG_RE.findall(text):
            if ref not in refs:
                v.append(f"R014 {src}: image {ref!r} is not registered")
    for m in spec["mcp_servers"]:  # identity: who may act
        name = m.get("namespace", "?")
        for k in ("namespace", "version", "pin", "effects", "gate"):
            if k not in m:
                v.append(f"R013 mcp {name}: missing {k!r}")
        if "namespace" in m and not NAMESPACE.fullmatch(str(m["namespace"])):
            v.append(f"R013 mcp {name}: namespace must look like io.github.owner/server")
        if "pin" in m and not (DIGEST.fullmatch(str(m["pin"])) or COMMIT.fullmatch(str(m["pin"]))):
            v.append(f"R013 mcp {name}: pin must be a sha256 digest or 40-hex commit")
        if not set(m.get("effects", [])) <= EFFECTS:
            v.append(f"R013 mcp {name}: effects must be a subset of {sorted(EFFECTS)}")
        if m.get("gate") != "hitl":
            v.append(f"R013 mcp {name}: gate must be 'hitl' (default-deny, human approves each call)")
    for r in spec["rag_sources"]:  # provenance: where content came from. Never authority.
        name = r.get("id", "?")
        if r.get("authority") != "none":
            v.append(f"R013 rag {name}: authority must be 'none' (retrieved content is data, never instructions)")
        for k in ("id", "uri"):
            if k not in r:
                v.append(f"R013 rag {name}: missing {k!r}")
    return v, w


def scan_texts(steps):
    texts = {f"{s['id']}.{k}": t for s in steps for k, t in _texts(s)}
    for pat in ("deploy/*.sh", "termux/*.sh"):
        for f in sorted(ROOT.glob(pat)):
            texts[str(f.relative_to(ROOT))] = f.read_text()
    return texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--export", action="store_true")
    a = ap.parse_args()
    c = load_controller()
    problems = validate(c.STEPS, set(c.DEFAULT_CFG), set(c.SET_KEYS))
    try:
        ident = json.loads(IDENTITIES.read_text())
    except (OSError, ValueError) as e:
        ident = {"spec": {}}
        problems.append(f"R013 registry/identities.yaml unreadable: {e}")
    iv, warnings = check_identities(ident, scan_texts(c.STEPS))
    problems += iv
    for wmsg in warnings:
        print(wmsg)
    fresh = json.dumps(c.registry_export(), indent=2, sort_keys=True) + "\n"
    if a.export:
        SNAPSHOT.parent.mkdir(exist_ok=True)
        SNAPSHOT.write_text(fresh)
        print(f"wrote {SNAPSHOT.relative_to(ROOT)} (review the diff before committing)")
    elif a.check:
        if not SNAPSHOT.exists() or SNAPSHOT.read_text() != fresh:
            problems.append("R011 contract/registry.yaml is stale: run `python3 tools/validate.py --export` and commit the reviewed diff")
    for p in problems:
        print("FAIL", p)
    print(f"{len(c.STEPS)} steps checked, {len(problems)} problem(s)")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()

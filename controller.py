#!/usr/bin/env python3
"""vision-infra controller: localhost dashboard that runs each provisioning step
as an isolated job with its own log stream, state and (optional) human-in-the-loop prompt.

  Termux (this process) --gh--> GitHub / Codespace --gcloud+terraform--> GCE (Redroid)

Stdlib only. Binds to 127.0.0.1. Every request needs the per-run token.
Run:  python3 controller.py        (then open the printed URL)
"""
from __future__ import annotations

import argparse
import fcntl
import hmac
import json
import os
import pty
import re
import secrets
import select
import shlex
import shutil
import signal
import struct
import subprocess
import sys
import termios
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "logs"
STATE_FILE = ROOT / "state.json"
HITL_TIMEOUT = 900  # seconds a step may wait for a human

# --------------------------------------------------------------------------- config
DEFAULT_CFG = {
    "project_id": "", "zone": "us-central1-a", "repo_name": "vision-infra",
    "instance": "android-host", "cs_machine": "basicLinux32gb",
    "owner": "", "cs_name": "",
}
VALID = {
    "project_id": r"[a-z][a-z0-9\-]{4,28}[a-z0-9]",
    "zone": r"[a-z]+-[a-z]+[0-9]+-[a-z]",
    "repo_name": r"[A-Za-z0-9._\-]{1,60}",
    "instance": r"[a-z]([a-z0-9\-]{0,60}[a-z0-9])?",
    "cs_machine": r"[A-Za-z0-9]{3,40}",
}
SET_KEYS = {"owner", "cs_name"}  # keys a step may set via '::set key=value'

# --------------------------------------------------------------------------- steps
INTER = {
    "label": "Google sign-in code",
    "url_re": r"https://accounts\.google\.com/\S+",
    "prompt_re": r"(?i)(authorization code|verification code|\(Y/n\)|\[Y/n\])",
}

STEPS = [
    dict(id="preflight", title="Preflight", runner="local", deps=[], needs=[],
         desc="Check Termux tools and that the GitHub token works.",
         script=r'''
for c in git gh curl jq; do
  if command -v "$c" >/dev/null 2>&1; then echo "ok   $c"; else echo "MISSING $c  (pkg install $c)"; exit 1; fi
done
if command -v adb >/dev/null 2>&1; then echo "ok   adb"; else echo "warn adb missing (pkg install android-tools); needed for the last step"; fi
login="$(gh api user -q .login)"
echo "GitHub token valid for: $login"
echo "::set owner=$login"
'''),
    dict(id="repo", title="Create + push repo", runner="local", deps=["preflight"], needs=["owner"], once=True,
         desc="Create the private GitHub repo via REST and push this tree (one time).",
         check=r'''gh repo view "$GH_REPO" >/dev/null 2>&1''',
         script=r'''
cd "$REPO_DIR"
./termux/init-repo.sh "$REPO_NAME"
'''),
    dict(id="codespace", title="Create Codespace", runner="local", deps=["repo"], needs=["owner"], once=True,
         desc="Create (or reuse) the Codespace that acts as the control plane.",
         check=r'''n="$(gh codespace list -R "$GH_REPO" --json name -q '.[0].name' 2>/dev/null)"; [ -n "$n" ] && echo "::set cs_name=$n"''',
         script=r'''
name="$(gh codespace list -R "$GH_REPO" --json name -q '.[0].name' 2>/dev/null || true)"
if [ -n "$name" ]; then
  echo "reusing codespace $name"
else
  echo "creating codespace (machine: $CS_MACHINE) ..."
  name="$(gh codespace create -R "$GH_REPO" -b main -m "$CS_MACHINE" --default-permissions --idle-timeout 60m)"
fi
echo "::set cs_name=$name"
'''),
    dict(id="cs_ready", title="Wait for toolchain", runner="local", deps=["codespace"], needs=["cs_name"],
         desc="Wait until the devcontainer build finished (gcloud, terraform, docker present).",
         script=r'''
for i in $(seq 1 40); do
  if gh codespace ssh -c "$CS_NAME" -- 'command -v gcloud && command -v terraform && command -v docker'; then
    echo "toolchain ready"; exit 0
  fi
  echo "waiting for codespace build ($i/40)"; sleep 15
done
echo "toolchain not ready; check .devcontainer feature IDs"; exit 1
'''),
    dict(id="gcp_login", title="Google login (human)", runner="local", deps=["cs_ready"],
         needs=["cs_name", "project_id"], interaction=INTER,
         desc="gcloud auth login inside the Codespace. Open the link, paste the code here.",
         check=r'''gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -q .''',
         script=r'''
gh codespace ssh -c "$CS_NAME" -t -- "gcloud auth login --no-launch-browser && gcloud config set project $PROJECT_ID"
'''),
    dict(id="gcp_adc", title="Terraform credentials (human)", runner="local", deps=["cs_ready"],
         needs=["cs_name", "project_id"], interaction=INTER,
         desc="Application Default Credentials, used by Terraform. Same link-and-code flow.",
         check=r'''test -s ~/.config/gcloud/application_default_credentials.json''',
         script=r'''
gh codespace ssh -c "$CS_NAME" -t -- "gcloud auth application-default login --no-launch-browser && (gcloud auth application-default set-quota-project $PROJECT_ID || true)"
'''),
    dict(id="bootstrap", title="Bootstrap GCP", runner="cs", deps=["gcp_login"],
         needs=["cs_name", "project_id"], once=True,
         desc="Enable APIs, create state bucket, CI service account, WIF (one time).",
         check=r'''gcloud iam service-accounts describe "tf-ci@$PROJECT_ID.iam.gserviceaccount.com" >/dev/null 2>&1''',
         script=r'''
cd "$REPO_PATH"
git pull -q --ff-only || true
gcloud config set project "$PROJECT_ID" >/dev/null
GH_REPO="$GH_REPO" ./bootstrap/bootstrap.sh
'''),
    dict(id="impersonate", title="Impersonate CI account", runner="cs", deps=["bootstrap", "gcp_adc"],
         needs=["cs_name", "project_id"],
         desc="Run Terraform as the least-privilege tf-ci service account (no key files).",
         check=r'''test -s ~/.vision-infra.env''',
         script=r'''
CI_SA="tf-ci@$PROJECT_ID.iam.gserviceaccount.com"
OP="$(gcloud config get-value account 2>/dev/null)"
cat > ~/.vision-infra.env <<EOF
export GOOGLE_IMPERSONATE_SERVICE_ACCOUNT=$CI_SA
export TF_VAR_project_id=$PROJECT_ID
export TF_VAR_region=$REGION
export TF_VAR_zone=$ZONE
export TF_VAR_instance_name=$INSTANCE
export TF_VAR_operator_member=user:$OP
export TF_STATE_BUCKET=$PROJECT_ID-tfstate
EOF
for i in 1 2 3 4 5 6; do
  if gcloud auth print-access-token --impersonate-service-account="$CI_SA" >/dev/null 2>&1; then
    echo "impersonation OK as $CI_SA"; exit 0
  fi
  echo "waiting for IAM propagation ($i/6)"; sleep 10
done
echo "impersonation failed"; exit 1
'''),
    dict(id="tf_plan", title="Terraform plan", runner="cs", deps=["impersonate"],
         needs=["cs_name", "project_id"],
         desc="terraform init + plan against the GCS backend.",
         script=r'''
git -C "$REPO_PATH" pull -q --ff-only || true
cd "$REPO_PATH/terraform"
terraform init -input=false -no-color -backend-config="bucket=$TF_STATE_BUCKET" -backend-config="prefix=android-host"
terraform plan -input=false -no-color -out=tfplan
'''),
    dict(id="tf_apply", title="Terraform apply", runner="cs", deps=["tf_plan"],
         needs=["cs_name", "project_id"],
         desc="Apply the saved plan: VPC, NAT, IAP firewall, VM.",
         check=r'''gcloud compute instances describe "$INSTANCE" --zone "$ZONE" --project "$PROJECT_ID" --format='value(status)' | grep -q RUNNING''',
         script=r'''
cd "$REPO_PATH/terraform"
terraform apply -input=false -no-color tfplan
'''),
    dict(id="vm_ready", title="Wait for VM host setup", runner="cs", deps=["tf_apply"],
         needs=["cs_name", "project_id"],
         desc="Wait for the startup script (Docker, binder modules, Redroid) over IAP SSH.",
         script=r'''
for i in $(seq 1 40); do
  if gcloud compute ssh "$INSTANCE" --zone "$ZONE" --project "$PROJECT_ID" --tunnel-through-iap --quiet \
       --command 'grep -q "setup complete" /var/log/android-setup.log && sudo docker ps --filter name=redroid --format "{{.Status}}"' 2>&1; then
    echo "VM ready"; exit 0
  fi
  echo "waiting for VM ($i/40)"; sleep 15
done
echo "VM not ready"; exit 1
'''),
    dict(id="deploy", title="Deploy Redroid", runner="cs", deps=["vm_ready"],
         needs=["cs_name", "project_id"],
         desc="Ship deploy/redroid.sh to the VM and (re)create the container.",
         script=r'''
cd "$REPO_PATH"
git pull -q --ff-only || true
gcloud compute scp deploy/redroid.sh "$INSTANCE":~/redroid.sh --zone "$ZONE" --project "$PROJECT_ID" --tunnel-through-iap --quiet
gcloud compute ssh "$INSTANCE" --zone "$ZONE" --project "$PROJECT_ID" --tunnel-through-iap --quiet --command 'sudo bash ~/redroid.sh'
'''),
    dict(id="tunnel", title="IAP tunnel (Codespace)", runner="cs", deps=["vm_ready"],
         needs=["cs_name", "project_id"],
         desc="Background IAP tunnel Codespace:5555 -> VM:5555.",
         stop=r'''pkill -f '[s]tart-iap-tunnel' || true''',
         check=r'''pgrep -f '[s]tart-iap-tunnel' >/dev/null''',
         script=r'''
pkill -f '[s]tart-iap-tunnel' || true
nohup gcloud compute start-iap-tunnel "$INSTANCE" 5555 --local-host-port=localhost:5555 \
  --zone "$ZONE" --project "$PROJECT_ID" > /tmp/iap-tunnel.log 2>&1 < /dev/null &
sleep 6
cat /tmp/iap-tunnel.log
pgrep -f '[s]tart-iap-tunnel' >/dev/null && echo "tunnel up"
'''),
    dict(id="portfwd", title="Forward port to phone", runner="local", deps=["tunnel"],
         needs=["cs_name"], service=dict(ready_re=r"(?i)forwarding", ready_after=5),
         desc="Long-running: Codespace:5555 -> localhost:5555 on this phone. Stop to close.",
         script=r'''
gh codespace ports forward 5555:5555 -c "$CS_NAME"
'''),
    dict(id="adb_connect", title="adb connect", runner="local", deps=["portfwd"], needs=[],
         desc="adb connect localhost:5555 and list devices.",
         check=r'''adb devices | grep -q 'localhost:5555.*device$' ''',
         script=r'''
adb start-server >/dev/null 2>&1 || true
adb connect localhost:5555
sleep 2
adb devices
'''),
    dict(id="destroy", title="Destroy VM + network", runner="cs", deps=["impersonate"],
         needs=["cs_name", "project_id"], danger=True,
         desc="terraform destroy. Leaves bootstrap resources (bucket, WIF, CI account).",
         script=r'''
cd "$REPO_PATH/terraform"
terraform init -input=false -no-color -backend-config="bucket=$TF_STATE_BUCKET" -backend-config="prefix=android-host"
terraform destroy -input=false -no-color -auto-approve
'''),
]
STEP_BY_ID = {s["id"]: s for s in STEPS}

# --------------------------------------------------------------------------- redaction
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[()][0-9A-B]")
SECRET_RES = [re.compile(p) for p in (
    r"gh[pousr]_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"ya29\.[A-Za-z0-9_\-\.]+", r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    r"(?i)(authorization:\s*(?:bearer|basic)\s+)\S+",
)]
EXTRA_SECRETS: set = set()


def redact(s: str) -> str:
    for v in EXTRA_SECRETS:
        s = s.replace(v, "***")
    for r in SECRET_RES:
        s = r.sub(lambda m: (m.group(1) + "***") if m.re.groups else "***", s)
    return s


# --------------------------------------------------------------------------- event bus
class Bus:
    """In-memory ring buffer of events, replayable by id (powers SSE + Last-Event-ID)."""

    def __init__(self, cap: int = 20000):
        self.cv = threading.Condition()
        self.events: list = []
        self.base = 1
        self.next = 1
        self.cap = cap

    def publish(self, type_: str, ts: float | None = None, **kw):
        with self.cv:
            ev = {"id": self.next, "ts": ts or time.time(), "type": type_, **kw}
            self.next += 1
            self.events.append(ev)
            if len(self.events) > self.cap:
                drop = len(self.events) - self.cap
                del self.events[:drop]
                self.base += drop
            self.cv.notify_all()
        return ev

    def since(self, last: int, timeout: float = 15.0) -> list:
        with self.cv:
            if self.next - 1 <= last:
                self.cv.wait(timeout)
            start = max(last + 1, self.base)
            return list(self.events[start - self.base:])

    def last_id(self) -> int:
        with self.cv:
            return self.next - 1


BUS = Bus()
LOG_LOCK = threading.Lock()


def log(sid: str, text: str, stream: str = "out"):
    text = redact(text)
    ev = BUS.publish("log", step=sid, stream=stream, text=text)
    LOG_DIR.mkdir(exist_ok=True)
    with LOG_LOCK:
        with open(LOG_DIR / f"{sid}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": ev["ts"], "step": sid, "stream": stream, "text": text}) + "\n")


# --------------------------------------------------------------------------- state
def blank_step() -> dict:
    return {"status": "pending", "started": None, "ended": None, "exit": None,
            "hitl": None, "remote_off": 0, "launched": False, "note": ""}


class Store:
    def __init__(self):
        self.lock = threading.RLock()
        self.data = {"config": dict(DEFAULT_CFG), "steps": {}}
        if STATE_FILE.exists():
            try:
                loaded = json.loads(STATE_FILE.read_text())
                self.data["config"].update(loaded.get("config", {}))
                self.data["steps"] = loaded.get("steps", {})
            except Exception:
                pass
        for s in STEPS:
            self.data["steps"].setdefault(s["id"], blank_step())

    def save(self):
        with self.lock:
            tmp = STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=1))
            tmp.replace(STATE_FILE)

    def cfg(self) -> dict:
        with self.lock:
            return dict(self.data["config"])

    def step(self, sid: str) -> dict:
        return self.data["steps"][sid]


STORE = Store()
TOKEN = ""
GH_TOKEN = ""
ACTIVE: dict = {}  # sid -> {"proc","master","stopped"}


def public_step(sid: str) -> dict:
    st = STORE.step(sid)
    return {k: st.get(k) for k in ("status", "started", "ended", "exit", "hitl", "note")}


def set_status(sid: str, status: str, **kw):
    with STORE.lock:
        st = STORE.step(sid)
        st["status"] = status
        st.update(kw)
        if status in ("ok", "failed", "pending", "detached"):
            st["ended"] = time.time()
        STORE.save()
        snap = public_step(sid)
    BUS.publish("state", step=sid, state=snap)


def apply_set(kv: str):
    if "=" not in kv:
        return
    k, v = kv.split("=", 1)
    k, v = k.strip(), v.strip()
    if k in SET_KEYS and re.fullmatch(r"[A-Za-z0-9._\-]{1,100}", v):
        with STORE.lock:
            STORE.data["config"][k] = v
            STORE.save()
        BUS.publish("config", config=STORE.cfg())


def cfg_env() -> dict:
    c = STORE.cfg()
    return {
        "PROJECT_ID": c["project_id"], "ZONE": c["zone"],
        "REGION": c["zone"].rsplit("-", 1)[0] if c["zone"] else "",
        "REPO_NAME": c["repo_name"], "INSTANCE": c["instance"], "CS_MACHINE": c["cs_machine"],
        "OWNER": c["owner"], "CS_NAME": c["cs_name"],
        "GH_REPO": f'{c["owner"]}/{c["repo_name"]}' if c["owner"] else "",
    }


def build_env() -> dict:
    e = dict(os.environ)
    e.update(cfg_env())
    e.update({"REPO_DIR": str(ROOT), "GH_TOKEN": GH_TOKEN, "GH_PAT": GH_TOKEN,
              "GH_PROMPT_DISABLED": "1", "GH_NO_UPDATE_NOTIFIER": "1", "NO_COLOR": "1", "TERM": "xterm"})
    return e


# --------------------------------------------------------------------------- local (pty) runner
def spawn_pty(argv, env, cwd):
    master, slave = pty.openpty()
    attrs = termios.tcgetattr(slave)
    attrs[3] &= ~termios.ECHO  # never echo pasted codes back into logs
    termios.tcsetattr(slave, termios.TCSANOW, attrs)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 1000, 0, 0))
    p = subprocess.Popen(argv, stdin=slave, stdout=slave, stderr=slave, env=env, cwd=cwd,
                         start_new_session=True, close_fds=True)
    os.close(slave)
    return p, master


def run_local(sid: str, s: dict):
    p, master = spawn_pty(["bash", "-c", "set -eo pipefail\n" + s["script"]], build_env(), str(ROOT))
    ACTIVE[sid] = {"proc": p, "master": master, "stopped": False}
    inter, svc = s.get("interaction"), s.get("service")
    state = {"url": None, "waiting": False, "deadline": 0.0, "up": False}
    t0 = time.time()

    def handle(line: str):
        line = line.rstrip()
        if not line.strip():
            return
        if line.startswith("::set "):
            apply_set(line[6:])
            log(sid, "set " + line[6:], "ctl")
            return
        log(sid, line)
        if inter:
            m = re.search(inter["url_re"], line)
            if m:
                state["url"] = m.group(0)
            if not state["waiting"] and re.search(inter["prompt_re"], line):
                state["waiting"], state["deadline"] = True, time.time() + HITL_TIMEOUT
                hitl = {"label": inter["label"], "url": state["url"], "prompt": redact(line)[:200], "since": time.time()}
                set_status(sid, "awaiting_human", hitl=hitl)
                log(sid, f"HITL requested: {inter['label']}", "hitl")
        if svc and not state["up"] and svc.get("ready_re") and re.search(svc["ready_re"], line):
            state["up"] = True
            set_status(sid, "up")

    buf, last = "", time.time()
    while True:
        r, _, _ = select.select([master], [], [], 0.5)
        if r:
            try:
                chunk = os.read(master, 4096)
            except OSError:
                chunk = b""
            if not chunk:
                break
            buf = ANSI.sub("", buf + chunk.decode("utf-8", "replace"))
            parts = re.split(r"\r\n|\n|\r", buf)
            buf = parts.pop()
            for line in parts:
                handle(line)
            last = time.time()
        else:
            if buf.strip() and time.time() - last > 0.6:  # prompts have no newline
                handle(buf)
                buf = ""
            if p.poll() is not None:
                break
        if state["waiting"] and STORE.step(sid)["status"] != "awaiting_human":
            state["waiting"] = False
        if state["waiting"] and time.time() > state["deadline"]:
            log(sid, "HITL timed out; stopping step", "hitl")
            ACTIVE[sid]["stopped"] = False
            try:
                os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            state["waiting"] = False
        if svc and not state["up"] and p.poll() is None and time.time() - t0 >= svc.get("ready_after", 5):
            state["up"] = True
            set_status(sid, "up")
    if buf.strip():
        handle(buf)
    rc = p.wait()
    try:
        os.close(master)
    except OSError:
        pass
    stopped = ACTIVE.pop(sid, {}).get("stopped", False)
    if stopped:
        log(sid, "stopped by user", "ctl")
        set_status(sid, "pending", exit=rc, hitl=None)
    elif svc:
        log(sid, f"service exited (code {rc})", "ctl")
        set_status(sid, "pending" if rc == 0 else "failed", exit=rc, hitl=None)
    elif rc == 0:
        log(sid, "step finished OK", "ctl")
        set_status(sid, "ok", exit=0, hitl=None)
    else:
        log(sid, f"step FAILED (exit {rc})", "ctl")
        set_status(sid, "failed", exit=rc, hitl=None)


# --------------------------------------------------------------------------- codespace (detached) runner
def cs_ssh(cmd: str, stdin: bytes | None = None, timeout: int = 90):
    argv = ["gh", "codespace", "ssh", "-c", STORE.cfg()["cs_name"], "--", cmd]
    return subprocess.run(argv, input=stdin, capture_output=True, timeout=timeout, env=build_env())


def cs_script(body: str) -> str:
    env = cfg_env()
    exports = "\n".join(f"export {k}={shlex.quote(v)}" for k, v in env.items() if v)
    repo = shlex.quote(STORE.cfg()["repo_name"])
    return (f"#!/usr/bin/env bash\nset -euo pipefail\n{exports}\nexport TERM=dumb NO_COLOR=1\n"
            f"export REPO_PATH=/workspaces/{repo}\n"
            f"if [ -f ~/.vision-infra.env ]; then source ~/.vision-infra.env; fi\n{body}\n")


def run_cs(sid: str, s: dict, resume: bool = False):
    st = STORE.step(sid)
    if not resume:
        up = cs_ssh(f"mkdir -p /tmp/jobs && cat > /tmp/jobs/{sid}.sh", stdin=cs_script(s["script"]).encode())
        if up.returncode != 0:
            log(sid, "upload failed: " + up.stderr.decode(errors="replace")[-300:], "err")
            set_status(sid, "failed", exit=up.returncode)
            return
        launch = (f"rm -f /tmp/jobs/{sid}.exit /tmp/jobs/{sid}.log; "
                  f"setsid nohup bash -c 'bash /tmp/jobs/{sid}.sh > /tmp/jobs/{sid}.log 2>&1; "
                  f"echo $? > /tmp/jobs/{sid}.exit' >/dev/null 2>&1 </dev/null & echo launched")
        la = cs_ssh(launch)
        if la.returncode != 0:
            log(sid, "launch failed: " + la.stderr.decode(errors="replace")[-300:], "err")
            set_status(sid, "failed", exit=la.returncode)
            return
        with STORE.lock:
            st["remote_off"], st["launched"] = 0, True
            STORE.save()
        log(sid, "job launched in Codespace (detached; survives disconnects)", "ctl")
    else:
        log(sid, "re-attaching to Codespace job", "ctl")
        set_status(sid, "running")

    fails = 0
    while True:
        off = st["remote_off"]
        cmd = (f"tail -c +{off + 1} /tmp/jobs/{sid}.log 2>/dev/null; echo; "
               f"echo __EXIT__$(cat /tmp/jobs/{sid}.exit 2>/dev/null)")
        try:
            r = cs_ssh(cmd, timeout=60)
            good = r.returncode == 0 and b"\n__EXIT__" in r.stdout
        except subprocess.TimeoutExpired:
            good = False
        if not good:
            fails += 1
            log(sid, f"connection to Codespace lost ({fails}/8); retrying", "ctl")
            if fails >= 8:
                log(sid, "giving up for now; the job may still be running. Use Reattach.", "ctl")
                set_status(sid, "detached")
                return
            time.sleep(min(5 * fails, 30))
            continue
        fails = 0
        out = r.stdout
        i = out.rfind(b"\n__EXIT__")
        content, code = out[:i], out[i + 9:].strip().decode(errors="replace")
        if not code:  # still running: only consume whole lines
            content = content[:content.rfind(b"\n") + 1]
        for line in ANSI.sub("", content.decode("utf-8", "replace")).splitlines():
            if line.strip():
                if line.startswith("::set "):
                    apply_set(line[6:])
                log(sid, line)
        with STORE.lock:
            st["remote_off"] = off + len(content)
            STORE.save()
        if code:
            rc = int(code) if code.lstrip("-").isdigit() else 1
            log(sid, "step finished OK" if rc == 0 else f"step FAILED (exit {rc})", "ctl")
            set_status(sid, "ok" if rc == 0 else "failed", exit=rc)
            return
        time.sleep(2.5)


# --------------------------------------------------------------------------- orchestration
def thread_main(sid: str, resume: bool = False):
    s = STEP_BY_ID[sid]
    try:
        if s["runner"] == "local":
            run_local(sid, s)
        else:
            run_cs(sid, s, resume)
    except Exception as e:  # noqa: BLE001
        log(sid, f"controller error: {e!r}", "err")
        ACTIVE.pop(sid, None)
        set_status(sid, "failed", exit=-1, hitl=None)


def deps_met(sid: str) -> list:
    return [d for d in STEP_BY_ID[sid]["deps"] if STORE.step(d)["status"] not in ("ok", "up")]


def api_error(code: int, msg: str):
    raise ApiError(code, msg)


class ApiError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code, self.msg = code, msg


def start_step(sid: str, force: bool = False, resume: bool = False):
    s = STEP_BY_ID.get(sid) or api_error(404, "unknown step")
    with STORE.lock:
        st = STORE.step(sid)
        if st["status"] in ("running", "awaiting_human", "up") and not resume:
            api_error(409, "already running")
        if resume:
            if st["status"] != "detached":
                api_error(409, "nothing to reattach")
        else:
            unmet = deps_met(sid)
            if unmet:
                api_error(409, "blocked by: " + ", ".join(unmet))
            if s.get("once") and st["status"] == "ok" and not force:
                api_error(409, "already done (use re-run)")
            if st["status"] == "detached":
                api_error(409, "job detached; reattach first")
        cfg = STORE.cfg()
        missing = [k for k in s.get("needs", []) if not cfg.get(k)]
        if missing:
            api_error(400, "set/obtain first: " + ", ".join(missing))
        if not resume:
            st.update(started=time.time(), ended=None, exit=None, hitl=None, note="")
            if s["runner"] == "cs":
                st["launched"] = False
    set_status(sid, "running")
    log(sid, ("— re-attach —" if resume else "— start —"), "ctl")
    threading.Thread(target=thread_main, args=(sid, resume), daemon=True).start()


def stop_step(sid: str):
    s = STEP_BY_ID.get(sid) or api_error(404, "unknown step")
    a = ACTIVE.get(sid)
    if a:
        a["stopped"] = True
        try:
            os.killpg(a["proc"].pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        return
    if s["runner"] == "cs":
        status = STORE.step(sid)["status"]
        if status in ("running", "detached"):
            cs_ssh(f"pkill -f '[b]ash /tmp/jobs/{sid}.sh' || true")
            log(sid, "stop signal sent to Codespace job", "ctl")
        elif s.get("stop"):
            r = cs_ssh("bash -s", stdin=cs_script(s["stop"]).encode())
            log(sid, "stopped" if r.returncode == 0 else "stop command failed", "ctl")
            set_status(sid, "pending")
        return
    api_error(409, "not running")


def submit_input(sid: str, text: str):
    st = STORE.step(sid)
    a = ACTIVE.get(sid)
    if st["status"] != "awaiting_human" or not a:
        api_error(409, "step is not waiting for input")
    if len(text) > 512 or "\n" in text or "\r" in text:
        api_error(400, "invalid input")
    os.write(a["master"], (text + "\n").encode())
    log(sid, "HITL resolved (input received; not logged)", "hitl")
    set_status(sid, "running", hitl=None)


def run_check(s: dict) -> bool:
    if s["runner"] == "local":
        r = subprocess.run(["bash", "-c", s["check"]], capture_output=True, timeout=45, env=build_env())
    else:
        r = cs_ssh("bash -s", stdin=cs_script(s["check"]).encode(), timeout=60)
    for line in r.stdout.decode(errors="replace").splitlines():
        if line.startswith("::set "):
            apply_set(line[6:])
    return r.returncode == 0


def refresh_checks():
    log("ctl", "refreshing state from live checks", "ctl")
    for s in STEPS:
        if not s.get("check"):
            continue
        sid, st, cfg = s["id"], None, STORE.cfg()
        st = STORE.step(sid)
        if st["status"] in ("running", "awaiting_human", "detached", "up"):
            continue
        if any(not cfg.get(k) for k in s.get("needs", [])) or (s["runner"] == "cs" and not cfg["cs_name"]):
            continue
        try:
            ok = run_check(s)
        except Exception as e:  # noqa: BLE001
            log("ctl", f"check {sid} error: {e!r}", "err")
            continue
        cur = st["status"]
        if ok and cur in ("pending", "failed"):
            set_status(sid, "ok", note="verified by live check")
        elif not ok and cur == "ok":
            set_status(sid, "pending", note="drift: live check failed")
    log("ctl", "refresh complete", "ctl")


def snapshot() -> dict:
    cfg = STORE.cfg()
    steps = []
    for s in STEPS:
        d = {"id": s["id"], "title": s["title"], "runner": s["runner"], "desc": s["desc"],
             "deps": s["deps"], "needs": s.get("needs", []), "once": bool(s.get("once")),
             "hitl": bool(s.get("interaction")), "service": bool(s.get("service")),
             "danger": bool(s.get("danger")),
             "can_stop": bool(s.get("service") or s.get("stop") or s["runner"] == "cs"),
             "blocked_by": deps_met(s["id"])}
        d.update(public_step(s["id"]))
        steps.append(d)
    return {"config": cfg, "steps": steps, "last_id": BUS.last_id()}


# --------------------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "vi-controller"

    def log_message(self, *a):  # silence default access log
        pass

    def _host_ok(self) -> bool:
        return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")

    def _auth(self) -> bool:
        if not self._host_ok():
            return False
        q = parse_qs(urlparse(self.path).query)
        tok = self.headers.get("X-Token") or (q.get("t") or [""])[0]
        return hmac.compare_digest(tok, TOKEN)

    def _origin_ok(self) -> bool:
        o = self.headers.get("Origin")
        if not o:
            return True
        return urlparse(o).hostname in ("127.0.0.1", "localhost")

    def _send(self, code: int, body: bytes, ctype: str = "application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj):
        self._send(code, json.dumps(obj).encode())

    def do_GET(self):
        path = urlparse(self.path).path
        if not self._host_ok():
            return self._json(403, {"error": "bad host"})
        if path == "/":
            f = ROOT / "dashboard.html"
            return self._send(200, f.read_bytes(), "text/html; charset=utf-8")
        if not self._auth():
            return self._json(401, {"error": "unauthorized"})
        if path == "/api/state":
            return self._json(200, snapshot())
        if path == "/api/events":
            return self._sse()
        self._json(404, {"error": "not found"})

    def _sse(self):
        q = parse_qs(urlparse(self.path).query)
        last = self.headers.get("Last-Event-ID") or (q.get("since") or ["0"])[0]
        last = int(last) if str(last).isdigit() else 0
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            while True:
                evs = BUS.since(last, 15)
                if not evs:
                    self.wfile.write(b": ping\n\n")
                for e in evs:
                    self.wfile.write(f"id: {e['id']}\ndata: {json.dumps(e)}\n\n".encode())
                    last = e["id"]
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return

    def do_POST(self):
        if not (self._auth() and self._origin_ok()):
            return self._json(401, {"error": "unauthorized"})
        n = int(self.headers.get("Content-Length") or 0)
        if n > 65536:
            return self._json(413, {"error": "too large"})
        try:
            body = json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "bad json"})
        parts = urlparse(self.path).path.strip("/").split("/")
        try:
            if parts == ["api", "config"]:
                return self._config(body)
            if parts == ["api", "refresh"]:
                threading.Thread(target=refresh_checks, daemon=True).start()
                return self._json(202, {"ok": True})
            if len(parts) == 4 and parts[:2] == ["api", "steps"]:
                sid, action = parts[2], parts[3]
                if action == "run":
                    start_step(sid, force=bool(body.get("force")))
                elif action == "reattach":
                    start_step(sid, resume=True)
                elif action == "stop":
                    stop_step(sid)
                elif action == "input":
                    submit_input(sid, str(body.get("text", "")))
                else:
                    api_error(404, "unknown action")
                return self._json(200, {"ok": True})
            api_error(404, "not found")
        except ApiError as e:
            self._json(e.code, {"error": e.msg})

    def _config(self, body: dict):
        with STORE.lock:
            for k, rx in VALID.items():
                if k in body:
                    v = str(body[k]).strip()
                    if v and not re.fullmatch(rx, v):
                        api_error(400, f"invalid {k}")
                    STORE.data["config"][k] = v
            STORE.save()
        BUS.publish("config", config=STORE.cfg())
        self._json(200, {"ok": True})


# --------------------------------------------------------------------------- startup
def load_token() -> str:
    tok = os.environ.get("GH_PAT") or os.environ.get("GH_TOKEN")
    if tok:
        return tok.strip()
    f = Path(os.environ.get("TOKEN_FILE", str(Path.home() / ".config/github/token.gpg")))
    if not f.exists():
        sys.exit(f"No token: export GH_PAT or create {f} (gpg-encrypted PAT: repo, workflow, codespace scopes).")
    gnupg = Path.home() / ".gnupg"
    gnupg.mkdir(mode=0o700, exist_ok=True)
    pin = shutil.which("pinentry-curses")
    conf = gnupg / "gpg-agent.conf"
    if pin and "pinentry-program" not in (conf.read_text() if conf.exists() else ""):
        with open(conf, "a") as fh:
            fh.write(f"pinentry-program {pin}\n")
        subprocess.run(["gpgconf", "--kill", "gpg-agent"], check=False)
    env = dict(os.environ)
    try:
        env["GPG_TTY"] = os.ttyname(0)
    except OSError:
        pass
    print(f"Decrypting {f} (enter passphrase when prompted)")
    r = subprocess.run(["gpg", "--decrypt", str(f)], capture_output=True, text=True, env=env)
    if r.returncode != 0 or not r.stdout.strip():
        sys.exit("gpg decrypt failed:\n" + r.stderr)
    return r.stdout.strip()


def replay_logs():
    rows = []
    if LOG_DIR.exists():
        for f in LOG_DIR.glob("*.jsonl"):
            try:
                for line in f.read_text(encoding="utf-8").splitlines()[-400:]:
                    rows.append(json.loads(line))
            except Exception:
                continue
    for r in sorted(rows, key=lambda x: x["ts"]):
        BUS.publish("log", ts=r["ts"], step=r["step"], stream=r.get("stream", "out"), text=r["text"], replay=True)


def recover():
    for s in STEPS:
        sid, st = s["id"], STORE.step(s["id"])
        if st["status"] in ("running", "awaiting_human", "up"):
            if s["runner"] == "cs" and st.get("launched") and st["status"] == "running":
                log(sid, "controller restarted; resuming detached job", "ctl")
                threading.Thread(target=thread_main, args=(sid, True), daemon=True).start()
            elif s.get("service"):
                set_status(sid, "pending", note="controller restarted")
            else:
                log(sid, "controller restarted while step was running", "ctl")
                set_status(sid, "failed", note="controller restarted")


def main():
    global TOKEN, GH_TOKEN
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-open", action="store_true")
    args = ap.parse_args()

    GH_TOKEN = load_token()
    EXTRA_SECRETS.add(GH_TOKEN)
    TOKEN = secrets.token_urlsafe(24)
    if shutil.which("termux-wake-lock"):
        subprocess.run(["termux-wake-lock"], check=False)

    replay_logs()
    recover()
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    srv.daemon_threads = True
    url = f"http://127.0.0.1:{args.port}/?t={TOKEN}"
    print(f"\nDashboard: {url}\n(Ctrl-C to stop; detached Codespace jobs keep running)\n")
    if not args.no_open and shutil.which("termux-open-url"):
        subprocess.run(["termux-open-url", url], check=False)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for a in list(ACTIVE.values()):
            try:
                os.killpg(a["proc"].pid, signal.SIGTERM)
            except Exception:
                pass


if __name__ == "__main__":
    main()

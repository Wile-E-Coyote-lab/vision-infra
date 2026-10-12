"""Boundary tests: hostile input must not cross a trust boundary. Stdlib unittest, no network."""
import importlib.util
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["VI_HOME"] = tempfile.mkdtemp(prefix="vi-test-")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


C = _load("vi_controller", ROOT / "controller.py")
V = _load("vi_validate", ROOT / "tools" / "validate.py")


class SetChannel(unittest.TestCase):
    HOSTILE = ["cs_name=a b", "cs_name=../x", "cs_name=", "cs_name=" + "a" * 101, "owner=x;rm -rf /",
               "owner=$(id)", "owner=`id`", "cs_name=ünï", "evil=1", "cs_name$IFS=x", "=x", "noequals"]

    def test_hostile_values_rejected(self):
        for kv in self.HOSTILE:
            self.assertFalse(C.apply_set(kv, ["cs_name", "owner"], "t"), kv)

    def test_undeclared_key_rejected(self):
        self.assertFalse(C.apply_set("cs_name=ok-name", [], "t"))

    def test_declared_key_accepted(self):
        self.assertTrue(C.apply_set("cs_name=fuzzy-space-abc123", ["cs_name"], "t"))
        self.assertEqual(C.STORE.cfg()["cs_name"], "fuzzy-space-abc123")


class ConfigValidation(unittest.TestCase):
    BAD = {"project_id": ["x;rm", "UPPER", "a"], "zone": ["us-central1-a; id", "x"],
           "repo_name": ["a b", "a;b", "../x"], "instance": ["A", "a_b", "x y"], "cs_machine": ["a;b", "x"]}

    def test_rejects_injection(self):
        for k, vals in self.BAD.items():
            for val in vals:
                self.assertIsNone(re.fullmatch(C.VALID[k], val), (k, val))


class UrlPatterns(unittest.TestCase):
    rx = re.compile(C.INTER_CONFIRM["url_re"])

    def test_lookalikes_do_not_match(self):
        for u in ["https://github.com.evil.example/settings/tokens", "http://github.com/settings/tokens",
                  "https://evilgithub.com/settings/tokens", "https://github.co/settings/tokens"]:
            self.assertIsNone(self.rx.search(u), u)

    def test_genuine_matches(self):
        self.assertTrue(self.rx.search("open https://github.com/settings/tokens now"))


class Redaction(unittest.TestCase):
    def test_secrets_removed(self):
        for s in ["ghp_" + "A" * 36, "github_pat_" + "B" * 30, "ya29." + "c" * 40,
                  "-----BEGIN OPENSSH PRIVATE KEY-----", "Authorization: Bearer abc123def"]:
            out = C.redact("x " + s + " y")
            self.assertNotIn(s.split(": ")[-1], out.replace("***", ""), s)


class Ledger(unittest.TestCase):
    def setUp(self):
        self.old = C.LEDGER_FILE
        C.LEDGER_FILE = Path(tempfile.mkdtemp()) / "ledger.jsonl"
        C._LEDGER_PREV[0] = None

    def tearDown(self):
        C.LEDGER_FILE = self.old
        C._LEDGER_PREV[0] = None

    def test_chain_verifies_and_detects_tamper(self):
        for i in range(4):
            C.ledger_append("t", n=i)
        self.assertEqual(C.verify_ledger()[:2], (True, 4))
        lines = C.LEDGER_FILE.read_text().splitlines()
        C.LEDGER_FILE.write_text("\n".join([lines[0], lines[1].replace('"n": 1', '"n": 9'), *lines[2:]]) + "\n")
        self.assertFalse(C.verify_ledger()[0])

    def test_deleted_record_detected(self):
        for i in range(4):
            C.ledger_append("t", n=i)
        lines = C.LEDGER_FILE.read_text().splitlines()
        C.LEDGER_FILE.write_text("\n".join([lines[0], lines[2], lines[3]]) + "\n")
        self.assertFalse(C.verify_ledger()[0])


class RegistryPolicy(unittest.TestCase):
    CK, SK = {"owner", "cs_name"}, {"owner", "cs_name"}

    def base(self, **kw):
        s = dict(id="demo", title="t", runner="local", deps=[], desc="d", script="echo ok\n", effect="read")
        s.update(kw)
        return s

    def rules(self, *steps):
        return {x.split()[0] for x in V.validate(list(steps), self.CK, self.SK)}

    def test_real_registry_is_clean(self):
        self.assertEqual(V.validate(C.STEPS, set(C.DEFAULT_CFG), set(C.SET_KEYS)), [])

    def test_seeded_violations_are_caught(self):
        cases = {
            "R001": self.base(bogus=1),
            "R002": self.base(deps=["nope"]),
            "R003": self.base(effect="destructive"),
            "R004": self.base(script="gcloud compute instances list\n"),
            "R005": self.base(script='eval "$x"\n'),
            "R006": self.base(script='echo "$GH_TOKEN"\n'),
            "R007": self.base(script="echo '::set evil=1'\n"),
            "R008": self.base(script="if then\n"),
            "R009": self.base(interaction={"url_re": "(", "prompt_re": "x"}),
            "R010": self.base(needs=["ghost"]),
        }
        for rule, step in cases.items():
            self.assertIn(rule, self.rules(step), rule)

    def test_token_never_in_codespace_scripts(self):
        self.assertIn("R006", self.rules(self.base(runner="cs", script='x="$GH_PAT"\n')))

    def test_cycle_detected(self):
        a, b = self.base(id="aa", deps=["bb"]), self.base(id="bb", deps=["aa"])
        self.assertIn("R002", self.rules(a, b))


class IdentityPolicy(unittest.TestCase):
    def ident(self, **spec):
        base = {"egress": [{"host": "github.com", "lifecycle": "active", "review_by": "2999-01-01"}],
                "images": [], "mcp_servers": [], "rag_sources": []}
        base.update(spec)
        return {"spec": base}

    def rules(self, ident, texts):
        v, w = V.check_identities(ident, texts)
        return {x.split()[0] for x in v}, w

    def test_real_identities_are_clean(self):
        import json
        ident = json.loads((ROOT / "registry" / "identities.yaml").read_text())
        v, _ = V.check_identities(ident, V.scan_texts(C.STEPS))
        self.assertEqual(v, [])

    def test_unregistered_egress_host_denied(self):
        self.assertIn("R012", self.rules(self.ident(), {"s": "curl https://evil.example/x"})[0])
        self.assertNotIn("R012", self.rules(self.ident(), {"s": "curl https://github.com/x"})[0])

    def test_unregistered_and_stale_images(self):
        good = {"id": "i", "ref": "a/b:1", "pin": None, "lifecycle": "active", "review_by": "2999-01-01"}
        self.assertIn("R014", self.rules(self.ident(), {"s": 'IMAGE="a/b:1"'})[0])
        self.assertIn("R013", self.rules(self.ident(images=[good]), {"s": "echo nothing"})[0])
        rules, warns = self.rules(self.ident(images=[good]), {"s": 'IMAGE="a/b:1"'})
        self.assertEqual(rules, set())
        self.assertTrue(any("unpinned" in x for x in warns))

    def test_bad_pin_rejected(self):
        bad = {"id": "i", "ref": "a/b:1", "pin": "sha256:xyz", "lifecycle": "active", "review_by": "2999-01-01"}
        self.assertIn("R013", self.rules(self.ident(images=[bad]), {"s": "a/b:1"})[0])

    def test_mcp_default_deny_shape(self):
        ok = {"namespace": "io.github.owner/server", "version": "1.0.0", "pin": "a" * 40,
              "effects": ["read"], "gate": "hitl", "lifecycle": "active", "review_by": "2999-01-01"}
        self.assertEqual(self.rules(self.ident(mcp_servers=[ok]), {})[0], set())
        for patch in ({"gate": "allow"}, {"pin": "latest"}, {"effects": ["root"]}, {"namespace": "no-slash"}):
            self.assertIn("R013", self.rules(self.ident(mcp_servers=[{**ok, **patch}]), {})[0], patch)

    def test_rag_content_never_has_authority(self):
        r = {"id": "docs", "uri": "https://github.com/x", "authority": "tool", "lifecycle": "active", "review_by": "2999-01-01"}
        self.assertIn("R013", self.rules(self.ident(rag_sources=[r]), {})[0])

    def test_overdue_review_warns(self):
        old = {"host": "github.com", "lifecycle": "active", "review_by": "2000-01-01"}
        rules, warns = self.rules(self.ident(egress=[old]), {})
        self.assertEqual(rules, set())
        self.assertTrue(any("overdue" in x for x in warns))


class Docs(unittest.TestCase):
    """Makes the 'valid frontmatter / strict headers / ENUM values' claims machine-checked."""
    PATH = ROOT / "docs" / "ARCHITECTURE.md"

    def test_frontmatter_headers_enums(self):
        text = self.PATH.read_text()
        self.assertTrue(text.startswith("---\n"))
        end = text.index("\n---\n", 4)
        front = text[4:end]
        for key in ("title:", "status:", "supersedes:"):
            self.assertIn(key, front)
        prev = 0
        for line in text[end:].splitlines():
            m = re.match(r"(#+) ", line)
            if m:
                self.assertLessEqual(len(m.group(1)), prev + 1, line)
                prev = len(m.group(1))
        blocks, cur = [], []
        for l in text.splitlines():
            if l.startswith("|"):
                cur.append(l)
            elif cur:
                blocks.append(cur)
                cur = []
        if cur:
            blocks.append(cur)
        for block in blocks:
            header = [c.strip() for c in block[0].strip("|").split("|")]
            if "Decision" in header:
                col = header.index("Decision")
                for r in block[2:]:
                    self.assertIn([c.strip() for c in r.strip("|").split("|")][col], {"allow", "deny", "hitl"}, r)


class Dashboard(unittest.TestCase):
    def test_logs_rendered_as_text_only(self):
        html = (ROOT / "dashboard.html").read_text()
        self.assertNotIn("innerHTML", html)
        self.assertNotIn("eval(", html)


if __name__ == "__main__":
    unittest.main()

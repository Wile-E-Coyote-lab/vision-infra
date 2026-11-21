import json
import pathlib
import unittest

class TestManifest(unittest.TestCase):
    def test_manifest_structure(self):
        p = pathlib.Path("docs/manifest.json")
        self.assertTrue(p.exists())
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertIsInstance(data.get("scenes"), list)

if __name__ == "__main__":
    unittest.main()

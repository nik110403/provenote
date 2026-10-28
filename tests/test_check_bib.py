import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/check-bib"

GOOD = """@article{a2020x,
  author = {Doe, Jane}, title = {A {Title}}, year = {2020},
  doi = {10.1234/abc.5}
}
@book{b2021y, author = "Roe, R.", title = "Book", year = 2021}
"""


class CheckBib(unittest.TestCase):
    def run_tool(self, bib, paper="Text [@a2020x; @b2021y].\n"):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "r.bib").write_text(bib, encoding="utf-8")
            (root / "p.md").write_text(paper, encoding="utf-8")
            return subprocess.run([sys.executable, str(TOOL), str(root / "r.bib"), str(root / "p.md")],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_clean(self):
        r = self.run_tool(GOOD)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("2 entries, 0 errors", r.stdout)

    def test_duplicate_key(self):
        r = self.run_tool(GOOD + "@misc{a2020x, author={X}, title={T}, year={2000}}\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn("duplicate key: a2020x", r.stdout)

    def test_missing_fields(self):
        r = self.run_tool("@article{k, title={T}}\n", "[@k]")
        self.assertEqual(r.returncode, 1)
        self.assertIn("k: missing author", r.stdout)
        self.assertIn("k: missing year", r.stdout)
        self.assertNotIn("k: missing title", r.stdout)

    def test_bad_doi(self):
        r = self.run_tool("@article{k, author={A}, title={T}, year={1}, doi={https://doi.org/10.1/x}}\n", "[@k]")
        self.assertEqual(r.returncode, 1)
        self.assertIn("malformed DOI", r.stdout)

    def test_cited_missing_and_uncited(self):
        r = self.run_tool(GOOD, "Only [@a2020x] and [@ghost]. mail me" + "@" + "mailbox.invalid <!-- @hidden -->")
        self.assertEqual(r.returncode, 1)
        self.assertIn("cited but not in bib: ghost", r.stdout)
        self.assertNotIn("hidden", r.stdout)
        self.assertNotIn("mailbox", r.stdout)
        self.assertIn("NOTE  in bib but never cited: b2021y", r.stdout)

    def test_uncited_only_is_ok(self):
        r = self.run_tool(GOOD, "[@a2020x]")
        self.assertEqual(r.returncode, 0)

    def test_missing_bib_usage_error(self):
        r = subprocess.run([sys.executable, str(TOOL), "/nonexistent.bib"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

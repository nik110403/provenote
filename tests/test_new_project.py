import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/new-project"
DIRS = ["00_admin", "01_notes", "02_sources", "03_code", "05_figures",
        "06_tables", "07_references", "10_paper"]
SUBDIRS = ["02_sources/pdf", "01_notes/lit"]
FILES = ["CLAUDE.md", "00_admin/TASKLIST.md", "00_admin/progress.md",
         "01_notes/open_questions.md", "07_references/references.bib"]


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


class NewProject(unittest.TestCase):
    def test_creates_tree(self):
        with tempfile.TemporaryDirectory() as t:
            target = Path(t) / "proj"
            r = run(str(target))
            self.assertEqual(r.returncode, 0, r.stderr)
            for d in DIRS:
                self.assertTrue((target / d).is_dir(), d)
            for d in SUBDIRS:
                self.assertTrue((target / d / ".gitkeep").is_file(), d)
            for f in FILES:
                self.assertTrue((target / f).is_file(), f)
            self.assertIn("## Resume here", (target / "00_admin/TASKLIST.md").read_text(encoding="utf-8"))
            self.assertEqual((target / "07_references/references.bib").read_text(encoding="utf-8"), "")

    def test_accepts_empty_existing_dir(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(run(t).returncode, 0)

    def test_refuses_non_empty_dir(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "keep.txt").write_text("x", encoding="utf-8")
            r = run(t)
            self.assertEqual(r.returncode, 1)
            self.assertIn("not empty", r.stderr)
            self.assertEqual([p.name for p in Path(t).iterdir()], ["keep.txt"])

    def test_refuses_file_target(self):
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "f"
            f.write_text("x", encoding="utf-8")
            self.assertEqual(run(str(f)).returncode, 1)

    def test_usage(self):
        self.assertEqual(run().returncode, 2)


if __name__ == "__main__":
    unittest.main()

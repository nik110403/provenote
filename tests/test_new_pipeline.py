import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/new-pipeline"


def run(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


class NewPipeline(unittest.TestCase):
    def test_scaffolds_python(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "p"
            r = run(str(d), "--lang", "python")
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ["run_all.py", "pyproject.toml", "src/01_demo.py", "data/raw/MANIFEST.md"]:
                self.assertTrue((d / f).is_file(), f)
            for sub in ["output/figures", "output/tables"]:
                self.assertTrue((d / sub).is_dir(), sub)

    def test_scaffolds_r(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "p"
            r = run(str(d), "--lang", "r")
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ["run_all.R", "src/01_demo.R", "data/raw/MANIFEST.md", "README.md"]:
                self.assertTrue((d / f).is_file(), f)
            self.assertIn("renv", (d / "README.md").read_text(encoding="utf-8"))

    def test_python_demo_runs_end_to_end(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "p"
            self.assertEqual(run(str(d), "--lang", "python").returncode, 0)
            cmd = ["uv", "run", "python", "run_all.py"] if shutil.which("uv") \
                else [sys.executable, "run_all.py"]
            r = subprocess.run(cmd, cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)
            self.assertIn("key,value", (d / "output/tables/demo_sum.csv").read_text(encoding="utf-8"))

    def test_failing_step_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "p"
            run(str(d), "--lang", "python")
            (d / "src/02_bad.py").write_text("raise SystemExit(3)\n", encoding="utf-8")
            r = subprocess.run([sys.executable, "run_all.py"], cwd=d, capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(r.returncode, 1)
            self.assertIn("FAIL", r.stdout)

    def test_refuses_non_empty_and_usage(self):
        with tempfile.TemporaryDirectory() as t:
            (Path(t) / "keep").write_text("x", encoding="utf-8")
            self.assertEqual(run(t, "--lang", "python").returncode, 1)
        self.assertEqual(run().returncode, 2)
        self.assertEqual(run("x", "--lang", "go").returncode, 2)

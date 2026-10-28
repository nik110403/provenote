import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LINT = Path(__file__).resolve().parent.parent / "scripts/lint-skills.py"


class LintSkills(unittest.TestCase):
    def lint(self, front):
        with tempfile.TemporaryDirectory() as t:
            d = Path(t) / "plugins/provenote/skills/demo"
            d.mkdir(parents=True)
            (d / "SKILL.md").write_bytes(f"---\n{front}\n---\nbody\n".encode("utf-8"))
            return subprocess.run([sys.executable, str(LINT), t], capture_output=True, text=True)

    def test_plain_description_passes(self):
        self.assertEqual(self.lint("name: demo\ndescription: Does a thing").returncode, 0)

    def test_folded_description_with_body_passes(self):
        self.assertEqual(self.lint("name: demo\ndescription: >\n  Does a thing\n  over two lines").returncode, 0)

    def test_empty_block_scalars_fail(self):
        for ind in (">", "|", ">-", "|+"):
            r = self.lint(f"name: demo\ndescription: {ind}")
            self.assertEqual(r.returncode, 1, ind + r.stdout)
            r = self.lint(f"description: {ind}\n\nname: demo")
            self.assertEqual(r.returncode, 1, ind + r.stdout)
            r = self.lint(f"name: demo\ndescription: {ind}\nother: x")
            self.assertEqual(r.returncode, 1, ind + r.stdout)


if __name__ == "__main__":
    unittest.main()

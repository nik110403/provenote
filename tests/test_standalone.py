import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import shutil

BIN = Path(__file__).resolve().parent.parent / "plugins/provenote/bin"


class Standalone(unittest.TestCase):
    def test_help_works_from_a_lone_copy(self):
        tools = sorted(p for p in BIN.iterdir() if p.is_file())
        self.assertTrue(tools)
        for tool in tools:
            with self.subTest(tool=tool.name), tempfile.TemporaryDirectory() as t:
                shutil.copy2(tool, t)
                r = subprocess.run(
                    [sys.executable, str(Path(t) / tool.name), "--help"],
                    cwd=t,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue(r.stdout.strip())
                self.assertEqual(sorted(p.name for p in Path(t).iterdir()), [tool.name])


if __name__ == "__main__":
    unittest.main()

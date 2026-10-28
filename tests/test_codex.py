import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INSTALL = ROOT / "scripts/install-codex.py"


class CodexInstall(unittest.TestCase):
    def install(self, project):
        return subprocess.run(
            [sys.executable, str(INSTALL), "--project", str(project)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_complete_install_and_identical_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project with spaces"
            project.mkdir()
            first = self.install(project)
            self.assertEqual(first.returncode, 0, first.stderr)
            skill = project / ".agents/skills/provenote"
            for name in (
                "SKILL.md",
                "bin/verify-quotes",
                "templates/project",
                "agents/source-reader.md",
                "workflows/literature-notes/SKILL.md",
            ):
                self.assertTrue((skill / name).exists(), name)
            for helper in (skill / "bin").iterdir():
                if helper.is_file():
                    help_result = subprocess.run(
                        [sys.executable, str(helper), "--help"],
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertEqual(
                        help_result.returncode, 0, helper.name + help_result.stderr
                    )
            second = self.install(project)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertIn("already installed", second.stdout)

    def test_collision_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            target = project / ".agents/skills/provenote"
            target.mkdir(parents=True)
            marker = target / "marker"
            marker.write_text("keep", encoding="utf-8")
            result = self.install(project)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_symlink_destination_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            (project / ".agents/skills").mkdir(parents=True)
            try:
                os.symlink(project, project / ".agents/skills/provenote")
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            result = self.install(project)
            self.assertEqual(result.returncode, 2)

    def test_symlink_ancestor_is_refused_without_writing_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "target"
            target.mkdir()
            alias = root / "alias"
            try:
                os.symlink(target, alias, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlink creation unavailable: {error}")
            result = self.install(alias)
            self.assertEqual(result.returncode, 2)
            self.assertFalse((target / ".agents").exists())

    @unittest.skipUnless(sys.platform == "darwin", "macOS system alias")
    def test_macos_var_temp_alias_is_allowed(self):
        with tempfile.TemporaryDirectory(dir="/var/tmp") as temp:
            self.assertTrue(Path(temp).is_relative_to("/var"))
            project = Path(temp) / "project"
            project.mkdir()
            result = self.install(project)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_installed_helper_verifies_clean_example(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            self.assertEqual(self.install(project).returncode, 0)
            example = project / "example"
            shutil.copytree(ROOT / "examples/basic", example)
            helper = project / ".agents/skills/provenote/bin/verify-quotes"
            result = subprocess.run(
                [
                    sys.executable,
                    str(helper),
                    "--strict",
                    "01_notes/lit/lei2023financial.md",
                ],
                cwd=example,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()

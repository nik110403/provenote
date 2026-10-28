import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "plugins/provenote/bin/doctor"
loader = importlib.machinery.SourceFileLoader("doctor", str(TOOL))
spec = importlib.util.spec_from_loader(loader.name, loader)
doctor = importlib.util.module_from_spec(spec)
loader.exec_module(doctor)


class Doctor(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        self.which = stack.enter_context(
            patch.object(doctor.shutil, "which", return_value=None)
        )
        stack.enter_context(patch.object(doctor.sys, "platform", "linux"))

    def findings(self, workflow="all"):
        return doctor.diagnose(workflow, self.project)["findings"]

    def ids(self, workflow="all"):
        return [finding["id"] for finding in self.findings(workflow)]

    def test_missing_tools_and_exact_package_fixes(self):
        findings = self.findings()
        self.assertEqual(
            [f["id"] for f in findings], ["pdftotext.missing", "pandoc.missing"]
        )
        self.assertEqual(
            findings[0]["fixes"],
            {
                "windows": "winget install oschwartz10612.Poppler OR choco install poppler",
                "macos": "brew install poppler",
                "linux": "apt install poppler-utils OR dnf install poppler-utils",
            },
        )
        self.assertEqual(
            findings[1]["fixes"],
            {
                "windows": "winget install JohnMacFarlane.Pandoc OR choco install pandoc",
                "macos": "brew install pandoc",
                "linux": "apt install pandoc OR dnf install pandoc",
            },
        )
        for finding in findings:
            self.assertEqual(finding["severity"], "error")
            self.assertTrue(finding["evidence"])

    def test_workflow_prerequisites(self):
        self.assertEqual(self.ids("pdf"), ["pdftotext.missing"])
        self.assertEqual(self.ids("build"), ["pandoc.missing"])
        self.assertEqual(self.ids("word"), [])

    def test_python_too_old(self):
        with (
            patch.object(doctor.sys, "version_info", (3, 8)),
            patch.object(doctor.sys, "version", "3.8.0"),
        ):
            self.assertEqual(self.ids("word"), ["python.too-old"])
            self.assertIn("winget", self.findings("word")[0]["fixes"]["windows"])

    def test_versions_and_bound_probes(self):
        self.which.side_effect = lambda name: (
            "/tools/" + name if name in ("pdftotext", "pandoc") else None
        )
        for version, expected in (
            ("pandoc 2.10", ["pandoc.too-old"]),
            ("pandoc 2.11.4", []),
            ("unrecognized", ["pandoc.version-unknown"]),
        ):
            with (
                self.subTest(version=version),
                patch.object(
                    doctor.subprocess,
                    "run",
                    return_value=subprocess.CompletedProcess([], 0, version, ""),
                ) as run,
            ):
                self.assertEqual(self.ids("build"), expected)
                self.assertEqual(run.call_args.kwargs["timeout"], 3)
                self.assertFalse(run.call_args.kwargs["shell"])
                self.assertEqual(run.call_args.args[0], ["/tools/pandoc", "--version"])
        for error in (
            subprocess.TimeoutExpired("pandoc", 3),
            OSError("not executable"),
        ):
            with patch.object(doctor.subprocess, "run", side_effect=error):
                self.assertEqual(self.ids("build"), ["pandoc.unusable"])

    def test_typst_requires_pandoc_3_1(self):
        self.which.side_effect = lambda name: (
            "/tools/" + name if name in ("pandoc", "typst") else None
        )
        with patch.object(doctor, "tool_version", return_value=("pandoc 3.0", None)):
            finding = self.findings("build")[0]
            self.assertEqual(finding["id"], "pandoc.too-old")
            self.assertIn("3.1", finding["evidence"])

    def test_healthy_zero_and_repeatable_json(self):
        self.which.side_effect = lambda name: (
            "/tools/" + name if name in ("pandoc", "pdftotext") else None
        )
        with (
            patch.object(
                doctor,
                "tool_version",
                side_effect=lambda path, flag: (
                    "pandoc 3.1" if flag == "--version" else "pdftotext version 24",
                    None,
                ),
            ),
            patch.object(doctor.Path, "cwd", return_value=self.project),
        ):
            outputs = []
            for _ in range(2):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(doctor.main(["--json"]), 0)
                outputs.append(output.getvalue())
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(
                json.loads(outputs[0]),
                {"schema_version": 1, "workflow": "all", "findings": []},
            )

    def test_windows_stub_and_non_utf8(self):
        self.which.side_effect = lambda name: (
            r"C:\Windows\System32\bash.exe" if name == "bash" else None
        )
        with (
            patch.object(doctor.sys, "platform", "win32"),
            patch.dict(os.environ, {"SystemRoot": r"C:\Windows"}),
            patch.object(
                doctor.sys, "stdout", type("Stream", (), {"encoding": "cp1252"})()
            ),
            patch.object(
                doctor.sys, "stderr", type("Stream", (), {"encoding": "ascii"})()
            ),
        ):
            findings = self.findings("word")
        self.assertEqual(
            [f["id"] for f in findings], ["path.windows-bash-stub", "console.non-utf8"]
        )
        self.assertIn("do not use the System32 stub", findings[0]["fixes"]["windows"])
        self.assertIn("PYTHONIOENCODING='utf-8'", findings[1]["fixes"]["windows"])
        self.assertEqual(set(findings[1]["fixes"]), {"windows", "macos", "linux"})

    def test_helper_shadow(self):
        self.which.side_effect = lambda name: (
            "/other/check-docx" if name == "check-docx" else None
        )
        self.assertEqual(self.ids("word"), ["path.helper-shadowed"])
        self.which.side_effect = lambda name: (
            "/other/new-project" if name == "new-project" else None
        )
        self.assertEqual(self.ids("word"), ["path.helper-shadowed"])

    def test_adapter_only_compares_proven_existing_helpers(self):
        adapter = self.project / ".agents/skills/provenote/bin"
        adapter.mkdir(parents=True)
        # Missing files are not proof of a stale copy (e.g. an older inventory).
        self.assertEqual(self.ids("word"), [])
        (adapter / "check-docx").write_text("stale", encoding="utf-8")
        self.assertEqual(self.ids("word"), ["adapter.stale-helper"])
        with patch.object(doctor, "__file__", str(adapter / "doctor")):
            self.assertEqual(self.ids("word"), [])
        (adapter / "check-docx").write_bytes((TOOL.parent / "check-docx").read_bytes())
        self.assertEqual(self.ids("word"), [])

    def test_unwritable_nested_directory_without_write_probe(self):
        nested = self.project / "02_sources/md"
        nested.mkdir(parents=True)
        with (
            patch.object(
                doctor.os, "access", side_effect=lambda path, mode: Path(path) != nested
            ),
            patch.object(
                doctor.Path, "write_text", side_effect=AssertionError("write probe")
            ),
            patch.object(
                doctor.Path, "touch", side_effect=AssertionError("write probe")
            ),
        ):
            findings = self.findings("pdf")
        self.assertEqual(
            [f["id"] for f in findings], ["pdftotext.missing", "project.not-writable"]
        )
        self.assertIn(str(nested), findings[-1]["evidence"])

    def test_verification_failure_is_not_setup(self):
        (self.project / "01_notes").mkdir()
        (self.project / "01_notes/bad.md").write_text(
            "FAIL: fabricated quotation; wrong hash and binding", encoding="utf-8"
        )
        (self.project / "build.log").write_text(
            "guard FAILED: unresolved citations", encoding="utf-8"
        )
        self.assertEqual(self.ids("word"), [])

    def test_cli_fake_empty_path_and_json_exit(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), "--workflow", "pdf", "--json"],
            cwd=self.project,
            env={**os.environ, "PATH": str(self.project), "PYTHONIOENCODING": "utf-8"},
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(
            [f["id"] for f in json.loads(result.stdout)["findings"]],
            ["pdftotext.missing"],
        )


if __name__ == "__main__":
    unittest.main()

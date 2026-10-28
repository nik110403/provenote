#!/usr/bin/env python3
"""Run a portable smoke test against a fresh copy of the bundled example."""

import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def documented_launcher():
    if sys.platform != "win32":
        if shutil.which("python3"):
            return ["python3"]
        raise SystemExit("smoke: python3 is required on non-Windows platforms")
    if shutil.which("python"):
        return ["python"]
    if shutil.which("py"):
        return ["py", "-3"]
    raise SystemExit("smoke: Windows requires python or py -3 on PATH")


def run(command, *, cwd):
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        raise SystemExit(
            f"smoke: {' '.join(map(str, command))} exited {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def main():
    if not shutil.which("pandoc") or not shutil.which("pdftotext"):
        raise SystemExit("smoke: pandoc and pdftotext are required")
    launcher = documented_launcher()
    with tempfile.TemporaryDirectory() as temp:
        example = Path(temp) / "basic"
        shutil.copytree(ROOT / "examples/basic", example)
        paper_dir = example / "10_paper"
        paper_dir.mkdir(exist_ok=True)
        (paper_dir / "paper.md").write_text("# Smoke test\n", encoding="utf-8")
        verified = run(
            [
                *launcher,
                str(ROOT / "plugins/provenote/bin/verify-quotes"),
                "--strict",
                "01_notes/lit/lei2023financial.md",
            ],
            cwd=example,
        )
        if "PASS" not in verified.stdout:
            raise SystemExit("smoke: known-good quote did not pass")
        run(
            [
                *launcher,
                str(ROOT / "plugins/provenote/bin/build-paper"),
                "--to",
                "html",
            ],
            cwd=example,
        )
        if not (paper_dir / "paper.html").is_file():
            raise SystemExit("smoke: HTML build was not created")
        reference = Path(temp) / "reference style ü.docx"
        run(
            [
                "pandoc",
                "-o",
                str(reference),
                "--print-default-data-file",
                "reference.docx",
            ],
            cwd=example,
        )
        run(
            [
                *launcher,
                str(ROOT / "plugins/provenote/bin/build-paper"),
                "--to",
                "docx",
                "--reference-doc",
                str(reference),
            ],
            cwd=example,
        )
        output = paper_dir / "paper.docx"
        try:
            with zipfile.ZipFile(output) as archive:
                if archive.testzip() is not None:
                    raise ValueError("corrupt archive member")
                document = archive.read("word/document.xml").decode("utf-8")
        except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as error:
            raise SystemExit(f"smoke: DOCX export is invalid: {error}") from error
        if "Smoke test" not in document:
            raise SystemExit("smoke: DOCX export omitted known paper text")
        word_demo = Path(temp) / "Word demo ü"
        demo = run(
            [*launcher, str(ROOT / "examples/word/RUN.py"), "--out", str(word_demo)],
            cwd=ROOT,
        )
        if "demo retained at" not in demo.stdout:
            raise SystemExit(
                "smoke: Word demo did not complete its clean and fabricated checks"
            )
    print("smoke: PASS")


if __name__ == "__main__":
    main()

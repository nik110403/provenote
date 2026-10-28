import sys
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "plugins/provenote/bin/build-paper"
TEMPLATE = ROOT / "plugins/provenote/templates/project"

BIB = "@article{a2020x, author={Doe, Jane}, title={Title}, journal={J}, year={2020}}\n"


@unittest.skipUnless(shutil.which("pandoc"), "pandoc not installed")
class BuildPaper(unittest.TestCase):
    def project(self, paper):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        root = Path(t.name) / "p"
        shutil.copytree(TEMPLATE, root)
        (root / "07_references/references.bib").write_text(BIB, encoding="utf-8")
        if paper is not None:
            (root / "10_paper/paper.md").write_text(paper, encoding="utf-8")
        return root

    def build(self, root, *args):
        return subprocess.run(
            [sys.executable, str(TOOL), *args],
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def out(self, root):
        return list((root / "10_paper").glob("paper.pdf")) + list(
            (root / "10_paper").glob("paper.html")
        )

    def default_reference(self, path):
        result = subprocess.run(
            ["pandoc", "-o", str(path), "--print-default-data-file", "reference.docx"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def customize_reference(self, path):
        self.default_reference(path)
        with zipfile.ZipFile(path) as archive:
            contents = {
                info.filename: archive.read(info.filename)
                for info in archive.infolist()
            }
        styles = contents["word/styles.xml"].decode("utf-8")
        self.assertIn('w:val="4F81BD"', styles)
        contents["word/styles.xml"] = styles.replace(
            'w:val="4F81BD"', 'w:val="A1B2C3"', 1
        ).encode("utf-8")
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for name, content in contents.items():
                archive.writestr(name, content)

    def docx_part(self, path, name):
        with zipfile.ZipFile(path) as archive:
            return archive.read(name).decode("utf-8", errors="replace")

    def test_good_build(self):
        root = self.project("# Intro\n\nAs shown by @a2020x.\n")
        r = self.build(root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(self.out(root))
        self.assertIn("pandoc:", r.stdout)

    def test_template_builds(self):
        r = self.build(self.project(None))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_unresolved_citation_fails(self):
        r = self.build(self.project("# Intro\n\nSee [@ghost].\n"))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("unresolved citations", r.stderr)

    def test_triple_question_marks_fail(self):
        r = self.build(self.project("# Intro\n\nTODO ??? here.\n"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("???", r.stderr)

    def test_missing_image_fails_and_soft_passes(self):
        root = self.project("# Intro\n\n![fig](../05_figures/nope.png)\n")
        self.assertEqual(self.build(root).returncode, 1)
        self.assertEqual(self.build(root, "--soft").returncode, 0)

    def test_requested_html_and_docx_are_not_mislabeled(self):
        root = self.project("# Intro\n\nAs shown by @a2020x.\n")
        self.assertEqual(self.build(root, "--to", "html").returncode, 0)
        self.assertTrue((root / "10_paper/paper.html").is_file())
        self.assertEqual(self.build(root, "--to", "docx").returncode, 0)
        self.assertTrue((root / "10_paper/paper.docx").is_file())

    def test_docx_reference_document_preserves_content_and_custom_styles(self):
        root = self.project(
            "# Intro\n\nAs shown by @a2020x.[^1]\n\n[^1]: A surviving footnote.\n\n| A | B |\n| - | - |\n| 1 | 2 |\n"
        )
        reference = root / "templates with space" / "Grüß reference.docx"
        reference.parent.mkdir()
        self.customize_reference(reference)
        before = hashlib.sha256(reference.read_bytes()).hexdigest()

        r = self.build(
            root,
            "--to",
            "docx",
            "--reference-doc",
            "templates with space/Grüß reference.docx",
        )

        output = root / "10_paper/paper.docx"
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(before, hashlib.sha256(reference.read_bytes()).hexdigest())
        self.assertIn("A1B2C3", self.docx_part(output, "word/styles.xml"))
        self.assertIn("Doe", self.docx_part(output, "word/document.xml"))
        self.assertIn(
            "A surviving footnote.", self.docx_part(output, "word/footnotes.xml")
        )
        self.assertIn("<w:tbl>", self.docx_part(output, "word/document.xml"))

    def test_reference_document_errors_are_controlled(self):
        root = self.project("# Intro\n\nAs shown by @a2020x.\n")
        missing = self.build(root, "--to", "docx", "--reference-doc", "missing.docx")
        wrong_output = self.build(
            root, "--to", "html", "--reference-doc", "missing.docx"
        )
        invalid = root / "reference-directory"
        invalid.mkdir()
        invalid_result = self.build(
            root, "--to", "docx", "--reference-doc", str(invalid)
        )
        self.assertEqual(missing.returncode, 2)
        self.assertIn("--reference-doc not found", missing.stderr)
        self.assertEqual(wrong_output.returncode, 2)
        self.assertIn("only supported with --to docx", wrong_output.stderr)
        self.assertEqual(invalid_result.returncode, 2)
        self.assertIn("must be a file", invalid_result.stderr)

    def test_reference_document_cannot_alias_build_outputs(self):
        root = self.project("# Intro\n\nAs shown by @a2020x.\n")
        paper_dir = root / "10_paper"
        for output_name in ("paper.docx", "build.log"):
            for alias in ("direct", "hardlink", "symlink"):
                target = paper_dir / output_name
                self.customize_reference(target)
                before = hashlib.sha256(target.read_bytes()).hexdigest()
                reference = target
                if alias == "hardlink":
                    reference = root / f"reference-{output_name}-hardlink.docx"
                    os.link(target, reference)
                elif alias == "symlink":
                    reference = root / f"reference-{output_name}-symlink.docx"
                    reference.symlink_to(target)

                with self.subTest(output=output_name, alias=alias):
                    r = self.build(
                        root, "--to", "docx", "--reference-doc", str(reference)
                    )
                self.assertEqual(r.returncode, 2)
                self.assertIn("must not alias a build output", r.stderr)
                self.assertEqual(
                    before, hashlib.sha256(target.read_bytes()).hexdigest()
                )


if __name__ == "__main__":
    unittest.main()

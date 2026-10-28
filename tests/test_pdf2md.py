import csv
import importlib.machinery
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/pdf2md"
_loader = importlib.machinery.SourceFileLoader("pdf2md", str(TOOL))
_spec = importlib.util.spec_from_loader("pdf2md", _loader)
pdf2md = importlib.util.module_from_spec(_spec)
_loader.exec_module(pdf2md)


def make_pdf(path, pages):
    """Write a minimal text PDF with one line per page."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>"]
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(len(pages)))
    objs.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>")
    font = 3 + 2 * len(pages)
    for i, text in enumerate(pages):
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                    f"/Contents {4 + 2 * i} 0 R /Resources << /Font << /F1 {font} 0 R >> >> >>")
        stream = f"BT /F1 12 Tf 72 700 Td ({text}) Tj ET"
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out = b"%PDF-1.4\n"
    offs = []
    for n, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{n} 0 obj\n{o}\nendobj\n".encode()
    x = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
    Path(path).write_bytes(out)


@unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not installed")
class NotAPdf(unittest.TestCase):
    def test_one_clean_error_line(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as t:
            bad = Path(t) / "x.pdf"
            bad.write_text("hello", encoding="utf-8")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                rc = pdf2md.main([str(bad), "--out", str(Path(t) / "md")])
        self.assertEqual(rc, 1)
        lines = err.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("not a readable PDF", lines[0])


@unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not installed")
class RealPdf(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pdf = self.dir / "paper.pdf"
        make_pdf(self.pdf, ["Alpha page one", "Beta page two"])
        self.out = self.dir / "02_sources" / "md"

    def tearDown(self):
        self.tmp.cleanup()

    def run_tool(self, *extra):
        return pdf2md.main([str(self.pdf), "--out", str(self.out), "--threshold", "1", *extra])

    def test_text_pdf_markers_and_manifest(self):
        self.assertEqual(self.run_tool(), 0)
        md = (self.out / "paper.md").read_text(encoding="utf-8")
        self.assertIn("<!-- page 1 -->", md)
        self.assertIn("<!-- page 2 -->", md)
        self.assertIn("Alpha page one", md)
        self.assertIn("pages: 2", md)
        self.assertIn("method: pdftotext", md)
        self.assertIn("sha256: " + pdf2md.sha256(self.pdf), md)
        rows = list(csv.DictReader(open(self.dir / "02_sources" / "manifest.csv", encoding="utf-8")))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["stem"], "paper")
        self.assertEqual(rows[0]["pages"], "2")
        self.assertEqual(rows[0]["method"], "pdftotext")

    def test_md_sha256_and_converter_recorded(self):
        import re
        self.assertEqual(self.run_tool(), 0)
        md = (self.out / "paper.md").read_text(encoding="utf-8")
        h = re.search(r"^md_sha256: ([0-9a-f]{64})$", md, re.M).group(1)
        self.assertEqual(h, pdf2md.canonical_hash(md.split("\n---\n", 1)[1]))
        self.assertRegex(md, r"(?m)^converter: pdf2md \d")
        rows = list(csv.DictReader(open(self.dir / "02_sources" / "manifest.csv", encoding="utf-8")))
        self.assertEqual(rows[0]["md_sha256"], h)
        self.assertTrue(rows[0]["converter"].startswith("pdf2md"))
        self.assertNotIn(b"\r", (self.out / "paper.md").read_bytes())

    def test_crlf_and_lf_bodies_hash_identically(self):
        body = "<!-- page 1 -->\nAlpha \u00e9\n"
        self.assertEqual(pdf2md.canonical_hash(body), pdf2md.canonical_hash(body.replace("\n", "\r\n")))
        self.assertEqual(pdf2md.canonical_hash("e\u0301"), pdf2md.canonical_hash("\u00e9"))

    def test_docling_refused(self):
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            rc = self.run_tool("--engine", "docling")
        self.assertNotEqual(rc, 0)
        self.assertIn("per-page", err.getvalue())
        self.assertFalse((self.out / "paper.md").exists())

    def test_legacy_manifest_upgraded(self):
        self.out.parent.mkdir(parents=True, exist_ok=True)
        (self.out.parent / "manifest.csv").write_text(
            "stem,source,sha256,pages,chars_per_page,method,md_path\nold,o.pdf,abc,1,9.0,pdftotext,o.md\n",
            encoding="utf-8")
        self.assertEqual(self.run_tool(), 0)
        rows = list(csv.DictReader(open(self.out.parent / "manifest.csv", encoding="utf-8")))
        self.assertEqual([r["stem"] for r in rows], ["old", "paper"])
        self.assertEqual(rows[0]["md_sha256"], "")
        self.assertTrue(rows[1]["md_sha256"])

    def test_header_only_legacy_manifest_upgraded(self):
        self.out.parent.mkdir(parents=True, exist_ok=True)
        (self.out.parent / "manifest.csv").write_text(
            "stem,source,sha256,pages,chars_per_page,method,md_path\n", encoding="utf-8")
        self.assertEqual(self.run_tool(), 0)
        with open(self.out.parent / "manifest.csv", newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["md_sha256"])

    def test_layout_flag_recorded(self):
        self.assertEqual(self.run_tool("--layout"), 0)
        self.assertIn("method: pdftotext-layout", (self.out / "paper.md").read_text(encoding="utf-8"))

    def test_no_overwrite_unless_force(self):
        self.run_tool()
        md = self.out / "paper.md"
        md.write_text("EDITED", encoding="utf-8")
        self.run_tool()
        self.assertEqual(md.read_text(encoding="utf-8"), "EDITED")
        rows = list(csv.DictReader(open(self.dir / "02_sources" / "manifest.csv", encoding="utf-8")))
        self.assertEqual(len(rows), 1)
        self.run_tool("--force")
        self.assertIn("Alpha page one", md.read_text(encoding="utf-8"))
        rows = list(csv.DictReader(open(self.dir / "02_sources" / "manifest.csv", encoding="utf-8")))
        self.assertEqual(len(rows), 2)


class OcrPath(unittest.TestCase):
    def test_low_text_triggers_ocr(self):
        calls = []

        def fake_pdftotext(pdf, layout=False):
            calls.append(Path(pdf).name)
            return ["x"] if Path(pdf).name == "scan.pdf" else ["recognised text " * 20]

        def fake_run(cmd):
            calls.append(cmd[0])
            if cmd[0] == "qpdf":
                return mock.Mock(returncode=2, stderr="")  # not encrypted
            return mock.Mock(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as t, \
                mock.patch.object(pdf2md, "pdftotext", fake_pdftotext), \
                mock.patch.object(pdf2md, "run", fake_run):
            pages, method = pdf2md.convert(Path(t) / "scan.pdf", 200, "auto", t)
        self.assertEqual(method, "pdftotext+ocr")
        self.assertIn("ocrmypdf", calls)
        self.assertIn("recognised", pages[0])

    def test_missing_binary_is_clear_error(self):
        with tempfile.TemporaryDirectory() as t:
            pdf = Path(t) / "a.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            with mock.patch.object(pdf2md.shutil, "which", return_value=None):
                rc = pdf2md.main([str(pdf), "--out", str(Path(t) / "o")])
            self.assertEqual(rc, 1)
            self.assertFalse((Path(t) / "o" / "a.md").exists())


if __name__ == "__main__":
    unittest.main()

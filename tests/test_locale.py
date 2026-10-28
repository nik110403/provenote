"""Tools must work when the locale's default encoding is ASCII (the Windows cp1252 class of failure)."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parent.parent / "plugins/provenote/bin"
NAME = "Gr\u00e9gory \u010capek \u2014 \u00fc"

ENV = dict(
    os.environ, LC_ALL="C", PYTHONCOERCECLOCALE="0", PYTHONUTF8="0", PYTHONIOENCODING=""
)


def run(args, cwd=None, env=None):
    r = subprocess.run(args, cwd=cwd, env=env or ENV, capture_output=True, timeout=60)
    return (
        r.returncode,
        r.stdout.decode("utf-8", "replace"),
        r.stderr.decode("utf-8", "replace"),
    )


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Locale(unittest.TestCase):
    def setUp(self):
        self._t = tempfile.TemporaryDirectory()
        self.root = Path(self._t.name)
        self.addCleanup(self._t.cleanup)

    def ok(self, rc, err, want=0):
        self.assertEqual(rc, want, err)
        self.assertNotIn("Unicode", err)

    def test_verify_quotes(self):
        write(
            self.root / "02_sources/md/a.md",
            f"<!-- page 1 -->\nBy {NAME} wrote this.\n",
        )
        note = self.root / "01_notes/lit/a.md"
        write(
            note,
            f"---\ncitekey: a\nsource_md: 02_sources/md/a.md\nread_scope: full_text\n"
            f'claims: []\nquotes:\n  - page: 1\n    text: "By {NAME} wrote"\n---\nbody\n',
        )
        rc, out, err = run(
            [sys.executable, str(BIN / "verify-quotes"), str(note)], cwd=self.root
        )
        self.ok(rc, err)
        self.assertIn("PASS", out)

    def test_check_claims(self):
        write(
            self.root / "02_sources/md/a.md",
            f"<!-- page 1 -->\nBy {NAME} wrote this long sentence.\n",
        )
        write(
            self.root / "01_notes/lit/a.md",
            f'---\ncitekey: a\nsource_md: 02_sources/md/a.md\nclaims:\n  - "{NAME} claim."\nquotes:\n'
            f'  - page: 1\n    text: "By {NAME} wrote this long sentence."\n---\nbody {NAME}\n',
        )
        write(self.root / "draft.md", f'{NAME} says "wrote this long sentence" [@a].\n')
        rc, out, err = run(
            [sys.executable, str(BIN / "check-claims"), str(self.root / "draft.md")],
            cwd=self.root,
        )
        self.ok(rc, err)

    def test_check_bib(self):
        write(
            self.root / "r.bib",
            f"@article{{a2020x,\n  author = {{{NAME}}}, title = {{T}}, year = {{2020}},\n"
            f"  doi = {{10.1234/abc.5}}\n}}\n",
        )
        write(self.root / "p.md", f"{NAME} [@a2020x].\n")
        rc, out, err = run(
            [
                sys.executable,
                str(BIN / "check-bib"),
                str(self.root / "r.bib"),
                str(self.root / "p.md"),
            ],
            cwd=self.root,
        )
        self.ok(rc, err)

    def _lit_search(self, *argv, key=None):
        driver = (
            "import importlib.machinery as m, importlib.util as u, json, sys\n"
            f"l = m.SourceFileLoader('ls', {str(BIN / 'lit-search')!r})\n"
            "mod = u.module_from_spec(u.spec_from_loader('ls', l)); l.exec_module(mod)\n"
            "name = 'Gr\\u00e9gory \\u010capek \\u2014 \\u00fc'\n"
            "oa = json.dumps({'results': [{'display_name': 'Money ' + name, 'doi': 'https://doi.org/10.1/x',\n"
            "  'publication_year': 2020, 'cited_by_count': 3, 'authorships': [{'author': {'display_name': name}}]}]})\n"
            "bib = '@article{k2020, author = {' + name + '}, title = {T}, year = {2020}}'\n"
            "def fetch(url, accept='application/json', **kw):\n"
            "    if 'doi.org' in url: return bib\n"
            "    if 'openalex' in url: return oa\n"
            "    raise RuntimeError('HTTP 503')\n"
            "sys.exit(mod.main(sys.argv[1:], fetch=fetch))\n"
        )
        return run([sys.executable, "-c", driver, *argv], cwd=self.root)

    def test_lit_search(self):
        rc, out, err = self._lit_search("money", "--out", "s")
        self.ok(rc, err)
        files = {p.suffix: p for p in (self.root / "s").iterdir()}
        self.assertIn(NAME, files[".md"].read_text(encoding="utf-8"))
        self.assertIn(NAME, files[".csv"].read_text(encoding="utf-8"))

    def test_lit_search_export_bib(self):
        rc, out, err = self._lit_search("--export-bib", "10.1/x", "--bib", "r.bib")
        self.ok(rc, err)
        self.assertIn(NAME, (self.root / "r.bib").read_text(encoding="utf-8"))
        rc, out, err = self._lit_search("--export-bib", "10.1/y", "--bib", "r.bib")
        self.ok(rc, err)

    @unittest.skipIf(
        sys.platform == "win32",
        "synthetic PATH stub requires POSIX executable resolution; valid-PDF coverage is in test_pdf2md",
    )
    def test_pdf2md_text_path(self):
        stub = self.root / "stub"
        stub.mkdir()
        tool = stub / "pdftotext"
        tool.write_text(f"#!/bin/sh\nprintf '%s\\n' '{NAME}'\n", encoding="utf-8")
        tool.chmod(0o755)
        pdf = self.root / "p.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        env = dict(ENV, PATH=str(stub) + os.pathsep + os.environ["PATH"])
        rc, out, err = run(
            [
                sys.executable,
                str(BIN / "pdf2md"),
                str(pdf),
                "--out",
                "md",
                "--threshold",
                "0",
            ],
            cwd=self.root,
            env=env,
        )
        self.ok(rc, err)
        self.assertIn(NAME, (self.root / "md/p.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

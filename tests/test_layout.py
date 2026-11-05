import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_pdf2md import make_pdf  # noqa: E402

BIN = Path(__file__).resolve().parent.parent / "plugins/provenote/bin"
HELPER_COPIES = ("build-paper", "check-bib", "lit-search", "pdf2md", "verify-quotes")
SOURCE = ("---\ntitle: T\n---\n<!-- page 1 -->\nMoney is a social convention that evolved over many "
          "centuries of trade.\n")
NOTE = ('---\ncitekey: a\nsource_md: {src}/a.md\nclaims:\n  - "A claim."\nquotes:\n  - page: 1\n'
        '    text: "Money is a social convention that evolved over many centuries"\n---\nbody\n')
LAYOUT = {"notes": "notes/lit2", "sources_md": "src/md", "sources_pdf": "src/pdf",
          "manifest": "src/files.csv", "bib": "refs/my.bib", "paper_dir": "draft", "search": "notes/search2"}


def load(name):
    loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(BIN / name))
    mod = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(mod)
    return mod


def run(tool, *args, cwd=None):
    return subprocess.run([sys.executable, str(BIN / tool), *args], cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


@contextlib.contextmanager
def chdir(path):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


class Project(unittest.TestCase):
    """A project whose folders differ from the default layout."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "provenote.json").write_text(json.dumps(LAYOUT), encoding="utf-8")
        for d in ("notes/lit2", "src/md", "refs", "draft"):
            (self.root / d).mkdir(parents=True)
        (self.root / "src/md/a.md").write_text(SOURCE, encoding="utf-8")
        self.note = self.root / "notes/lit2/a.md"
        self.note.write_text(NOTE.format(src="src/md"), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()


class HelperCopies(unittest.TestCase):
    def test_the_five_copies_are_identical(self):
        blocks = {}
        for name in HELPER_COPIES:
            text = (BIN / name).read_text(encoding="utf-8")
            start = text.index("# --- layout helper:")
            end = text.index("# --- end layout helper ---")
            blocks[name] = text[start:end]
        self.assertEqual(len(set(blocks.values())), 1, "layout helper copies differ: " + ", ".join(blocks))


class LayoutFile(Project):
    def test_read_from_the_given_folder_only(self):
        for name in HELPER_COPIES:
            mod = load(name)
            self.assertEqual(mod.find_layout(self.root)[0], self.root, name)
            self.assertIsNone(mod.find_layout(self.root / "draft")[0], name)  # no walk to the folder above

    def test_windows_drive_and_root_forms_are_refused(self):
        bad = ["C:x", "C:\\x", "C:/x", "\\Windows\\x", "/abs", "//server/share/x", "a/../b", "a\\..\\b"]
        good = ["notes/lit", "notes\\lit", "x"]
        for name in HELPER_COPIES:
            mod = load(name)
            for v in bad:
                self.assertFalse(mod.plain_relative(v), f"{name}: {v!r} accepted")
            for v in good:
                self.assertTrue(mod.plain_relative(v), f"{name}: {v!r} refused")

    def test_windows_drive_form_in_the_file_is_a_clear_error(self):
        for v in ("C:x", "\\Windows\\x"):
            (self.root / "provenote.json").write_text(json.dumps({"notes": v}), encoding="utf-8")
            r = run("verify-quotes", str(self.note), cwd=self.root)
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("bad layout entries", r.stderr)


class VerifyQuotesLayout(Project):
    def test_custom_paths_pass(self):
        r = run("verify-quotes", str(self.note), cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_layout_file_in_a_folder_above_is_not_read(self):
        r = run("verify-quotes", str(self.note), cwd=self.root / "draft")
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)  # default layout: src/md is outside 02_sources/md

    def test_note_outside_notes_folder_fails_strict_naming_the_layout_path(self):
        other = self.root / "elsewhere"
        other.mkdir()
        n = other / "a.md"
        n.write_text(NOTE.format(src="src/md"), encoding="utf-8")
        r = run("verify-quotes", "--strict", str(n), cwd=self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("notes/lit2", r.stdout)

    def test_source_in_default_folder_is_refused(self):
        (self.root / "02_sources/md").mkdir(parents=True)
        (self.root / "02_sources/md/a.md").write_text(SOURCE, encoding="utf-8")
        self.note.write_text(NOTE.format(src="02_sources/md"), encoding="utf-8")
        r = run("verify-quotes", str(self.note), cwd=self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("src/md", r.stdout)

    def test_manifest_hash_read_from_layout_manifest(self):
        text = SOURCE
        digest = load("verify-quotes").body_hash(text)
        (self.root / "src/md/a.md").write_text(text.replace("title: T", f"title: T\nmd_sha256: {digest}"), encoding="utf-8")
        mf = self.root / "src/files.csv"
        mf.write_text(f"stem,md_sha256\na,{digest}\n", encoding="utf-8")
        self.assertEqual(run("verify-quotes", "--strict", str(self.note), cwd=self.root).returncode, 0)
        mf.write_text("stem,md_sha256\na,deadbeef\n", encoding="utf-8")  # proves the layout manifest is read
        r = run("verify-quotes", "--strict", str(self.note), cwd=self.root)
        self.assertEqual(r.returncode, 1)
        self.assertIn("differs from the md front matter", r.stdout)

    def test_bad_layout_file_is_a_clear_error(self):
        (self.root / "provenote.json").write_text('{"notes": "/abs", "typo": "x"}', encoding="utf-8")
        r = run("verify-quotes", str(self.note), cwd=self.root)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("bad layout entries", r.stderr)

    def test_no_layout_file_keeps_default_layout(self):
        (self.root / "provenote.json").unlink()
        (self.root / "01_notes/lit").mkdir(parents=True)
        (self.root / "02_sources/md").mkdir(parents=True)
        (self.root / "02_sources/md/a.md").write_text(SOURCE, encoding="utf-8")
        n = self.root / "01_notes/lit/a.md"
        n.write_text(NOTE.format(src="02_sources/md"), encoding="utf-8")
        self.assertEqual(run("verify-quotes", str(n), cwd=self.root).returncode, 0)


class CheckClaimsLayout(Project):
    DRAFT = "Money evolved over many centuries [@a].\n"

    def setUp(self):
        super().setUp()
        self.draft = self.root / "draft/paper.md"
        self.draft.write_text(self.DRAFT, encoding="utf-8")

    def test_with_root(self):
        r = run("check-claims", "--root", str(self.root), str(self.draft), cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(str(self.root / "notes/lit2"), r.stderr)

    def test_root_pins_the_project_whatever_the_working_directory_holds(self):
        other = self.root / "draft"  # its own provenote.json points at folders that do not exist
        (other / "provenote.json").write_text(json.dumps({"notes": "nowhere", "sources_md": "nowhere"}),
                                              encoding="utf-8")
        r = run("check-claims", "--root", str(self.root), str(self.draft), cwd=other)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(str(self.root / "notes/lit2"), r.stderr)

    def test_without_root_finds_notes_through_the_layout_file(self):
        r = run("check-claims", str(self.draft), cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("lit2", r.stderr)

    def test_without_root_a_layout_file_above_the_working_directory_is_not_read(self):
        r = run("check-claims", str(self.draft), cwd=self.root / "draft")
        self.assertNotIn("lit2", r.stderr, r.stdout + r.stderr)


class Pdf2mdLayout(Project):
    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not installed")
    def test_default_out_and_manifest_come_from_the_layout(self):
        pdf = self.root / "p.pdf"
        make_pdf(pdf, ["Alpha page one"])
        r = run("pdf2md", str(pdf), "--threshold", "1", cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.root / "src/md/p.md").is_file())
        self.assertTrue((self.root / "src/files.csv").is_file())
        self.assertFalse((self.root / "02_sources").exists())

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not installed")
    def test_layout_file_above_the_working_directory_is_not_read(self):
        pdf = self.root / "p.pdf"
        make_pdf(pdf, ["Alpha page one"])
        r = run("pdf2md", str(pdf), "--threshold", "1", cwd=self.root / "draft")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((self.root / "draft/02_sources/md/p.md").is_file())
        self.assertFalse((self.root / "src/md/p.md").exists())

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not installed")
    def test_explicit_out_wins(self):
        pdf = self.root / "p.pdf"
        make_pdf(pdf, ["Alpha page one"])
        out = self.root / "custom/md"
        r = run("pdf2md", str(pdf), "--threshold", "1", "--out", str(out), cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue((out / "p.md").is_file())
        self.assertTrue((out.parent / "manifest.csv").is_file())


class LitSearchLayout(Project):
    BIB = "@article{k,\n  title={T},\n  doi={10.1000/alpha}\n}\n"

    def fetch(self, url, accept="application/json"):
        return self.BIB

    def test_export_bib_default_comes_from_the_layout(self):
        ls = load("lit-search")
        with chdir(self.root), contextlib.redirect_stdout(io.StringIO()):
            ls.main(["--export-bib", "10.1000/alpha"], fetch=self.fetch)
        self.assertIn("doi={10.1000/alpha}", (self.root / "refs/my.bib").read_text(encoding="utf-8"))
        self.assertFalse((self.root / "07_references").exists())

    def test_layout_file_above_the_working_directory_is_not_read(self):
        ls = load("lit-search")
        with chdir(self.root / "draft"), contextlib.redirect_stdout(io.StringIO()):
            ls.main(["--export-bib", "10.1000/alpha"], fetch=self.fetch)
        self.assertTrue((self.root / "draft/07_references/references.bib").is_file())
        self.assertFalse((self.root / "refs/my.bib").exists())

    def test_explicit_bib_wins(self):
        ls = load("lit-search")
        target = self.root / "other.bib"
        with chdir(self.root), contextlib.redirect_stdout(io.StringIO()):
            ls.main(["--export-bib", "10.1000/alpha", "--bib", str(target)], fetch=self.fetch)
        self.assertTrue(target.is_file())
        self.assertFalse((self.root / "refs/my.bib").exists())

    def test_search_out_default_comes_from_the_layout(self):
        ls = load("lit-search")
        seen = {}
        orig = ls.run_search

        def fake(query, since, n, snow, out, *a, **k):
            seen["out"] = out
            return {"status": "ok", "provider_status": {}, "counts": {"after_dedupe": 0}}, [], "stem"
        ls.run_search = fake
        with chdir(self.root), contextlib.redirect_stdout(io.StringIO()):
            ls.main(["money"])
        ls.run_search = orig
        self.assertEqual(Path(seen["out"]), self.root / "notes/search2")


class CheckBibLayout(Project):
    def test_default_bib_and_paper_come_from_the_layout(self):
        (self.root / "refs/my.bib").write_text(
            "@article{k,\n  author={A},\n  title={T},\n  year={2020}\n}\n", encoding="utf-8")
        (self.root / "draft/paper.md").write_text("Text [@k].\n", encoding="utf-8")
        r = run("check-bib", cwd=self.root)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 entries, 0 errors", r.stdout)


if __name__ == "__main__":
    unittest.main()

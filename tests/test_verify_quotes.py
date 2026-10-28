import importlib.machinery
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/verify-quotes"

_loader = importlib.machinery.SourceFileLoader("verify_quotes", str(TOOL))
vq = importlib.util.module_from_spec(importlib.util.spec_from_loader("verify_quotes", _loader))
_loader.exec_module(vq)

SOURCE = """---
title: Test
---
<!-- page 1 -->
Money is a social
convention that evolved over many cen-
turies of trade.

<!-- page 2 -->
Inflation   is always and everywhere
a monetary phenomenon.
"""


def note(quotes, source="02_sources/md/a.md"):
    items = "".join(f'  - page: {p}\n    text: "{t}"\n' for p, t in quotes)
    return (f'---\ncitekey: a\nsource_md: {source}\nread_scope: full_text\n'
            f'claims: []\nquotes:\n{items}---\nbody\n')


class VerifyQuotes(unittest.TestCase):
    def run_note(self, quotes, source_text=SOURCE, source_ref="02_sources/md/a.md"):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            if source_text is not None:
                (root / "02_sources/md").mkdir(parents=True)
                (root / "02_sources/md/a.md").write_text(source_text, encoding="utf-8")
            (root / "01_notes/lit").mkdir(parents=True)
            n = root / "01_notes/lit/a.md"
            n.write_text(note(quotes, source_ref), encoding="utf-8")
            return subprocess.run([sys.executable, str(TOOL), str(n)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")

    def test_exact_match(self):
        r = self.run_note([(2, "always and everywhere a monetary phenomenon")])
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("PASS", r.stdout)

    def test_whitespace_and_linebreak(self):
        r = self.run_note([(2, "Inflation is always and everywhere a monetary phenomenon.")])
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_hyphenation(self):
        r = self.run_note([(1, "evolved over many centuries of trade")])
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_wrong_page(self):
        r = self.run_note([(1, "always and everywhere a monetary phenomenon")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)
        self.assertIn("different page", r.stdout)

    def test_fabricated(self):
        r = self.run_note([(1, "Money was invented by aliens long ago")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("FAIL", r.stdout)

    def test_missing_source(self):
        r = self.run_note([(1, "Money is a social convention that")], source_text=None)
        self.assertEqual(r.returncode, 1)
        self.assertIn("source_md not found", r.stdout)

    def test_any_fail_fails_all(self):
        r = self.run_note([(1, "Money is a social convention that"), (1, "nonsense text that is not there")])
        self.assertEqual(r.returncode, 1)
        self.assertIn("PASS", r.stdout)
        self.assertIn("FAIL", r.stdout)

    def run_raw(self, note_text, source_bytes=None, name="a"):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "02_sources/md").mkdir(parents=True)
            (root / "01_notes/lit").mkdir(parents=True)
            (root / "02_sources/md/a.md").write_bytes(source_bytes if source_bytes is not None
                                                     else SOURCE.encode("utf-8"))
            n = root / f"01_notes/lit/{name}.md"
            n.write_bytes(note_text if isinstance(note_text, bytes) else note_text.encode("utf-8"))
            return subprocess.run([sys.executable, str(TOOL), str(n)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")

    GOOD = [(1, "Money is a social convention that")]

    def test_bom_note_accepted(self):
        r = self.run_raw(b"\xef\xbb\xbf" + note(self.GOOD).encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_crlf_note_accepted(self):
        r = self.run_raw(note(self.GOOD).replace("\n", "\r\n"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_non_utf8_is_clean_error(self):
        for n, s in ((b"---\ncitekey: a\n---\n\xff\xfe", None), (note(self.GOOD), b"\xff\xfe<!-- page 1 -->")):
            r = self.run_raw(n, s)
            self.assertEqual(r.returncode, 1)
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(len(r.stdout.strip().splitlines()), 1, r.stdout)

    def test_unconsumed_front_matter_line_fails(self):
        r = self.run_raw(note(self.GOOD).replace("claims: []", "claims: []\nstray line without colon"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("cannot parse", r.stdout)

    def test_flow_list_rejected_but_empty_allowed(self):
        r = self.run_raw(note(self.GOOD).replace("quotes:\n", "quotes: [{page: 1, text: x}]\nzz:\n"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("flow-style", r.stdout)
        r = self.run_raw(note([]).replace("quotes:\n", "quotes: []\n"))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_fragment_not_on_word_boundary(self):
        r = self.run_raw(note([(1, "ial convention that evolved over many")]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("not found", r.stdout)

    def test_short_quote_fails(self):
        r = self.run_raw(note([(1, "Money is a social")]))
        self.assertEqual(r.returncode, 1)
        self.assertIn("shorter than 5 words", r.stdout)

    def test_nfkc_ligature_and_nbsp(self):
        src = SOURCE.replace("Inflation   is", "Inflation\u00a0is").replace("monetary", "mone\ufb01tary")
        r = self.run_raw(note([(2, "Inflation is always and everywhere a monefitary phenomenon")]), src.encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_citekey_must_match_file_stem(self):
        r = self.run_raw(note(self.GOOD), name="b")
        self.assertEqual(r.returncode, 1)
        self.assertIn("does not match the file name", r.stdout)

    def test_source_md_stem_must_match_citekey(self):
        r = self.run_raw(note(self.GOOD).replace("citekey: a", "citekey: b"), name="b")
        self.assertEqual(r.returncode, 1)
        self.assertIn("is not the paper", r.stdout)

    def test_source_pdf_stem_must_match_citekey(self):
        r = self.run_raw(note(self.GOOD), SOURCE.replace("title: Test", "source: other.pdf").encode("utf-8"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("names pdf", r.stdout)

    def test_md_sha256_checked(self):
        body = SOURCE.split("---\n", 2)[2]
        good = SOURCE.replace("title: Test", "md_sha256: " + vq.body_hash(SOURCE))
        r = self.run_raw(note(self.GOOD), good.encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARN", r.stderr)
        r = self.run_raw(note(self.GOOD), good.replace("many cen-", "many CEN-").encode("utf-8"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("edited after conversion", r.stdout)
        self.assertTrue(body)

    def test_legacy_md_warns_but_passes(self):
        r = self.run_raw(note(self.GOOD))
        self.assertEqual(r.returncode, 0)
        self.assertIn("WARN", r.stderr)

    def test_crlf_and_lf_copies_hash_identically(self):
        lf = SOURCE
        crlf = SOURCE.replace("\n", "\r\n")
        cr = SOURCE.replace("\n", "\r")
        self.assertEqual(vq.body_hash(lf), vq.body_hash(crlf))
        self.assertEqual(vq.body_hash(lf), vq.body_hash(cr))
        self.assertNotEqual(vq.body_hash(lf), vq.body_hash(lf.replace("Money", "Gold")))
        r = self.run_raw(note(self.GOOD), (lf.replace("title: Test", "md_sha256: " + vq.body_hash(lf))
                                           .replace("\n", "\r\n")).encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_cjk_quote_and_superscript_marker(self):
        src = "---\ntitle: T\n---\n<!-- page 1 -->\n\u8d27\u5e01\u653f\u7b56\u5728\u7ecf\u6d4e\u5371\u673a\u4e2d\u8d77\u5230\u91cd\u8981\u4f5c\u7528\u3002\nThe top decile\u00b9 earns more.\nIt ended.\u00b2 Then much more follows.\n"
        r = self.run_raw(note([(1, "\u8d27\u5e01\u653f\u7b56\u5728\u7ecf\u6d4e\u5371\u673a\u4e2d\u8d77\u5230\u91cd\u8981\u4f5c\u7528")]), src.encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout)
        r = self.run_raw(note([(1, "\u8d27\u5e01\u653f\u7b56")]), src.encode("utf-8"))
        self.assertEqual(r.returncode, 1)
        self.assertIn("15 characters", r.stdout)
        r = self.run_raw(note([(1, "The top decile\u00b9 earns more.")]), src.encode("utf-8"))
        self.assertEqual(r.returncode, 0, r.stdout)
        r = self.run_raw(note([(1, "The top decile earns more.")]), src.encode("utf-8"))  # letter-glued: copy it
        self.assertEqual(r.returncode, 1)
        r = self.run_raw(note([(1, "It ended. Then much more follows.")]), src.encode("utf-8"))  # after punctuation: may be omitted
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_hyphen_is_word_char(self):
        src = SOURCE.replace("a social", "a non-social")
        r = self.run_raw(note([(1, "Money is a social convention that")]), src.encode("utf-8"))
        self.assertEqual(r.returncode, 1)

    def test_parser_messages(self):
        r = self.run_raw(note(self.GOOD).replace("claims: []", "authors:\n  name: x\nclaims: []"))
        self.assertIn("nested mappings are not supported", r.stdout)
        wrapped = note(self.GOOD).replace('text: "Money is a social convention that"',
                                          'text: "Money is a social\n      convention that"')
        self.assertIn("keep each quote on one line", self.run_raw(wrapped).stdout)

    def test_stem_messages_say_how_to_fix(self):
        r = self.run_raw(note(self.GOOD), name="b")
        self.assertIn("rename the note to a.md", r.stdout)
        r = self.run_raw(note(self.GOOD).replace("citekey: a", "citekey: b"), name="b")
        self.assertIn("rename the pdf and md", r.stdout)

    def test_usage(self):
        r = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

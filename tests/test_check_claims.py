import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent.parent / "plugins/provenote/bin/check-claims"

SOURCE = """---
source: {k}.pdf
---
<!-- page 1 -->
Money is a social convention that evolved over many centuries of trade.
Prices rise. Inflation is always and everywhere a monetary phenomenon.
"""
OK_NOTE = ('---\ncitekey: {k}\nsource_md: 02_sources/md/{k}.md\nclaims:\n  - "A claim."\nquotes:\n'
           '  - page: 1\n    text: "Money is a social convention that evolved over many centuries"\n---\nbody\n')
CLAIMS_ONLY = '---\ncitekey: {k}\nsource_md: 02_sources/md/{k}.md\nclaims:\n  - "A claim."\nquotes: []\n---\nbody\n'
EMPTY_NOTE = '---\ncitekey: {k}\nclaims: []\nquotes: []\n---\nbody\n'
BAD_QUOTE = OK_NOTE.replace("evolved over many centuries", "invented by aliens in space")


class CheckClaims(unittest.TestCase):
    def run_draft(self, draft, notes, *flags):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "01_notes/lit").mkdir(parents=True)
            (root / "02_sources/md").mkdir(parents=True)
            for k, body in notes.items():
                (root / f"01_notes/lit/{k}.md").write_text(body.format(k=k), encoding="utf-8")
                if "source_md: none" not in body:
                    (root / f"02_sources/md/{k}.md").write_text(SOURCE.format(k=k), encoding="utf-8")
            (root / "10_draft.md").write_text(draft, encoding="utf-8")
            return subprocess.run([sys.executable, str(TOOL), *flags, "--root", str(root), str(root / "10_draft.md")],
                                  cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")

    def row(self, r, key):
        return next(l for l in r.stdout.splitlines() if f"| {key} |" in l)

    def test_multiple_keys(self):
        r = self.run_draft("Money evolved [@a; @b, p. 12]. Prices rise [@c].\n",
                           {"a": OK_NOTE, "b": OK_NOTE, "c": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        for k in "abc":
            self.assertIn("| OK |", self.row(r, k))
        self.assertIn("1 cited paragraph(s)", r.stdout)

    def test_missing_note_is_unverified(self):
        r = self.run_draft("Claim one [@a]. Claim two [@ghost].\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "ghost"))
        self.assertIn("| OK |", self.row(r, "a"))

    def test_claims_only_note_is_unverified(self):
        r = self.run_draft("A claim [@a].\n", {"a": CLAIMS_ONLY})
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "a"))

    def test_empty_note_is_unverified(self):
        r = self.run_draft("A claim [@a].\n", {"a": EMPTY_NOTE})
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "a"))

    def test_failing_quote_is_unverified(self):
        r = self.run_draft("A claim [@a].\n", {"a": BAD_QUOTE})
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "a"))

    def test_narrative_key_recognised(self):
        r = self.run_draft("As @a argues, money evolved.\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("| OK |", self.row(r, "a"))
        r = self.run_draft("As @ghost argues, money evolved.\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "ghost"))

    def test_draft_quote_must_be_in_source(self):
        r = self.run_draft('Money is "a social convention that evolved" [@a].\n', {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        d = 'Money is \u201ca social convention that never evolved\u201d [@a].\n'
        r = self.run_draft(d, {"a": OK_NOTE}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "a"))
        self.assertNotIn("(advisory)", r.stdout)
        self.assertIn("never evolved", r.stdout)
        r = self.run_draft(d, {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("UNVERIFIED (advisory)", self.row(r, "a"))
        self.assertIn("run with --strict-quotes to make it fail", r.stdout)
        self.assertIn("0 row(s) not OK; 1 advisory", r.stdout)

    def test_period_inside_draft_quote_does_not_split(self):
        r = self.run_draft('The text says "Prices rise. Inflation is always" [@a].\n', {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 cited paragraph(s)", r.stdout)

    def test_no_source_note(self):
        ns = '---\ncitekey: {k}\nsource_md: none\nno_source: software package\nclaims:\n  - "It exists."\nquotes: []\n---\n'
        r = self.run_draft("We use the tool [@a]. See [@b].\n", {"a": ns, "b": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("NO-SOURCE", self.row(r, "a"))
        r = self.run_draft('The tool says "Money is a social convention that evolved" [@a].\n', {"a": ns}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "a"))

    def test_no_source_note_in_verify_quotes(self):
        with tempfile.TemporaryDirectory() as t:
            n = Path(t) / "a.md"
            n.write_text('---\ncitekey: a\nsource_md: none\nno_source: print book\nclaims:\n  - "x"\nquotes: []\n---\n',
                         encoding="utf-8")
            r = subprocess.run([sys.executable, str(TOOL.parent / "verify-quotes"), str(n)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertIn("NO-SOURCE: print book", r.stdout)
            n.write_text(n.read_text(encoding="utf-8").replace("no_source: print book\n", ""), encoding="utf-8")
            r = subprocess.run([sys.executable, str(TOOL.parent / "verify-quotes"), str(n)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 1)

    def test_false_citations_ignored(self):
        for d in ["Mail me at x" + "@lei2023financial.example now.\n", "See https://medium.com/@someauthor/x for more.\n",
                  "Run `@cache` first.\n", "```\n[@a]\n```\n", "<!-- cite [@a, p. 12] -->\n",
                  "See medium.com/@someauthor/x here.\n"]:
            r = self.run_draft(d, {"a": OK_NOTE})
            self.assertEqual(r.returncode, 1, d)
            self.assertIn("0 cited paragraph(s)", r.stdout, d)

    def test_key_grammar(self):
        for d in ["Money @a? yes.\n", "As @a--and so on.\n", "Money [@{a}].\n", "Money [-@a, p. 3].\n", "So @a, said.\n"]:
            r = self.run_draft(d, {"a": OK_NOTE})
            self.assertEqual(r.returncode, 0, d + r.stdout + r.stderr)
            self.assertIn("| a |", r.stdout, d)
        r = self.run_draft("Money [@{../a}].\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 1)

    def test_draft_quote_matching_is_lenient_where_honest(self):
        base = "Money is a social convention that evolved over many centuries"
        for q in [base + ",", base.replace("Money", "money"), "Money is ... evolved over many centuries",
                  "[M]oney is a social convention that evolved", "Money is a social [convention] that evolved over",
                  ]:
            r = self.run_draft(f'Text "{q}" [@a].\n', {"a": OK_NOTE}, "--strict-quotes")
            self.assertEqual(r.returncode, 0, q + r.stdout)
        # scare quotes and inch marks are not judged
        r = self.run_draft('A "so called" thing and a 12" ruler [@a].\n', {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)
        # order matters
        r = self.run_draft('Text "evolved over many centuries ... Money is a social convention" [@a].\n', {"a": OK_NOTE}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("check ellipsis/brackets/case", r.stdout)

    def test_unbalanced_quote_fails(self):
        r = self.run_draft('He wrote \u201cMoney is invented by aliens in space [@a].\n', {"a": OK_NOTE}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("unbalanced", r.stdout)

    def test_uncited_quote_is_flagged_unless_marked(self):
        q = '"Money is a social convention that evolved"'
        r = self.run_draft(f"Cited [@a].\n\nAn aside {q} appears here.\n", {"a": OK_NOTE}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNCITED", r.stdout)
        r = self.run_draft(f"Cited [@a].\n\n<!-- unsourced: own interview -->\nAn aside {q} appears here.\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("UNSOURCED", r.stdout)
        self.assertIn("own interview", r.stdout)
        # empty reason: ignored
        r = self.run_draft(f"Cited [@a].\n\n<!-- unsourced: -->\nAn aside {q} appears here.\n", {"a": OK_NOTE}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        # marker exempts quotes, never citations
        r = self.run_draft('<!-- unsourced: hypothesis box -->\nHe said "never ever verified anywhere" [@ghost].\n', {"a": OK_NOTE})
        self.assertEqual(r.returncode, 1)
        self.assertIn("UNVERIFIED", self.row(r, "ghost"))

    def test_locator_emphasis_and_apostrophes(self):
        r = self.run_draft("Lei [@a] wrote:\n\n> Money is a *social* convention that evolved over many centuries (p. 9)\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)
        r = self.run_draft("Lei [@a] wrote:\n\n> Money is a social convention that evolved over many centuries (Lei, 2023, p. 9)\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)
        r = self.run_draft("The \u201890s and a 12\u201d ruler and the \u00bbfoo bar\u00ab [@a].\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)
        r = self.run_draft("Money is \u2018a social convention that evolved over many centuries\u2019 [@a].\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_no_source_quote_message(self):
        ns = '---\ncitekey: {k}\nsource_md: none\nno_source: print book\nclaims:\n  - "x"\nquotes: []\n---\n'
        r = self.run_draft('He wrote "never ever verified anywhere at all" [@a].\n', {"a": ns}, "--strict-quotes")
        self.assertEqual(r.returncode, 1)
        self.assertIn("no source text for a (NO-SOURCE)", r.stdout)

    def test_table_shows_original_text(self):
        r = self.run_draft('Money `code` [@a] and <!-- note --> more.\n', {"a": OK_NOTE})
        self.assertIn("`code`", r.stdout)

    def test_zero_citations_fails(self):
        r = self.run_draft("No citation here at all.\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 1)

    def test_uncited_sentences_ignored_and_period_in_locator(self):
        r = self.run_draft("No citation here. Cited [@a, p. 3]. Also none.\n", {"a": OK_NOTE})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("1 cited paragraph(s)", r.stdout)

    def test_usage(self):
        r = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()

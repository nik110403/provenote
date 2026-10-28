"""Bypass corpus: each case is a known way to get a fabricated or unlinked quote past the tools.

Every bypass test asserts the SECURE behaviour (non-zero exit / FAIL / UNVERIFIED).
Controls (genuine quotes) must keep passing.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import importlib.machinery
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "plugins/provenote/bin"
FIX = Path(__file__).resolve().parent / "fixtures/bypass"
_ld = importlib.machinery.SourceFileLoader("vq", str(BIN / "verify-quotes"))
vq = importlib.util.module_from_spec(importlib.util.spec_from_loader("vq", _ld))
_ld.exec_module(vq)
SRC_MD = ROOT / "examples/basic/02_sources/md/lei2023financial.md"


def _can_symlink() -> bool:
    d = Path(tempfile.mkdtemp())
    try:
        (d / "l").symlink_to(d, target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False
    finally:
        shutil.rmtree(d, True)


needs_symlink = unittest.skipUnless(_can_symlink(), "symlinks unavailable (Windows without privilege)")


class Bypass(unittest.TestCase):
    def setUp(self):
        # every temp dir of a test lives under this one fresh parent, never directly in the shared temp dir
        self.base = Path(tempfile.mkdtemp(prefix="bypass-")).resolve()
        self.addCleanup(shutil.rmtree, self.base, True)
        # the tool scans all ancestors, so a stray notes folder above the parent would change results: say so
        for a in self.base.parents:
            if (a / "01_notes/lit").exists():
                self.fail(f"environment has a stray {a / '01_notes/lit'}; remove it before running this suite")

    def mk(self):
        return Path(tempfile.mkdtemp(dir=self.base)).resolve()

    def project(self, note=None, draft=None, key=None, parent=None):
        """Temp project with Lei's source md, one fixture note (saved as <key>.md) and a draft."""
        t = tempfile.TemporaryDirectory(dir=parent or self.base)
        self.addCleanup(t.cleanup)
        root = Path(t.name).resolve()
        (root / "02_sources/md").mkdir(parents=True)
        (root / "01_notes/lit").mkdir(parents=True)
        shutil.copy(SRC_MD, root / "02_sources/md")
        if note:
            shutil.copy(FIX / "notes" / f"{note}.md", root / f"01_notes/lit/{key or note}.md")
        if draft:
            shutil.copy(FIX / "drafts" / f"{draft}.md", root / "draft.md")
        return root

    def run_tool(self, tool, root, target, *flags):
        env = {**os.environ, "PWD": str(root)}  # what a shell would export for this cwd
        return subprocess.run([sys.executable, str(BIN / tool), *flags, target], cwd=root, env=env,
                              capture_output=True, text=True, encoding="utf-8", errors="replace")

    def verify(self, note, key=None):
        root = self.project(note, key=key)
        return self.run_tool("verify-quotes", root, f"01_notes/lit/{key or note}.md")

    def claims(self, draft, note=None, key=None, *flags):
        root = self.project(note, draft, key)
        return self.run_tool("check-claims", root, "draft.md", *flags)

    def assertRejected(self, r):
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)

    def project_text(self, draft, notes=None, extra_md=None):
        """Project with Lei's note/source and a draft given as text. notes: {key: note text}."""
        root = self.project("lei2023financial")
        (root / "draft.md").write_text(draft, encoding="utf-8")
        for k, text in (notes or {}).items():
            (root / f"01_notes/lit/{k}.md").write_text(text, encoding="utf-8")
        return root

    def claims_text(self, draft, notes=None, *flags):
        return self.run_tool("check-claims", self.project_text(draft, notes), "draft.md", *flags)

    # controls: genuine material still passes
    def test_control_verify_quotes_genuine_passes(self):
        r = self.verify("lei2023financial")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_control_check_claims_genuine_ok(self):
        r = self.claims("genuine", "lei2023financial")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("OK", r.stdout)

    # bypasses
    def test_wrapped_quote_double_quoted_invented_continuation(self):
        self.assertRejected(self.verify("wrapped_dq"))

    def test_wrapped_quote_plain_invented_continuation(self):
        self.assertRejected(self.verify("wrapped_plain"))

    def test_flow_style_quotes_list(self):
        self.assertRejected(self.verify("flow"))

    def test_claims_without_quotes(self):
        self.assertRejected(self.verify("claims_only"))

    def test_fragment_quote(self):
        self.assertRejected(self.verify("fragment"))

    def test_note_bound_to_wrong_paper(self):
        # smith2020's quote is genuine Lei text; the note names Lei's source_md.
        self.assertRejected(self.verify("smith2020"))

    def test_check_claims_ok_despite_failing_quotes(self):
        root = self.project("fab2023", "fab2023")
        self.assertEqual(self.run_tool("verify-quotes", root, "01_notes/lit/fab2023.md").returncode, 1)
        self.assertRejected(self.run_tool("check-claims", root, "draft.md"))

    def test_fabricated_quote_in_draft(self):
        r = self.claims("fabricated_quote", "lei2023financial", None, "--strict-quotes")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertIn("UNVERIFIED", r.stdout)
        # without the flag the draft-quote finding is advisory: exit 0, but visibly not OK
        r = self.claims("fabricated_quote", "lei2023financial")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("UNVERIFIED (advisory)", r.stdout)
        self.assertIn("advisory: draft-quote check is heuristic; run with --strict-quotes to make it fail", r.stdout)
        self.assertIn("1 advisory", r.stdout)

    def test_draft_with_zero_recognised_citations(self):
        self.assertRejected(self.claims("zero_citations", "lei2023financial"))

    # quote <-> citation attachment and quote forms
    F = "Central banks always rescue labor markets in every crisis"
    REAL = "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports"
    OTHER = ('---\ncitekey: other2020\nsource_md: none\nno_source: print book\nclaims:\n  - "x"\nquotes: []\n---\n')

    def assertUnverified(self, draft, notes=None):
        r = self.claims_text(draft, notes, "--strict-quotes")
        self.assertNotEqual(r.returncode, 0, draft + r.stdout)
        self.assertIn("UNVERIFIED", r.stdout, draft)

    def test_quote_after_abbreviation_split(self):
        self.assertUnverified(f'As @lei2023financial et al. note, "{self.F}".\n')

    def test_citation_in_own_sentence(self):
        self.assertUnverified(f'Lei writes "{self.F}". [@lei2023financial, p. 3]\n')

    def test_other_quote_forms(self):
        for q in (f"\u2018{self.F}\u2019", f"\u00ab{self.F}\u00bb", f"&quot;{self.F}&quot;", f"<q>{self.F}</q>",
                  f"\u2039{self.F}\u203a", f"\u201e{self.F}\u201c", f"'{self.F}'"):
            self.assertUnverified(f"Lei writes {q} [@lei2023financial, p. 3].\n")

    def test_blockquote(self):
        self.assertUnverified(f"> {self.F}\n\n[@lei2023financial, p. 3]\n")
        self.assertUnverified(f"Lei writes:\n\n> {self.F}\n> [@lei2023financial, p. 3]\n")
        self.assertUnverified(f"Lei [@lei2023financial] writes:\n\n> {self.F}\n")

    def test_unclosed_quote(self):
        self.assertUnverified(f"Lei writes \u201c{self.F} [@lei2023financial, p. 3].\n")
        self.assertUnverified(f'Lei writes "{self.F} [@lei2023financial, p. 3].\n')

    def test_real_quote_misattributed(self):
        self.assertUnverified(f'Others say "{self.REAL}" [@other2020].\n', {"other2020": self.OTHER})
        r = self.claims_text(f'Others say "{self.REAL}" [@other2020; @lei2023financial].\n', {"other2020": self.OTHER}, "--strict-quotes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("held by lei2023financial", r.stdout)

    def test_braced_key_and_masked_regions(self):
        self.assertUnverified(f'Lei writes "{self.F}" [@{{lei2023financial}}].\n')
        r = self.claims_text("<!-- [@lei2023financial] -->\n\n```\n[@lei2023financial]\n```\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("0 cited paragraph(s)", r.stdout)

    def test_hyphen_is_a_word_character(self):
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports",
            "eurozone countries, labor market flexibility is pivotal").replace("page: 3", "page: 9")
        root = self.project("lei2023financial")
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        self.assertRejected(self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md"))

    def test_non_ascii_digit_page_is_clean_failure(self):
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace("page: 3", 'page: "\u00b2"')
        root = self.project("lei2023financial")
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("Traceback", r.stderr)

    def test_empty_note_fails(self):
        root = self.project("lei2023financial")
        (root / "01_notes/lit/lei2023financial.md").write_text(
            "---\ncitekey: lei2023financial\nclaimz:\n  - x\nquotez: []\n---\n", encoding="utf-8")
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("empty note", r.stdout)

    # hash strictness
    def hashed_project(self, edit=None, drop_hash=False, manifest_hash="same"):
        root = self.project("lei2023financial")
        md = root / "02_sources/md/lei2023financial.md"
        text = md.read_text(encoding="utf-8")
        h = vq.body_hash(text)
        text = text.replace("method: pdftotext\n", f"method: pdftotext\nmd_sha256: {h}\n", 1) if "md_sha256" not in text else text
        h = vq.body_hash(text)
        if edit:
            text += edit
        if drop_hash:
            text = "".join(l for l in text.splitlines(True) if not l.startswith("md_sha256:"))
        md.write_bytes(text.encode("utf-8"))
        mh = h if manifest_hash == "same" else manifest_hash
        (root / "02_sources/manifest.csv").write_text(
            f"stem,md_sha256\nlei2023financial,{mh}\n", encoding="utf-8")
        (root / "draft.md").write_text("Lei writes [@lei2023financial, p. 3].\n", encoding="utf-8")
        return root

    def test_strict_hash(self):
        root = self.hashed_project()
        note = "01_notes/lit/lei2023financial.md"
        self.assertEqual(self.run_tool("verify-quotes", root, note).returncode, 0)
        r = subprocess.run([sys.executable, str(BIN / "verify-quotes"), "--strict", note], cwd=root,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        # delete the hash field and append a fabricated sentence
        root = self.hashed_project(edit=f"\n{self.F}.\n", drop_hash=True)
        r = subprocess.run([sys.executable, str(BIN / "verify-quotes"), "--strict", note], cwd=root,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("re-run pdf2md", r.stdout)
        self.assertRejected(self.run_tool("check-claims", root, "draft.md"))
        # a hash that does not match the manifest
        root = self.hashed_project(manifest_hash="0" * 64)
        r = subprocess.run([sys.executable, str(BIN / "verify-quotes"), "--strict", note], cwd=root,
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 1)
        self.assertIn("manifest.csv", r.stdout)
        self.assertRejected(self.run_tool("check-claims", root, "draft.md"))

    def test_footnote_and_colon_attachment(self):
        self.assertUnverified(f'Lei writes "{self.F}".[^1]\n\n[^1]: See @lei2023financial, p. 9.\n')
        self.assertUnverified(f'As Lei puts it [@lei2023financial]:\n\n- "{self.F}."\n')
        self.assertUnverified(f'As Lei puts it [@lei2023financial]:\n\n"{self.F}."\n')

    def test_uncited_quote(self):
        d = f'Genuine [@lei2023financial, p. 3].\n\nSomeone said "{self.F}" once.\n'
        r = self.claims_text(d, None, "--strict-quotes")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("UNCITED", r.stdout)
        r = self.claims_text(d)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("UNCITED (advisory)", r.stdout)

    def test_quote_inside_citation_brackets(self):
        for d in (f'[@lei2023financial, p. 9: "{self.F}"]', f'[as Lei puts it, \u201c{self.F}\u201d, @lei2023financial]',
                  f'Text.^[Lei: "{self.F}" @lei2023financial]'):
            self.assertUnverified(d + "\n")

    def test_apostrophes_do_not_hide_text(self):
        real = "Conversely, Zeev (2019) underscores that freely depreciating exchange rates"
        self.assertUnverified(f"Lei [@lei2023financial] says \u2018{real} don\u2019t ever rescue labor markets\u2019.\n")
        self.assertUnverified(f"Lei [@lei2023financial] says '{real} don't ever rescue labor markets'.\n")
        self.assertUnverified(f"Lei [@lei2023financial] says \u2018{real} crisis\u2019s fake tail never written\u2019.\n")
        self.assertUnverified(f"Lei [@lei2023financial] says \u2018{self.F} and more words here.\n")

    def test_ellipsis_pieces_all_checked(self):
        self.assertUnverified(f'Lei [@lei2023financial] says "Never \u2026 {self.REAL.split(" ", 1)[1]}".\n')
        self.assertUnverified('Lei [@lei2023financial] says "always rescue labor" "markets in every" "crisis for sure".\n')

    def test_cjk_with_latin_token(self):
        self.assertUnverified("Lei [@lei2023financial] \u8bf4 \u201cLei \u8d27\u5e01\u653f\u7b56\u4e00\u5b9a\u4f1a\u62ef\u6551\u6240\u6709\u5e02\u573a\u201d.\n")

    def test_more_quote_forms(self):
        for q in (f"\u300c{self.F}\u300d", f"\u300e{self.F}\u300f", f"&ldquo;{self.F}&rdquo;",
                  f"<blockquote>{self.F}</blockquote>", f"\u201a{self.F}\u2018", f"\u00bb{self.F}\u00ab", f"\u203a{self.F}\u2039"):
            self.assertUnverified(f"Lei writes {q} [@lei2023financial, p. 3].\n")

    def test_fence_and_url_do_not_hide_citation(self):
        self.assertUnverified(f'```code``` Lei writes "{self.F}" [@lei2023financial].\n')
        self.assertUnverified(f'Lei "{self.F}" (https://doi.org/10.1/x)[@lei2023financial]\n')

    def test_nosource_not_self_declarable_for_converted_paper(self):
        ns = '---\ncitekey: lei2023financial\nsource_md: none\nno_source: print\nclaims:\n  - "x"\nquotes: []\n---\n'
        root = self.project_text(f'Lei writes "{self.F}" [@lei2023financial].\n', {"lei2023financial": ns})
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("converted copy", r.stdout)
        self.assertNotEqual(self.run_tool("check-claims", root, "draft.md").returncode, 0)

    def test_subdirectory_forged_source_fails_strict(self):
        root = self.hashed_project()
        sub = root / "02_sources/md/x"
        sub.mkdir()
        forged = (root / "02_sources/md/lei2023financial.md").read_text(encoding="utf-8") + f"\n<!-- page 3 -->\n{self.F}.\n"
        h = vq.body_hash(forged)
        forged = "".join(f"md_sha256: {h}\n" if l.startswith("md_sha256:") else l for l in forged.splitlines(True))
        (sub / "lei2023financial.md").write_bytes(forged.encode("utf-8"))
        (root / "02_sources/manifest.csv").write_text(f"stem,md_sha256\nlei2023financial,{h}\n", encoding="utf-8")
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "02_sources/md/lei2023financial.md", "02_sources/md/x/lei2023financial.md").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("directly in 02_sources/md", r.stdout)
        self.assertRejected(self.run_tool("check-claims", root, "draft.md"))

    def test_planted_nested_sources_cannot_shadow_real_one(self):
        root = self.project("lei2023financial")
        (root / "01_notes/02_sources/md").mkdir(parents=True)
        forged = SRC_MD.read_text(encoding="utf-8") + f"\n<!-- page 3 -->\n{self.F}.\n"
        (root / "01_notes/02_sources/md/lei2023financial.md").write_text(forged, encoding="utf-8")
        self.assertEqual(Path(vq.project_root(root / "01_notes/lit/lei2023financial.md")).resolve(), root.resolve())
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "02_sources/md/lei2023financial.md", "01_notes/02_sources/md/lei2023financial.md").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        self.assertRejected(self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md"))

    @needs_symlink
    def test_symlinked_note_cannot_pick_attacker_root(self):
        root = self.project("lei2023financial")
        evil = Path(self.mk())
        self.addCleanup(shutil.rmtree, evil, True)
        (evil / "02_sources/md").mkdir(parents=True)
        (evil / "01_notes/lit").mkdir(parents=True)
        forged = SRC_MD.read_text(encoding="utf-8") + f"\n<!-- page 3 -->\n{self.F}.\n"
        h = vq.body_hash(forged)
        forged = "".join(f"md_sha256: {h}\n" if l.startswith("md_sha256:") else l for l in forged.splitlines(True))
        (evil / "02_sources/md/lei2023financial.md").write_bytes(forged.encode("utf-8"))
        (evil / "02_sources/manifest.csv").write_text(f"stem,md_sha256\nlei2023financial,{h}\n", encoding="utf-8")
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (evil / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        (root / "draft.md").write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
        lit = root / "01_notes/lit"
        shutil.rmtree(lit)
        lit.symlink_to(evil / "01_notes/lit")
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("outside the project", r.stdout)
        r = self.run_tool("check-claims", root, "draft.md")
        self.assertEqual(r.returncode, 1, r.stdout)

    @needs_symlink
    def test_control_project_reached_through_symlink(self):
        root = self.project("lei2023financial", "genuine")
        link = Path(self.mk()) / "link"
        self.addCleanup(shutil.rmtree, link.parent, True)
        link.symlink_to(root, target_is_directory=True)
        r = self.run_tool("verify-quotes", link, "01_notes/lit/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = self.run_tool("check-claims", link, "draft.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_stray_outer_sources_does_not_disable_converted_copy_guard(self):
        root = self.project("lei2023financial")
        outer = root.parent / "stray_outer"
        outer.mkdir()
        self.addCleanup(shutil.rmtree, outer, True)
        proj = outer / "proj"
        shutil.move(str(root), str(proj))
        (outer / "02_sources").mkdir()
        ns = '---\ncitekey: lei2023financial\nsource_md: none\nno_source: print\nclaims:\n  - "x"\nquotes: []\n---\n'
        (proj / "01_notes/lit/lei2023financial.md").write_text(ns, encoding="utf-8")
        r = self.run_tool("verify-quotes", proj, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("converted copy", r.stdout)

    def test_subdirectory_md_fails_without_manifest(self):
        root = self.project("lei2023financial")
        (root / "02_sources/md/x").mkdir()
        shutil.move(str(root / "02_sources/md/lei2023financial.md"), str(root / "02_sources/md/x/lei2023financial.md"))
        note = (root / "01_notes/lit/lei2023financial.md").read_text(encoding="utf-8").replace(
            "02_sources/md/lei2023financial.md", "02_sources/md/x/lei2023financial.md")
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("directly in 02_sources/md", r.stdout)

    def test_forged_source_outside_sources_and_broken_manifest(self):
        root = self.project("lei2023financial")
        (root / "03_x/md").mkdir(parents=True)
        forged = SRC_MD.read_text(encoding="utf-8") + f"\n<!-- page 3 -->\n{self.F}.\n"
        (root / "03_x/md/lei2023financial.md").write_text(forged, encoding="utf-8")
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "02_sources/md/lei2023financial.md", "03_x/md/lei2023financial.md")
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("under 02_sources/md", r.stdout)
        # a manifest that cannot be parsed makes check-claims strict
        root = self.project("lei2023financial")
        (root / "02_sources/manifest.csv").write_bytes(b"\xff\xfe\x00bad")
        (root / "draft.md").write_text("Lei [@lei2023financial].\n", encoding="utf-8")
        self.assertNotEqual(self.run_tool("check-claims", root, "draft.md").returncode, 0)

    def forged_pair(self, base):
        """Plant an empty 01_notes/ and a forged, hash-consistent 02_sources/ inside base."""
        (base / "01_notes").mkdir(parents=True)
        (base / "02_sources/md").mkdir(parents=True)
        forged = SRC_MD.read_text(encoding="utf-8") + f"\n<!-- page 3 -->\n{self.F}.\n"
        h = vq.body_hash(forged)
        forged = "".join(f"md_sha256: {h}\n" if l.startswith("md_sha256:") else l for l in forged.splitlines(True))
        (base / "02_sources/md/lei2023financial.md").write_bytes(forged.encode("utf-8"))
        (base / "02_sources/manifest.csv").write_text(f"stem,md_sha256\nlei2023financial,{h}\n", encoding="utf-8")

    def test_planted_pair_inside_notes_cannot_pick_root(self):
        root = self.project("lei2023financial")
        self.forged_pair(root / "01_notes/lit")
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (root / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        (root / "draft.md").write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
        self.assertEqual(Path(vq.project_root(root / "01_notes/lit/lei2023financial.md")).resolve(), root.resolve())
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 1, r.stdout)
        r = self.run_tool("check-claims", root, "draft.md", "--strict-quotes")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_draft_side_planted_pair_cannot_pick_notes(self):
        root = self.project("lei2023financial")
        (root / "10_paper").mkdir()
        self.forged_pair(root / "10_paper")
        (root / "10_paper/01_notes/lit").mkdir()
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (root / "10_paper/01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        (root / "10_paper/ch.md").write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
        r = self.run_tool("check-claims", root, "10_paper/ch.md", "--strict-quotes")
        self.assertEqual(r.returncode, 2, r.stdout)
        r = self.run_tool("check-claims", root, "10_paper/ch.md", "--strict-quotes", "--root", str(root))
        self.assertEqual(r.returncode, 1, r.stdout)
        r = self.run_tool("check-claims", root, "10_paper/ch.md", "--root", str(root))
        self.assertNotIn("| OK |", r.stdout)
        self.assertIn("UNVERIFIED", r.stdout)

    def test_draft_side_planted_no_source_note_not_accepted(self):
        root = self.project("lei2023financial")
        (root / "10_paper/01_notes/lit").mkdir(parents=True)
        ns = '---\ncitekey: lei2023financial\nsource_md: none\nno_source: print\nclaims:\n  - "x"\nquotes: []\n---\n'
        (root / "10_paper/01_notes/lit/lei2023financial.md").write_text(ns, encoding="utf-8")
        (root / "10_paper/ch.md").write_text("Lei [@lei2023financial].\n", encoding="utf-8")
        r = self.run_tool("check-claims", root, "10_paper/ch.md", "--strict-quotes")
        self.assertNotIn("NO-SOURCE", r.stdout, r.stdout)  # real note is used, not the planted one

    @needs_symlink
    def test_symlink_steering_root_rejected(self):
        root = self.project("lei2023financial")
        inner = root / "01_notes/lit/inner"
        self.forged_pair(inner)
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (inner / "01_notes/lit").mkdir()
        (inner / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        (root / "x").symlink_to(inner, target_is_directory=True)
        r = self.run_tool("verify-quotes", root, "x/01_notes/lit/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_strict_note_outside_01_notes_fails(self):
        root = self.project("lei2023financial")
        shutil.move(str(root / "01_notes/lit"), str(root / "elsewhere"))
        r = self.run_tool("verify-quotes", root, "elsewhere/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("not under", r.stdout)

    @needs_symlink
    def test_control_symlinked_sources_dir(self):
        for sub in ("02_sources", "02_sources/md"):
            root = self.project("lei2023financial", "genuine")
            ext = Path(self.mk())
            self.addCleanup(shutil.rmtree, ext, True)
            target = root / sub
            shutil.move(str(target), str(ext / "store"))
            target.symlink_to(ext / "store", target_is_directory=True)
            r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md", "--strict")
            self.assertEqual(r.returncode, 0, sub + r.stdout + r.stderr)
            r = self.run_tool("check-claims", root, "draft.md")
            self.assertEqual(r.returncode, 0, sub + r.stdout + r.stderr)

    def test_control_note_in_nested_folder_resolves_root(self):
        root = self.project("lei2023financial", "genuine")
        (root / "01_notes/lit/sub").mkdir()
        shutil.move(str(root / "01_notes/lit/lei2023financial.md"), str(root / "01_notes/lit/sub"))
        self.assertEqual(Path(vq.project_root(root / "01_notes/lit/sub/lei2023financial.md")).resolve(), root.resolve())
        r = self.run_tool("verify-quotes", root, "01_notes/lit/sub/lei2023financial.md", "--strict")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # notes folder: exactly one candidate, or fail (no ordering among candidates)
    def planted_parent(self):
        """(sandbox S holding a forged pair + note, genuine project P inside S, draft quoting the forgery)."""
        sandbox = Path(self.mk())
        self.addCleanup(shutil.rmtree, sandbox, True)
        self.forged_pair(sandbox)
        (sandbox / "01_notes/lit").mkdir(parents=True, exist_ok=True)
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (sandbox / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        root = self.project("lei2023financial", parent=sandbox)
        return sandbox, root

    def test_planted_parent_pair_is_ambiguous(self):
        _, root = self.planted_parent()
        (root / "10_paper").mkdir()
        for d in ("ch.md", "10_paper/ch.md"):
            (root / d).write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
            r = self.run_tool("check-claims", root, d, "--strict-quotes")
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("ambiguous notes folder", r.stderr)
            self.assertNotIn("|", r.stdout)
        r = self.run_tool("check-claims", root, "ch.md", "--strict-quotes", "--root", str(root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("UNVERIFIED", r.stdout)
        self.assertIn(f"notes: {root / '01_notes/lit'}", r.stderr)

    def test_stray_empty_parent_notes_folder_is_ambiguous_not_silent(self):
        sandbox = Path(self.mk())
        self.addCleanup(shutil.rmtree, sandbox, True)
        (sandbox / "01_notes/lit").mkdir(parents=True)
        root = self.project("lei2023financial", "genuine", parent=sandbox)
        r = self.run_tool("check-claims", root, "draft.md")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r = self.run_tool("check-claims", root, "draft.md", "--root", str(root))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_external_draft_with_own_notes_is_ambiguous(self):
        root = self.project("lei2023financial")
        ext = Path(self.mk())
        self.addCleanup(shutil.rmtree, ext, True)
        self.forged_pair(ext / "collab")
        (ext / "collab/01_notes/lit").mkdir(parents=True)
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (ext / "collab/01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        draft = ext / "collab/ch.md"
        draft.write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
        r = self.run_tool("check-claims", root, str(draft), "--strict-quotes")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        r = self.run_tool("check-claims", root, str(draft), "--strict-quotes", "--root", str(root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    @needs_symlink
    def test_symlinked_paper_dir_with_pair_never_ok(self):
        root = self.project("lei2023financial")
        ext = Path(self.mk())
        self.addCleanup(shutil.rmtree, ext, True)
        self.forged_pair(ext)
        (ext / "01_notes/lit").mkdir(parents=True)
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (ext / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        (root / "10_paper").symlink_to(ext, target_is_directory=True)
        (ext / "ch.md").write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
        r = self.run_tool("check-claims", root / "10_paper", "ch.md", "--strict-quotes")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertNotIn("| OK |", r.stdout)

    def external_forged_draft(self):
        """(genuine project P, draft X/ch.md in an external folder shipping a forged pair + note)."""
        root = self.project("lei2023financial")
        (root / "10_paper").mkdir()
        ext = self.mk()
        self.forged_pair(ext)
        (ext / "01_notes/lit").mkdir(parents=True)
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", self.F)
        (ext / "01_notes/lit/lei2023financial.md").write_text(note, encoding="utf-8")
        draft = ext / "ch.md"
        draft.write_text(f'Lei writes "{self.F}" [@lei2023financial].\n', encoding="utf-8")
        return root, draft

    def test_external_draft_cwd_inside_project_is_ambiguous(self):
        root, draft = self.external_forged_draft()
        for cwd in (root / "10_paper", root / "01_notes/lit"):
            r = self.run_tool("check-claims", cwd, str(draft), "--strict-quotes")
            self.assertEqual(r.returncode, 2, f"{cwd}: {r.stdout}{r.stderr}")
            self.assertIn("ambiguous notes folder", r.stderr)
        r = self.run_tool("check-claims", root / "10_paper", str(draft), "--strict-quotes", "--root", str(root))
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)

    def test_unreadable_planted_notes_folder_exits_2(self):
        if sys.platform == "win32" or not hasattr(os, "geteuid"):
            self.skipTest("POSIX file modes only")
        if os.geteuid() == 0:
            self.skipTest("root ignores file modes")
        sandbox = self.mk()
        (sandbox / "01_notes").mkdir()
        root = self.project("lei2023financial", "genuine", parent=sandbox)
        (sandbox / "01_notes").chmod(0)
        self.addCleanup((sandbox / "01_notes").chmod, 0o755)
        r = self.run_tool("check-claims", root, "draft.md")
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn("cannot inspect", r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        r = self.run_tool("check-claims", root, "draft.md", "--root", str(root))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_root_must_hold_notes(self):
        root = self.project("lei2023financial", "genuine")
        r = self.run_tool("check-claims", root, "draft.md", "--root", str(root / "nope"))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr)

    def test_control_single_candidate_found_and_reported(self):
        root = self.project("lei2023financial", "genuine")
        r = self.run_tool("check-claims", root, "draft.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("notes: ", r.stderr)

    def test_short_quotes_add_up(self):
        self.assertUnverified('Lei [@lei2023financial] says "always rescue" and "labor markets" and "every crisis".\n')


    # super/subscript digits: never erased, never equal to plain digits; footnote tolerance is source-side only
    def sup_match(self, quote, source):
        want = vq._ws(quote)
        return vq.contains(want, vq.variants(source))

    def test_altered_numbers_with_super_subscripts_fail(self):
        for quote, source in (
            ("Our dataset includes 130\u2079 countries and regions", "Our dataset includes 130 countries and regions"),
            ("the sample of H\u2082O\u2082 molecules was large", "the sample of H\u2082O molecules was large"),
            ("a total of 10\u2079 units were counted", "a total of 10\u00b3 units were counted"),
            ("a total of 109 units were counted", "a total of 10\u2079 units were counted"),
            ("a total of 10 units were counted today", "a total of 10\u2079 units were counted today"),
            ("an area of 5 m\u00b3 was measured", "an area of 5 m\u00b2 was measured"),
        ):
            self.assertFalse(self.sup_match(quote, source), (quote, source))

    def test_source_footnote_markers_are_tolerated(self):
        # a marker after sentence punctuation / closing quote and before whitespace or the end may be omitted
        for quote, source in (
            ("it was impossible. Next the rates rose", "it was impossible.\u00b9 Next the rates rose"),
            ("it was impossible.\u00b9 Next the rates rose", "it was impossible.\u00b9 Next the rates rose"),
            ("interest rates rose, while the prices fell", "interest rates rose,\u00b2 while the prices fell"),
            ("interest rates rose,\u00b2 while the prices fell", "interest rates rose,\u00b2 while the prices fell"),
            ('he said "it works well enough" and left', 'he said "it works well enough"\u00b9 and left'),
            ("a total of 10\u2079 units were counted", "a total of 10\u2079 units were counted"),
            ("H\u2082O is the common solvent here", "H\u2082O is the common solvent here"),
            ("a letter-glued interest rates\u00b9 rose sharply", "a letter-glued interest rates\u00b9 rose sharply"),
        ):
            self.assertTrue(self.sup_match(quote, source), (quote, source))

    def test_letter_glued_and_unit_superscripts_must_be_copied(self):
        for quote, source in (
            ("the value n! grows quickly with size", "the value n!\u00b2 grows quickly with size"),
            ("the term f' at the origin is zero", "the term f'\u00b2 at the origin is zero"),
            ("interest rates rose sharply in the spring", "interest rates\u00b9 rose sharply in the spring"),
            ("the area was 100 m today for sure", "the area was 100 m\u00b2 today for sure"),
            ("an R of 0.93 was reported here", "an R\u00b2 of 0.93 was reported here"),
            ("the sum x+y=z holds for all values", "the sum x\u00b2+y\u00b2=z\u00b2 holds for all values"),
            ("a volume of 5 cm was measured here", "a volume of 5 cm\u00b3 was measured here"),
            ("the ion Ca+ was present in the sample", "the ion Ca\u00b2\u207a was present in the sample"),
            ("the ion Ca\u207a was present in the sample", "the ion Ca\u00b2\u207a was present in the sample"),
            ("the ion Ca+ was present in the sample", "the ion Ca\u207a was present in the sample"),
            ("the factor (1+r) was applied here today", "the factor (1+r)\u00b2 was applied here today"),
            ("a dose of (10 mg) was given to them", "a dose of (10 mg)\u00b2 was given to them"),
            ("a growth of 5% was seen in all cases", "a growth of 5%\u00b9 was seen in all cases"),
        ):
            self.assertFalse(self.sup_match(quote, source), (quote, source))

    def test_private_use_characters_never_equal_tokens(self):
        for typed, src in (("\ue009", "\u2079"), ("\u2079", "\ue009"), ("\ue021", "\u207b")):
            self.assertFalse(self.sup_match(f"a total of 10{typed} units were counted", f"a total of 10{src} units were counted"))
        self.assertFalse(self.sup_match("a total of 10\ue019 units were counted", "a total of 10\u2089 units were counted"))

    def test_forged_superscript_number_fails_cli(self):
        root = self.project("lei2023financial")
        note = (FIX / "notes/lei2023financial.md").read_text(encoding="utf-8")
        q = "Our dataset includes 130\u2079 countries and regions spanning from 2000 to 2019."
        forged = note.replace("page: 3", "page: 4").replace(
            "Conversely, Zeev (2019) underscores that freely depreciating exchange rates can spur exports", q)
        (root / "01_notes/lit/lei2023financial.md").write_bytes(forged.encode("utf-8"))
        for flags in ((), ("--strict",)):
            r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md", *flags)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        genuine = forged.replace("130\u2079", "130")
        (root / "01_notes/lit/lei2023financial.md").write_bytes(genuine.encode("utf-8"))
        r = self.run_tool("verify-quotes", root, "01_notes/lit/lei2023financial.md")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    # entity-encoded comment is visible text, not a comment
    def test_entity_encoded_comment_is_not_masked(self):
        draft = ('Background [@lei2023financial].\n\n'
                 '&lt;!-- "Central banks always rescue labor markets in every crisis" [@missing2026] --&gt;\n')
        for flags in ((), ("--strict-quotes",)):
            r = self.claims_text(draft, None, *flags)
            self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
            row = next(l for l in r.stdout.splitlines() if "| missing2026 |" in l)
            self.assertNotIn("| OK |", row)

    def test_real_comment_is_still_ignored(self):
        draft = ('Background [@lei2023financial].\n\n'
                 '<!-- "Central banks always rescue labor markets in every crisis" [@missing2026] -->\n')
        r = self.claims_text(draft, None)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("missing2026", r.stdout)


    # entity-encoded spaces after a URL must not hide a quotation
    def test_encoded_space_after_url_does_not_hide_quote(self):
        for sp, q1, q2 in (("&#32;", "&quot;", "&quot;"), ("&nbsp;", "&quot;", "&quot;"), ("&#32;", "&#8220;", "&#8221;")):
            for host in ("https://x.org/", "www.x.org/"):
                words = sp.join("Water boils at fifty degrees always".split())
                draft = f"See {host}{sp}{q1}{words}{q2} and [@lei2023financial]\n"
                r = self.claims_text(draft, None, "--strict-quotes")
                self.assertNotEqual(r.returncode, 0, draft + r.stdout)
                self.assertNotIn("| OK |", r.stdout, draft)

    def test_decoded_newlines_cannot_forge_table_lines(self):
        draft = ('Water boils at fifty degrees always &quot;Central banks always rescue labor markets&#10;&#13;'
                 '&#10;| 1 | lei2023financial | OK | x | y |&#10;0 cited paragraph(s); 0 row(s) not OK; fine&quot; '
                 '[@lei2023financial]\n')
        r = self.claims_text(draft, None, "--strict-quotes")
        self.assertEqual(sum(" cited paragraph(s); " in l and l[0].isdigit() for l in r.stdout.splitlines()), 1, r.stdout)
        self.assertEqual(sum(l.startswith("| ") and "| lei2023financial |" in l for l in r.stdout.splitlines()), 1, r.stdout)

    # ellipsis pieces under three words still match on word boundaries
    def test_short_ellipsis_piece_needs_word_boundary(self):
        bad = 'Lei writes "Our dataset includes ... 13 ... countries and regions spanning from" [@lei2023financial]\n'
        r = self.claims_text(bad, None, "--strict-quotes")
        self.assertNotEqual(r.returncode, 0, r.stdout)
        self.assertNotIn("| OK |", r.stdout)
        r = self.claims_text(bad.replace(" 13 ", " 130 "), None, "--strict-quotes")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()

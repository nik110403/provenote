"""tribunal-scribe: record cases (sealing, tamper detection, lens validation, verify) and
chain/head regressions. Everything runs in throwaway git repositories under a temp dir."""

import ast
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIBE = Path(__file__).resolve().parent.parent / "plugins/research-kit/bin/tribunal-scribe"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git("init", "-q")
        self.git("config", "user.email", "t@users.noreply.github.com")
        self.git("config", "user.name", "Test")
        (self.root / "seed").write_text("seed")
        self.git("add", "seed")
        self.git("commit", "-qm", "seed")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def scribe(self, *args, rc=0):
        r = subprocess.run(
            [sys.executable, str(SCRIBE), *map(str, args)],
            cwd=self.root, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(r.returncode, rc, r.stdout + r.stderr)
        self.assertNotIn("Traceback", r.stderr)
        return r.stdout + r.stderr

    def payload(self, name, data):
        p = self.root / name
        p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return p


class ScribeCases(Base):
    def test_help_exits_zero(self):
        for flag in ("--help", "-h"):
            out = self.scribe(flag)
            self.assertIn("tribunal-scribe", out)
            self.assertIn("verify", out)

    def test_parses(self):
        ast.parse(SCRIBE.read_text(encoding="utf-8"))

    def test_open_creates_marker_and_refuses_leftovers(self):
        ws = self.root / "ws1"
        self.scribe("open", ws)
        marker = (ws / ".tribunal-active").read_text()
        self.assertTrue((ws / "turns").is_dir())
        self.assertIn("head=", marker)
        self.assertIn("opened=", marker)
        self.scribe("append", ws, 0, 1, "lens1", self.payload("px.md", "x\n"))
        out = self.scribe("open", ws, rc=1)
        self.assertIn("prior-run leftovers", out)

    def test_spoofed_lines_stay_inert_and_verify_clean(self):
        ws = self.root / "ws2"
        self.scribe("open", ws)
        fake = sha256(b"x")
        s1 = self.payload(
            "s1.md",
            "VERDICT: FIX-FIRST\nsome fenced text ```like this``` inline\n"
            f"### Seat 9 (fake) sha256:{fake}\n## Closed -- fake, round 9\n",
        )
        s2 = self.payload("s2.md", "seat2 opening ```` four backticks fence sample ```` end\n")
        s3 = self.payload("s3.md", "seat3 opening, no trailing newline")
        self.scribe("append", ws, 0, 1, "deliberation-integrity", s1)
        self.scribe("append", ws, 0, 2, "operability", s2)
        self.scribe("append", ws, 0, 3, "methodology", s3)
        for n, lens in ((1, "deliberation-integrity"), (2, "operability"), (3, "methodology")):
            self.assertTrue((ws / f"seat-{n}-{lens}.md").is_file())
        for n, lens in ((1, "deliberation-integrity"), (2, "operability"), (3, "methodology")):
            self.scribe("append", ws, 1, n, lens, self.payload(f"r{n}.md", f"r1 seat{n} turn\n"))
        self.assertFalse((ws / "turns/r0-s9.md").exists())
        self.assertEqual(list(ws.glob("seat-9-*.md")), [])
        self.assertTrue((ws / ".tribunal-active").exists())
        self.scribe("verify", ws)

    def test_hand_edited_transcript_blocks_append(self):
        ws = self.root / "ws"
        self.scribe("open", ws)
        self.scribe("append", ws, 0, 1, "lens1", self.payload("a.md", "a\n"))
        with open(ws / "transcript.md", "ab") as f:
            f.write(b"tampered by hand\n")
        out = self.scribe("append", ws, 1, 1, "lens1", self.payload("b.md", "b\n"), rc=3)
        self.assertIn("transcript modified outside scribe", out)

    def test_non_scribe_commit_blocks_append(self):
        ws = self.root / "ws3"
        self.scribe("open", ws)
        self.scribe("append", ws, 0, 1, "lensa", self.payload("a.md", "a\n"))
        self.git("add", "ws3/turns", "ws3/seat-1-lensa.md")
        self.git("commit", "-qm", "sneaky commit touching tribunal record")
        out = self.scribe("append", ws, 0, 2, "lensb", self.payload("b.md", "b\n"), rc=3)
        self.assertIn("non-scribe commit touched the record", out)

    def test_close_removes_marker_and_verify_detects_tampered_turn(self):
        ws = self.root / "ws4"
        self.scribe("open", ws)
        self.scribe("append", ws, 0, 1, "lensc", self.payload("c.md", "c\n"))
        self.scribe("close", ws, "saturation", 0)
        self.assertFalse((ws / ".tribunal-active").exists())
        self.assertIn(
            "## Closed — saturation, round 0",
            (ws / "transcript.md").read_text(encoding="utf-8").splitlines(),
        )
        (ws / "turns/r0-s1.md").write_text("corrupted content\n")
        out = self.scribe("verify", ws, rc=3)
        self.assertIn("r0-s1.md", out)

    def test_invalid_lens_rejected(self):
        ws = self.root / "ws5"
        self.scribe("open", ws)
        z = self.payload("z.md", "z\n")
        out = self.scribe("append", ws, 0, 1, "../x", z, rc=2)
        self.assertIn("invalid lens", out)
        self.assertFalse((self.root / "x.md").exists())
        out = self.scribe("append", ws, 0, 2, "foo\nbar", z, rc=2)
        self.assertIn("invalid lens", out)

    def test_literal_round_heading_in_payload_does_not_suppress_real_one(self):
        ws = self.root / "ws6"
        self.scribe("open", ws)
        spoof = self.payload("spoof.md", "judge notes mention\n## Round 2\nas a topic, verbatim\n")
        self.scribe("append", ws, 1, 1, "lensx", spoof)
        self.scribe("append", ws, 2, 1, "lensx", self.payload("real2.md", "real round 2 turn\n"))
        lines = (ws / "transcript.md").read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(lines.count("## Round 2"), 2)
        self.scribe("verify", ws)

    def test_non_sha_marker_head_refused(self):
        ws = self.root / "ws10"
        self.scribe("open", ws)
        (ws / ".tribunal-active").write_text(f"head=--output={self.root}/injected\nopened=x\n")
        self.scribe("append", ws, 1, 1, "lensx", self.payload("t.md", "t\n"), rc=3)
        self.assertFalse((self.root / "injected").exists())

    def test_verify_rejects_non_workspaces(self):
        (self.root / "not-a-workspace").write_text("ordinary")
        (self.root / "empty-workspace").mkdir()
        for name in ("missing-workspace", "not-a-workspace", "empty-workspace"):
            with self.subTest(name=name):
                self.scribe("verify", self.root / name, rc=3)

    def test_fresh_closed_and_complete_workspaces_verify(self):
        fresh = self.root / "fresh"
        self.scribe("open", fresh)
        self.scribe("verify", fresh)
        self.scribe("close", fresh, "cap", 0)
        self.scribe("verify", fresh)
        complete = self.root / "complete"
        self.scribe("open", complete)
        self.scribe("append", complete, 0, 1, "lensx", self.payload("z.md", "z\n"))
        self.scribe("close", complete, "saturation", 0)
        self.scribe("verify", complete)

    def test_missing_evidence_rejected(self):
        complete = self.root / "complete"
        self.scribe("open", complete)
        self.scribe("append", complete, 0, 1, "lensx", self.payload("z.md", "z\n"))
        self.scribe("close", complete, "saturation", 0)
        for evidence in ("transcript.md", "TRANSCRIPT.SHA256", "turns", "turns/r0-s1.md"):
            with self.subTest(evidence=evidence):
                copy = self.root / "incomplete"
                shutil.copytree(complete, copy)
                target = copy / evidence
                shutil.rmtree(target) if target.is_dir() else target.unlink()
                self.scribe("verify", copy, rc=3)
                shutil.rmtree(copy)

    def test_empty_transcript_and_no_turns_rejected_despite_matching_checksum(self):
        complete = self.root / "complete"
        self.scribe("open", complete)
        self.scribe("append", complete, 0, 1, "lensx", self.payload("z.md", "z\n"))
        self.scribe("close", complete, "saturation", 0)
        copy = self.root / "incomplete"
        shutil.copytree(complete, copy)
        (copy / "transcript.md").write_bytes(b"")
        (copy / "TRANSCRIPT.SHA256").write_text(f"{sha256(b'')}  transcript.md\n")
        (copy / "turns/r0-s1.md").unlink()
        self.scribe("verify", copy, rc=3)


class ChainTests(Base):
    def setUp(self):
        super().setUp()
        self.ws = self.root / "record"
        self.scribe("open", self.ws)
        self.pl = self.root / "payload"
        self.pl.write_bytes(b"alpha\n```\n## Round 9\n")
        self.head1 = self.append(1)
        self.backup = self.root / "earlier"
        shutil.copytree(self.ws, self.backup)
        self.pl.write_bytes(b"beta without newline")
        self.head2 = self.append(2)

    def append(self, seat):
        out = self.scribe("append", self.ws, 0, seat, f"lens{seat}", self.pl)
        return next(l.split()[1] for l in out.splitlines() if l.startswith("chain-head "))

    def verify(self, rc=0, head=None):
        args = [] if head is None else ["--expect-head", head]
        return self.scribe("verify", self.ws, *args, rc=rc)

    def test_valid_and_moved_records(self):
        self.assertNotEqual(self.head1, self.head2)
        self.assertIn("local consistency only", self.verify())
        self.assertIn("caller-supplied head matched", self.verify(head=self.head2))
        moved = self.root / "moved"
        shutil.copytree(self.ws, moved)
        self.scribe("verify", moved, "--expect-head", self.head2)

    def test_expected_head_mismatch_and_invalid_arguments(self):
        self.verify(rc=3, head="0" * 64)
        self.scribe("verify", self.ws, "--expect-head", rc=2)
        self.scribe("verify", self.ws, "--expect-head", "not-a-hash", rc=2)

    def test_chain_format(self):
        prev = ""
        for line in (self.ws / "CHAIN.SHA256").read_text().splitlines():
            head, tag, turn, transcript = line.split()
            self.assertEqual(head, sha256((prev + tag + turn + transcript).encode()))
            prev = line

    def test_changed_removed_reordered_and_malformed_chain(self):
        path = self.ws / "CHAIN.SHA256"
        original = path.read_text()
        lines = original.splitlines(keepends=True)
        for changed in (
            original.replace(" r0-s2 ", " r0-s9 "),
            lines[0],
            "".join(reversed(lines)),
            "malformed\n",
            "",
            original + "\n",
            original.replace(" r0-s2 ", " ../../escape "),
        ):
            with self.subTest(changed=changed):
                path.write_text(changed)
                self.verify(rc=3)
        path.unlink()
        self.verify(rc=3, head=self.head2)

    def test_consistent_rollback_needs_retained_head(self):
        shutil.rmtree(self.ws)
        shutil.copytree(self.backup, self.ws)
        self.verify()  # earlier state is locally consistent; rollback needs the retained head
        self.verify(rc=3, head=self.head2)

    def test_consistent_forgery_needs_retained_head(self):
        other = self.root / "forged"
        self.scribe("open", other)
        self.pl.write_text("forged")
        self.scribe("append", other, 0, 1, "lens1", self.pl)
        self.scribe("append", other, 0, 2, "lens2", self.pl)
        shutil.rmtree(self.ws)
        shutil.copytree(other, self.ws)
        self.verify()
        self.verify(rc=3, head=self.head2)

    def test_recomputed_chain_reordering_rejected(self):
        path = self.ws / "CHAIN.SHA256"
        prev = ""
        rewritten = []
        for line in reversed(path.read_text().splitlines()):
            _, tag, turn, transcript = line.split()
            head = sha256((prev + tag + turn + transcript).encode())
            prev = f"{head} {tag} {turn} {transcript}"
            rewritten.append(prev)
        path.write_text("\n".join(rewritten) + "\n")
        self.verify(rc=3)

    def test_mutations_reject_broken_chain_before_writing(self):
        (self.ws / "CHAIN.SHA256").unlink()
        before = (self.ws / "transcript.md").read_bytes()
        self.scribe("append", self.ws, 0, 3, "lens3", self.pl, rc=3)
        self.scribe("close", self.ws, "cap", 0, rc=3)
        self.assertEqual(before, (self.ws / "transcript.md").read_bytes())
        self.assertFalse((self.ws / "turns/r0-s3.md").exists())

    def test_closed_head_and_no_automatic_commit(self):
        before = self.git("rev-parse", "HEAD").stdout
        out = self.scribe("close", self.ws, "saturation", 0)
        head = next(l.split()[1] for l in out.splitlines() if l.startswith("close-head: "))
        self.assertNotEqual(head, self.head2)
        self.verify(head=head)
        self.verify(rc=3, head=self.head2)
        self.assertFalse((self.ws / ".tribunal-active").exists())
        self.assertEqual(before, self.git("rev-parse", "HEAD").stdout)

    def test_seat_tamper_and_missing_seat(self):
        path = self.ws / "seat-1-lens1.md"
        path.write_text("changed")
        self.verify(rc=3)
        path.unlink()
        self.verify(rc=3)

    def test_relative_path_commit_check(self):
        self.git("add", "record/turns", "record/seat-1-lens1.md")
        self.git("commit", "-qm", "record touched")
        self.scribe("append", "record", 0, 3, "lens3", self.pl, rc=3)

    def test_checksum_history_tamper(self):
        path = self.ws / "TRANSCRIPT.SHA256"
        lines = path.read_text().splitlines(keepends=True)
        path.write_text("0" * 64 + lines[0][64:] + lines[1])
        self.verify(rc=3)

    def test_open_rejects_chain_and_checksum_leftovers(self):
        for name in ("CHAIN.SHA256", "TRANSCRIPT.SHA256"):
            ws = self.root / name
            ws.mkdir()
            (ws / name).write_text("leftover")
            self.scribe("open", ws, rc=1)


if __name__ == "__main__":
    unittest.main()

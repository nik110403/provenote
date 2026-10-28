import sys
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "leak-check.sh"
HOME_PATH = "/ho" + "me/x/notes"  # built in pieces so this file is itself clean
IP = "10.1." + "2.3"
EMAIL = "jane@" + "example.org"
PUBLIC_HANDLE = "nik" + "110403"
AUTHOR_FAMILY = "Khosravi" + "pour"
PUBLIC_URLS = tuple(
    "https://github.com/" + PUBLIC_HANDLE + "/" + repo
    for repo in ("provenote", "ai-architecture")
)
PUBLIC_DOCS = (
    "README.md",
    "INSTALL.md",
    "CATALOG.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "docs/adapters.md",
    "docs/workflow.md",
)


def _find_bash(is_windows=None):
    """Absolute path of a usable bash, or None.

    On Windows, CreateProcess resolves a bare "bash" to the WSL launcher in System32
    before PATH, so prefer Git for Windows' bash and never accept the System32 one.
    """
    is_windows = os.name == "nt" if is_windows is None else is_windows
    found = shutil.which("bash")
    if not is_windows:
        return str(Path(found).resolve()) if found else None
    sysdir = os.path.normcase(
        os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "")
    )
    if found and not os.path.normcase(os.path.abspath(found)).startswith(sysdir):
        return str(Path(found).resolve())
    git = shutil.which("git")
    if git:
        git_path = Path(git).resolve()
        parent = git_path.parent
        if parent.name.lower() == "bin" and parent.parent.name.lower() == "mingw64":
            base = parent.parent.parent  # <Git>\mingw64\bin\git.exe
        elif parent.name.lower() in ("cmd", "bin"):
            base = parent.parent  # <Git>\cmd\git.exe or <Git>\bin\git.exe
        else:
            base = None
        for rel in ("bin/bash.exe", "usr/bin/bash.exe"):
            if base and (base / rel).is_file():
                return str(base / rel)
    return None


class FindBash(unittest.TestCase):
    def test_relative_path_result_becomes_absolute(self):
        with mock.patch(__name__ + ".shutil.which", return_value="relative/bash"):
            self.assertEqual(_find_bash(), str(Path("relative/bash").resolve()))

    def test_windows_mingw_git_layout_finds_usr_bash(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = Path(tmp) / "Git"
            executable = git / "mingw64/bin/git.exe"
            bash = git / "usr/bin/bash.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            bash.parent.mkdir(parents=True)
            bash.touch()
            with (
                mock.patch(
                    __name__ + ".shutil.which",
                    side_effect=lambda name: str(executable) if name == "git" else None,
                ),
            ):
                self.assertEqual(_find_bash(is_windows=True), str(bash.resolve()))

    def test_windows_standard_git_layout_finds_bin_bash(self):
        with tempfile.TemporaryDirectory() as tmp:
            git = Path(tmp) / "Git"
            executable = git / "cmd/git.exe"
            bash = git / "bin/bash.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            bash.parent.mkdir(parents=True)
            bash.touch()
            with mock.patch(
                __name__ + ".shutil.which",
                side_effect=lambda name: str(executable) if name == "git" else None,
            ):
                self.assertEqual(_find_bash(is_windows=True), str(bash.resolve()))

    def test_windows_system_bash_without_git_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            system_root = Path(tmp) / "Windows"
            stub = system_root / "System32/bash.exe"
            with (
                mock.patch.dict(os.environ, {"SystemRoot": str(system_root)}),
                mock.patch(
                    __name__ + ".shutil.which",
                    side_effect=lambda name: str(stub) if name == "bash" else None,
                ),
            ):
                self.assertIsNone(_find_bash(is_windows=True))


BASH = _find_bash()


@unittest.skipUnless(
    BASH, "leak-check.sh requires a non-WSL bash (e.g. Git for Windows)"
)
class LeakCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        self.deny = Path(self.tmp.name) / "denylist"
        self.deny.write_text("# comment\n\nSecretProject\n", encoding="utf-8")
        self.git("init", "-q")
        self.git("config", "user.email", "t@users.noreply.github.com")
        self.git("config", "user.name", "t")

    def git(self, *a):
        subprocess.run(["git", *a], cwd=self.repo, check=True, capture_output=True)

    def run_check(self, content, *args, deny=True):
        (self.repo / "f.txt").write_text(content + "\n", encoding="utf-8")
        self.git("add", "f.txt")
        env = dict(
            os.environ,
            PROVENOTE_DENYLIST=str(
                self.deny if deny else self.tmp.name + "/missing"
            ),
        )
        return subprocess.run(
            [BASH, str(SCRIPT), *args],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_home_path(self):
        r = self.run_check("see " + HOME_PATH)
        self.assertEqual(r.returncode, 1)
        self.assertIn("f.txt:1", r.stdout)

    def test_ip(self):
        self.assertEqual(self.run_check("host " + IP + " here").returncode, 1)

    def test_loopback_and_version_ok(self):
        self.assertEqual(self.run_check("127.0.0.1 0.0.0.0 v1.2.3.4").returncode, 0)

    def test_personal_email(self):
        self.assertEqual(self.run_check("mail " + EMAIL).returncode, 1)

    def test_source_md_email_exempt_but_denylist_not(self):
        d = self.repo / "02_sources" / "md"
        d.mkdir(parents=True)
        (d / "paper.md").write_text("contact " + EMAIL + "\n", encoding="utf-8")
        self.assertEqual(self.run_check("clean").returncode, 0)
        (d / "paper.md").write_text(
            "contact " + EMAIL + " SecretProject\n", encoding="utf-8"
        )
        self.git("add", "-A")
        self.assertEqual(self.run_check("clean").returncode, 1)

    def test_author_lines_exempt_only_in_metadata(self):
        env = dict(os.environ, PROVENOTE_DENYLIST=str(self.deny))

        def check(name, content):
            (self.repo / name).write_text(content + "\n", encoding="utf-8")
            self.git("add", name)
            r = subprocess.run(
                [BASH, str(SCRIPT)],
                cwd=self.repo,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.git("rm", "-q", "--cached", name)
            return r.returncode

        self.assertEqual(check("LICENSE", "Copyright (c) 2026 SecretProject"), 0)
        self.assertEqual(check("LICENSE", "Thanks to SecretProject"), 1)
        self.assertEqual(check("README.md", "Copyright (c) 2026 SecretProject"), 1)
        self.assertEqual(
            check("README.md", "/plugin marketplace add SecretProject/provenote"), 0
        )
        self.assertEqual(check("README.md", "see SecretProject/provenote"), 1)

    def test_citation_metadata_allowed_on_exact_lines_only(self):
        self.deny.write_text(
            "secretproject\n" + PUBLIC_HANDLE + "\n" + AUTHOR_FAMILY.lower() + "\n",
            encoding="utf-8",
        )
        env = dict(os.environ, PROVENOTE_DENYLIST=str(self.deny))
        family = '  - family-names: "' + AUTHOR_FAMILY + '"'
        creators = '  "creators": [{ "name": "' + AUTHOR_FAMILY + ', Nik" }],'
        repo_line = 'repository-code: "https://github.com/' + PUBLIC_HANDLE + '/provenote"'
        url_line = 'url: "https://' + PUBLIC_HANDLE + '.github.io/provenote/"'
        for name, text, want in (
            ("CITATION.cff", family, 0),
            ("CITATION.cff", family + " # x", 1),
            ("CITATION.cff", '  - family-names: "Secretproject"', 1),
            ("CITATION.cff", 'title: "' + AUTHOR_FAMILY + '"', 1),
            ("CITATION.cff", repo_line, 0),
            ("CITATION.cff", url_line, 0),
            ("CITATION.cff", repo_line.replace("provenote", "secretproject"), 1),
            (".zenodo.json", creators, 0),
            (".zenodo.json", '  "creators": [{ "name": "Secretproject, Nik" }],', 1),
            (".zenodo.json", creators.replace("Nik", "Secretproject"), 1),
            ("README.md", family, 1),
            (
                "plugins/provenote/README.md",
                "https://github.com/" + PUBLIC_HANDLE + "/provenote secretproject",
                1,
            ),
        ):
            (self.repo / name).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / name).write_text(text + "\n", encoding="utf-8")
            self.git("add", name)
            r = subprocess.run(
                [BASH, str(SCRIPT)],
                cwd=self.repo,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.git("rm", "-q", "--cached", name)
            self.assertEqual(r.returncode, want, (name, text, r.stderr))

    def test_banner_footer_default_allowed_on_exact_line_only(self):
        line = '    p.add_argument("--footer", default="secretproject.com")'
        self.deny.write_text("secretproject\n", encoding="utf-8")
        env = dict(os.environ, PROVENOTE_DENYLIST=str(self.deny))
        for name, text, want in (
            ("tools/banner/bin/make-banner", line, 0),
            ("tools/banner/bin/make-banner", line + " # secretproject", 1),
            ("tools/other", line, 1),
        ):
            path = self.repo / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text + "\n", encoding="utf-8")
            self.git("add", name)
            r = subprocess.run(
                [BASH, str(SCRIPT)],
                cwd=self.repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.git("reset", "-q")
            self.assertEqual(r.returncode, want, name + text)

    def test_denylist_case_insensitive(self):
        self.assertEqual(self.run_check("about SECRETPROJECT today").returncode, 1)

    def test_denylist_path_preserves_spaces_and_backslashes(self):
        # Windows supplies native separators; POSIX can exercise literal escapes.
        directory = (
            "paths with spaces" if os.name == "nt" else r"paths with spaces\temp\Users"
        )
        self.deny = Path(self.tmp.name) / directory / "denylist"
        self.deny.parent.mkdir()
        self.deny.write_text("SecretProject\n", encoding="utf-8")
        for mode in ("--staged", "--tree", "--history"):
            with self.subTest(mode=mode):
                if mode == "--history":
                    self.git("commit", "-qm", "fixture")
                result = self.run_check("about SECRETPROJECT today", mode)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("f.txt:1: [denylist] term #1", result.stdout)

    def test_noreply_ok(self):
        r = self.run_check("12345+u@users.noreply.github.com and noreply@example.org")
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_clean_ok(self):
        self.assertEqual(self.run_check("nothing here").returncode, 0)

    def test_missing_denylist_still_runs(self):
        r = self.run_check("clean", deny=False)
        self.assertEqual(r.returncode, 0)
        self.assertIn("skipping denylist", r.stderr)
        self.assertEqual(self.run_check(EMAIL, deny=False).returncode, 1)

    def test_tree_and_history(self):
        (self.repo / "f.txt").write_text("host " + IP + "\n", encoding="utf-8")
        self.git("add", "f.txt")
        self.git("commit", "-qm", "x")
        (self.repo / "f.txt").write_text("clean\n", encoding="utf-8")
        self.git("commit", "-qam", "y")
        env = dict(os.environ, PROVENOTE_DENYLIST=str(self.deny))
        run = lambda m: subprocess.run(
            [BASH, str(SCRIPT), m],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(run("--tree").returncode, 0)
        h = run("--history")
        self.assertEqual(h.returncode, 1)
        self.assertIn("f.txt:1", h.stdout)

    def check_reference(self, name, content, expected, mode="--staged", kind=None):
        self.deny.write_text(PUBLIC_HANDLE + "\nprivatefixtureword\n", encoding="utf-8")
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + "\n", encoding="utf-8")
        self.git("add", name)
        env = dict(os.environ, PROVENOTE_DENYLIST=str(self.deny))
        try:
            result = subprocess.run(
                [BASH, str(SCRIPT), mode],
                cwd=self.repo,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            if kind:
                self.assertIn("[" + kind + "]", result.stdout)
        finally:
            self.git("rm", "-q", "--cached", name)
            path.unlink()

    def test_public_doc_exact_urls(self):
        for name in PUBLIC_DOCS:
            for url in PUBLIC_URLS:
                for mode in ("--staged", "--tree"):
                    with self.subTest(name=name, url=url, mode=mode):
                        self.check_reference(
                            name, "[public](" + url + ") " + url, 0, mode
                        )

    def test_public_urls_do_not_hide_other_deny_terms(self):
        for url in PUBLIC_URLS:
            for text in (
                url + " privatefixtureword",
                "PRIVATEFIXTUREWORD " + url,
                url + " " + PUBLIC_HANDLE,
            ):
                with self.subTest(text=text):
                    self.check_reference("README.md", text, 1, kind="denylist")

    def test_public_handle_bare_is_denied(self):
        for name in PUBLIC_DOCS:
            with self.subTest(name=name):
                self.check_reference(name, PUBLIC_HANDLE, 1, kind="denylist")

    def test_public_url_lookalikes_are_denied(self):
        for url in PUBLIC_URLS:
            for suffix in ("-private", "ten", ".git", "_private", "/private"):
                with self.subTest(url=url, suffix=suffix):
                    self.check_reference("README.md", url + suffix, 1, kind="denylist")
            self.check_reference("README.md", "x" + url, 1, kind="denylist")

    def site_page_case(self, content, expected):
        self.check_reference(
            "site/index.html", content, expected, kind="denylist" if expected else None
        )

    def test_site_page_allowances_are_anchored(self):
        owner = PUBLIC_HANDLE
        base = "https://github.com/" + owner + "/provenote"
        install = "    <pre><code>/plugin marketplace add " + owner + "/provenote</code></pre>"
        # accepted forms
        self.site_page_case('<a href="' + base + '">x</a>', 0)
        self.site_page_case('<a href="' + base + '/blob/main/docs/verification.md">x</a>', 0)
        self.site_page_case(install, 0)
        # trailing content after the install line, wrong owner, path tricks
        self.site_page_case(install + '<a href="https://github.com/' + owner + '/privatefixtureword">x</a>', 1)
        self.site_page_case(install + " privatefixtureword", 1)
        self.site_page_case(
            "    <pre><code>/plugin marketplace add privatefixtureword/provenote</code></pre>", 1
        )
        for tail in (
            "/blob/main/../../privatefixtureword",
            "/blob/main/privatefixtureword/notes.md",
            "/blob/main/PRIVATEFIXTUREWORD/notes.md",
            "/tree/main//privatefixtureword",
            "-privatefixtureword",
            "/privatefixtureword",
        ):
            with self.subTest(tail=tail):
                self.site_page_case('<a href="' + base + tail + '">x</a>', 1)
        self.site_page_case(
            '<A HREF="' + base.upper().replace("HTTPS", "https") + "/BLOB/MAIN/PRIVATEFIXTUREWORD" + '">x</A>', 1
        )
        self.site_page_case('<a href="' + base + '">x</a> privatefixtureword', 1)
        self.site_page_case('<a href="x' + base + '">x</a>', 1)
        # the allowances apply to the exact file label only
        for name in ("docs/site/index.html", "a/site/index.html", "site/index.html.bak"):
            with self.subTest(name=name):
                self.check_reference(name, '<a href="' + base + '">x</a>', 1, kind="denylist")

    def test_site_pages_url_allowance_is_anchored(self):
        owner = PUBLIC_HANDLE
        pages = "https://" + owner + ".github.io/provenote/"
        self.site_page_case('<link rel="canonical" href="' + pages + '">', 0)
        self.site_page_case('<meta property="og:image" content="' + pages + 'social-preview.png">', 0)
        self.check_reference("README.md", pages, 1, kind="denylist")
        for bad in (
            "see " + pages,
            "https://" + owner + ".github.io/other/",
            pages + "privatefixtureword.png",
            "https://" + owner + ".github.io.evil.com/provenote/",
            "https://x" + owner + ".github.io/provenote/",
        ):
            with self.subTest(bad=bad):
                self.site_page_case('<a href="' + bad + '">x</a>' if "see" not in bad else bad, 1)
        self.site_page_case('<a href="' + pages + '">' + owner + "</a>", 1)

    def test_public_urls_unexpected_files_are_denied(self):
        for name in ("other.md", "nested/README.md", "docs/other.md"):
            for url in PUBLIC_URLS:
                with self.subTest(name=name, url=url):
                    self.check_reference(name, url, 1, kind="denylist")

    def test_public_urls_keep_other_layers(self):
        for url in PUBLIC_URLS:
            for value, kind in (
                (HOME_PATH, "home-path"),
                (EMAIL, "email"),
                (IP, "ipv4"),
            ):
                with self.subTest(url=url, kind=kind):
                    self.check_reference("INSTALL.md", url + " " + value, 1, kind=kind)

    def test_install_exact_marketplace_command(self):
        command = "/plugin marketplace add " + PUBLIC_HANDLE + "/provenote"
        self.check_reference("INSTALL.md", command, 0)
        self.check_reference(
            "INSTALL.md", command + " privatefixtureword", 1, kind="denylist"
        )
        self.check_reference(
            "INSTALL.md",
            command.replace(PUBLIC_HANDLE, "privatefixtureword"),
            1,
            kind="denylist",
        )
        self.check_reference("CATALOG.md", command, 1, kind="denylist")


if __name__ == "__main__":
    unittest.main()

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SH = ROOT / "scripts/install-deps.sh"
PS1 = ROOT / "scripts/install-deps.ps1"
BASH = shutil.which("bash")
SUDO = "" if hasattr(os, "geteuid") and os.geteuid() == 0 else "sudo "


@unittest.skipIf(sys.platform == "win32" or not BASH, "bash script; not for Windows")
class InstallDepsSh(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.dir = Path(temporary.name)
        self.bin = self.dir / "bin"
        self.bin.mkdir()

    def stub(self, name, body="exit 0"):
        path = self.bin / name
        path.write_text("#!%s\n%s\n" % (BASH, body))
        path.chmod(0o755)

    def run_script(self, kernel="Linux", release=None, *args):
        self.stub("uname", "echo %s" % kernel)
        rel = self.dir / "os-release"
        rel.write_text(release or "")
        # PATH holds only the stubs, so host tools never leak into the result
        env = {"PATH": str(self.bin), "RK_OS_RELEASE": str(rel)}
        return subprocess.run([BASH, str(SH), "--dry-run", *args], env=env,
                              capture_output=True, text=True)

    def test_macos_brew(self):
        self.stub("brew")
        r = self.run_script("Darwin", None)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("  brew install poppler pandoc\n", r.stdout)

    def test_macos_without_brew(self):
        r = self.run_script("Darwin", None)
        self.assertEqual(r.returncode, 4)
        self.assertIn("https://brew.sh", r.stderr)

    def test_ubuntu_apt(self):
        r = self.run_script("Linux", 'ID=ubuntu\nID_LIKE=debian\n')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("  %sapt-get update\n" % SUDO, r.stdout)
        self.assertIn("  %sapt-get install -y poppler-utils pandoc\n" % SUDO, r.stdout)

    def test_derivative_uses_id_like(self):
        r = self.run_script("Linux", 'ID="linuxmint"\nID_LIKE="ubuntu debian"\n')
        self.assertIn("apt-get install", r.stdout)

    def test_fedora_dnf(self):
        r = self.run_script("Linux", "ID=fedora\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("  %sdnf install -y poppler-utils pandoc\n" % SUDO, r.stdout)

    def test_unknown_distro_exits_3(self):
        r = self.run_script("Linux", "ID=arch\n")
        self.assertEqual(r.returncode, 3)
        self.assertIn("Install manually", r.stderr)

    def test_unknown_kernel_exits_3(self):
        self.assertEqual(self.run_script("FreeBSD").returncode, 3)

    def test_installed_tool_skipped(self):
        self.stub("pdftotext")
        r = self.run_script("Linux", "ID=fedora\n")
        self.assertIn("skip: pdftotext already installed", r.stdout)
        self.assertIn("dnf install -y pandoc\n", r.stdout)
        self.assertNotIn("poppler", r.stdout)

    def test_everything_installed_is_noop(self):
        self.stub("pdftotext")
        self.stub("pandoc")
        r = self.run_script("Linux", "ID=fedora\n")
        self.assertEqual(r.returncode, 0)
        self.assertIn("Nothing to install.", r.stdout)
        self.assertNotIn("dnf", r.stdout)

    def test_workflow_and_typst(self):
        self.stub("brew")
        r = self.run_script("Darwin", None, "--workflow", "pdf", "--typst")
        self.assertIn("  brew install poppler typst\n", r.stdout)
        self.assertNotIn("pandoc", r.stdout)
        r = self.run_script("Darwin", None, "--workflow", "build")
        self.assertIn("  brew install pandoc\n", r.stdout)

    def test_apt_typst_is_hint_not_install(self):
        r = self.run_script("Linux", "ID=ubuntu\n", "--typst")
        self.assertIn("apt-get install -y poppler-utils pandoc\n", r.stdout)
        self.assertNotIn("typst\n", r.stdout.split("note:")[0])
        self.assertIn("https://github.com/typst/typst#installation", r.stdout)

    def test_function_is_not_installed_tool(self):
        # type -P ignores functions/aliases; a pdftotext function must not count
        self.stub("uname", "echo Linux")
        rel = self.dir / "os-release"
        rel.write_text("ID=fedora\n")
        env = {"PATH": str(self.bin), "RK_OS_RELEASE": str(rel),
               "BASH_ENV": str(self.dir / "fn.sh")}
        (self.dir / "fn.sh").write_text("pdftotext() { :; }\n")
        r = subprocess.run([BASH, str(SH), "--dry-run"], env=env, capture_output=True, text=True)
        self.assertNotIn("skip: pdftotext", r.stdout)

    def test_relative_name_from_scripts_dir_with_cdpath(self):
        # bash 3.2 is the target (macOS /bin/bash); empty-array guards are in the script
        self.stub("pdftotext")
        self.stub("pandoc")
        self.stub("uname", "echo Linux")
        rel = self.dir / "os-release"
        rel.write_text("ID=fedora\n")
        env = {"PATH": str(self.bin), "RK_OS_RELEASE": str(rel), "CDPATH": str(self.dir)}
        r = subprocess.run([BASH, "install-deps.sh", "--dry-run"], env=env, cwd=SH.parent,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Nothing to install.", r.stdout)

    def test_missing_doctor_fails_before_install(self):
        copy = self.dir / "scripts"
        copy.mkdir()
        shutil.copy(SH, copy / "install-deps.sh")
        self.stub("uname", "echo Linux")
        r = subprocess.run([BASH, str(copy / "install-deps.sh"), "--dry-run"],
                           env={"PATH": str(self.bin)}, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("doctor not found", r.stderr)
        self.assertNotIn("Commands to run", r.stdout)

    def test_bad_workflow_exits_2(self):
        self.assertEqual(self.run_script("Linux", "ID=fedora\n", "--workflow", "word").returncode, 2)


@unittest.skipUnless(shutil.which("pwsh"), "pwsh not available")
class InstallDepsPs1(unittest.TestCase):
    def test_dry_run(self):
        r = subprocess.run(["pwsh", "-NoProfile", "-File", str(PS1), "-DryRun", "-Typst"],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue("Commands to run:" in r.stdout or "Nothing to install." in r.stdout)


if __name__ == "__main__":
    unittest.main()

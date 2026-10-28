# Read-only setup diagnostics

Run from the research project root, using the intended plugin's helper:

```sh
python3 /path/to/provenote/bin/doctor --workflow pdf
python3 /path/to/provenote/bin/doctor --workflow all --json
```

In PowerShell use `py -3 "C:\path\to\provenote\bin\doctor" --workflow word`.
If Python cannot start, select/install Python 3.9+ first; no Python program can
diagnose an interpreter that cannot parse or launch it.

Missing tools? [`scripts/install-deps.sh` / `.ps1`](../INSTALL.md#install-the-external-tools-one-command)
install them and finish by running `doctor`.

## Workflows and results

| Workflow | Required external tools |
|---|---|
| `pdf` | Poppler's `pdftotext` |
| `build` | pandoc |
| `word` | None: Word checks use Python's standard library |
| `all` (default) | Both pdftotext and pandoc |

All workflows check Python >=3.9, helper shadowing on PATH, Windows SystemRoot's
`System32\bash.exe` WSL stub, Windows stdout/stderr UTF-8 encoding, and project
directory access metadata. New-project scaffolding can use `word` from the
target's existing parent: no PDF/build dependency is needed.

The minimum pandoc is **2.11**, because `build-paper` uses integrated
`--citeproc`; its other baseline arguments and HTML/DOCX writers need no newer
version. If Typst is on PATH, `build-paper` selects `--pdf-engine=typst`, requiring
**3.1**, so doctor raises the minimum for that environment. PDF engine availability,
OCR, decryption, document validity and build/verification results are not certified.

Exit 0 means zero setup findings; exit 1 means one or more findings; invalid CLI
arguments exit 2. JSON contains `schema_version: 1`, `workflow` and `findings`.
Each finding has a stable `id`, `severity`, `evidence`, and `fixes` keyed by
`windows`, `macos`, `linux`. Repeated IDs are possible for different helpers or
directories; use their evidence to distinguish them. Identical observations
produce identical JSON; evidence naturally changes with paths or environment.
Text output escapes path/control characters; JSON is ASCII-safe on old consoles.

Finding IDs: `python.too-old`, `pdftotext.missing`, `pdftotext.unusable`,
`pandoc.missing`, `pandoc.unusable`, `pandoc.version-unknown`, `pandoc.too-old`,
`path.helper-shadowed`, `path.windows-bash-stub`, `console.non-utf8`,
`adapter.stale-helper`, `project.not-writable`. All currently have severity `error`.
Package suggestions include winget/choco, brew, and apt/dnf alternatives; these
are proposals, not commands executed by doctor. Use only an already permitted
package manager and existing rights; never escalate privileges.

## Install missing tools

`scripts/install-deps.sh` (macOS, Debian/Ubuntu, Fedora) and `scripts/install-deps.ps1`
(Windows) install the missing tools using the package names above, ask before running,
and finish by rerunning doctor. Use `--dry-run` / `-DryRun` to preview, `--typst` /
`-Typst` for the optional Typst engine, `--workflow pdf|build|all` to limit scope.

## Read-only boundaries

Doctor launches only resolved pdftotext/pandoc paths with fixed version arguments,
no shell and a three-second timeout per probe. It performs no network requests,
installations, shell evaluation or data-write probes. Version probes run the
executables selected by PATH: use a trusted PATH, as with the other kit helpers.
Directory checks use `os.access` for the root and existing numbered project
directories (including notes/lit and sources/pdf/md). This is a metadata hint,
not proof that a future write will succeed under every ACL or mount condition.

An adapter helper is reported stale only when both files exist and their bytes
differ from the plugin containing this doctor. That plugin must have the
`provenote` marker at `.claude-plugin/plugin.json`; no checkout/cache path is
guessed. Comparison covers `.agents/skills/provenote/bin` under the project.
Standalone adapters without the marker cannot establish a canonical plugin and
skip comparison. Missing/unreadable files and other adapter locations are not
proof of stale copies; this is not an adapter completeness check. No copy is
overwritten. Helper PATH checks compare against this doctor's own bin directory.

## Recovery

Follow the bundled [agent recovery template](../plugins/provenote/templates/agent-recovery.md):
doctor → smallest proposed fix → existing permission approval → apply → rerun
doctor → retry the original command. Allow at most two attempts per finding,
then report evidence and remaining work. Never edit research notes, sources,
manifests, hashes, bindings, verification code or check rules to repair setup.
A verification FAIL remains a FAIL; doctor never inspects or reclassifies it.

Tests simulate Windows path resolution and console encoding. Native Windows
execution, real package installs and permission/ACL behavior require separate
platform evidence; mocked checks do not establish native Windows support.

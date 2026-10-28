# Set up Claude Code or Codex for source-checked research

Written with Claude; reviewed by the Provenote author (review pending)

Date: 2026-10-26 · Tested with: research-kit 0.1.3 (the name before Provenote 0.2.0) at commit `adfce82` · Claude Code 2.1.310 (observed on Linux)

> **Status: preview, untested on real Mac/Windows.** The commands below are copied from
> this repository's own documents, and the quote check (Check 2) was run on Linux only. Nobody
> has yet followed this guide start to finish on a clean Mac or Windows PC. If a step does not
> behave as described, use [section 9](#9-when-you-are-stuck) and tell us.

This guide is for a researcher or student who uses the Claude or ChatGPT apps and has never
opened a terminal. Pick **one** assistant and follow only that route:

- **Route A: Claude Code + Provenote.** Follow sections 1 to 9 below, in order.
- **Route B: Codex + Provenote.** Read section 1, then follow [section C](#c-codex-route),
  then section 9 if you get stuck. Skip sections 2 to 8.

Do not mix the two routes. If you have no preference, Route A is the one that has been checked
more closely; Route B has the limits described in [C7](#c7-what-is-not-the-same-as-claude-code).

## 1. What you get, and what this does NOT do

You get a set of skills and helper programs that turn a reading list into source-grounded
notes, and check each quotation in your notes against a text copy of the source, on the page
you cite.

It does **not** tell you a quote is accurate to the original PDF, that it supports your claim,
or that your claim is true. A passing quote check means only: "these words are on this page of
this text copy of the source." Whether they mean what you say they mean is still your judgment
(and a model's reading of it needs your review). See [what is verified](verification.md).

## 2. Before you start

- **A Claude account that can use Claude Code, and its cost.** Plans and prices change, so this
  guide quotes none. Read the official page first:
  <https://docs.claude.com/en/docs/claude-code/setup>
- **A computer check.** A Mac or Windows PC with an internet connection, and permission to
  install programs. Close nothing yet; you will open a command window in the next section.
- **About Python.** Provenote's helper programs need Python 3.9 or newer. You will check this
  in section 7 and only if you get that far.

**DONE:** You have an account you can sign in with, and you have read the cost on the official page.
**STUCK:** You cannot tell which plan includes Claude Code. Stop here and read the official page
again, or ask in the issue tracker (section 9). Do not guess.

## 3. Install Claude Code

Claude Code runs in a command window ("terminal"). You type or paste one line at a time and
press Return (Mac) or Enter (Windows).

For the current install steps on your system, the official page is the authority:
<https://docs.claude.com/en/docs/claude-code/setup>. If the commands below differ from that
page, follow the official page.

<details>
<summary><b>macOS</b></summary>

1. Open **Terminal**: press Command + Space, type `Terminal`, press Return.
2. Paste this line and press Return. Wait until a new typing line appears.

From the official setup page: <https://docs.claude.com/en/docs/claude-code/setup>

```sh
curl -fsSL https://claude.ai/install.sh | bash
```

3. Close the Terminal window completely, open a new one, and check:

```sh
claude --version
```

**DONE:** a version number is printed.
**STUCK:** "command not found" or an error. Do not run the installer again and again. Copy the
exact text and use section 9.

</details>

<details>
<summary><b>Windows</b></summary>

1. Open the official page above and choose its **Windows** instructions for **PowerShell**. This
   guide does not repeat the Windows installer line; use the one on that page.
2. Click Start, type `PowerShell`, open it. Run the line from the official page. Wait until a new
   typing line appears.
3. Close **every** PowerShell window, open a new one, and check:

```powershell
claude --version
```

**DONE:** a version number is printed.
**STUCK:** "not recognized" or an error. Do not reinstall repeatedly. Copy the exact text and
use section 9.

</details>

**Sign in once.** Type `claude` and press Return/Enter, then follow the on-screen choices to sign in
with your Claude account. A browser may open; sign in there and return to the command window.

**DONE:** Claude Code shows a prompt where you can type a message.
**STUCK:** a sign-in loop or a plan error. Copy the exact text and use section 9.

## 4. Git pre-flight

**Why:** the plugin marketplace route downloads Provenote from GitHub, and in practice that
needs Git on your computer. (The README says the Codex route can start without Git, but the
Claude Code route needs Git.)

Check whether Git is present, in a normal command window (not inside Claude Code):

```sh
git --version
```

**DONE:** a version number is printed (for example `git version 2.x`). Go to section 5.

**Not present?** Install Git from <https://git-scm.com/downloads>, close the command window, open a
new one, and run `git --version` again. On a Mac the first `git --version` may instead offer to
install Apple's developer tools; accepting installs Git.

**STUCK:** still no version number after a restart. Copy the exact text and use section 9.

## 5. Install Provenote

Start Claude Code (`claude`), then type these two lines one after the other, each followed by
Return/Enter. They are copied from [README.md](../README.md) and [INSTALL.md](../INSTALL.md):

```text
/plugin marketplace add nik110403/provenote
/plugin install provenote@provenote
```

This installs the packaged skills and roles. It does not install Python, Poppler, pandoc or R.
Do not replace your existing settings, `CLAUDE.md` or permissions with anything from this
collection.

**Then restart Claude Code:** type `/exit` (or close the window), open a new command window, and run
`claude` again.

**DONE:** after the restart, no error was shown.
**STUCK:** an error after either `/plugin` line. Copy it exactly and use section 9.

## 6. Check 1: discovery

In Claude Code, ask:

```text
List the Provenote skills you can see. Do not run any tool yet.
```

**DONE:** you see the Provenote skills named in the [README](../README.md), such as
`new-research-project`, `literature-search`, `pdf-to-markdown`, `literature-notes`,
`review-against-notes`, `paper-build`, `analysis-pipeline` and `tribunal`.

This proves **discovery only**: Claude can see the instructions. It does **not** prove the helper
programs run. That is Check 2.

**STUCK:** no Provenote skills listed. Repeat the restart in section 5 once. Still nothing: use section 9.

## 7. Check 2: the installed helper

This runs the helper that your plugin install provides, on a small bundled example, so you see
real PASS and FAIL lines. It needs Python 3.9 or newer.

**a. Check Python** in a normal command window.

<details>
<summary><b>macOS</b></summary>

```sh
python3 --version
```

</details>

<details>
<summary><b>Windows</b></summary>

```powershell
py -3 --version
```

If `py -3` is not recognised, try `python --version`. On Windows the launcher is named `python`
or `py -3`, not `python3`.

</details>

**DONE:** it prints Python 3.9 or newer.
**Not present or older?** Install from the official pages linked in
[INSTALL.md](../INSTALL.md): [Windows](https://www.python.org/downloads/windows/) or
[macOS](https://www.python.org/downloads/macos/). Close and reopen the command window, then
check again.

**b. Get the example folder.** On the [Provenote GitHub page](https://github.com/nik110403/provenote),
choose **Code → Download ZIP** and extract it. The extracted folder is called
`provenote-main`. "Download ZIP" gives you the latest version of the branch, which may be newer
than the commit this guide was tested with. Inside it, the folder `examples/basic` holds two
open-access papers, their text copies, two notes, and one note with a planted fake quote.

**c. Open Claude Code with `examples/basic` as the working folder.** In your command window,
`cd` into that folder (type `cd `, then drag the folder into the window and press Return/Enter),
and run `claude`.

**d. Ask Claude to run the INSTALLED helper, not a copy from the folder:**

```text
Use the installed Provenote plugin's verify-quotes helper, not any copy inside the downloaded
provenote folder (neither examples/basic nor ../../plugins/provenote/bin). The helper path
must be under Claude Code's plugin install location. If it is inside the downloaded folder, stop
and tell me instead of running it.
First show me the full path of the helper you are using. Then run it with --strict on the
files in 01_notes/lit/. Then run it with --strict on the files in 01_notes/negative/.
Show me the complete output of both runs and each exit code.
```

**What you should see (observed on Linux, research-kit 0.1.3):**

- First run: 14 lines, each starting `PASS` (8 for `kireyev2026pricebench.md`, 6 for
  `lei2023financial.md`), and exit code 0.
- Second run: exactly one line, `FAIL lei2023financial.md: quote 1 (p. 1): text not found in source`,
  and exit code 1. **That failure is expected**: the note contains an invented quote on purpose,
  and the check is meant to catch it.
- The helper path shown in step d must be under Claude Code's plugin install location, and
  must NOT be anywhere inside your downloaded (extracted ZIP) Provenote folder.

**DONE:** 14 PASS, then the one expected FAIL.
**STUCK:** a different count, no FAIL, a Python error, or the helper path is inside
your downloaded provenote folder (for example `examples/basic` or `plugins/provenote/bin`
there). In that case do not trust the result: ask Claude to reinstall or locate the plugin
(section 5), then repeat step d. Copy the exact output and use section 9 if it persists.

**Running it yourself (optional).** Ask Claude: "Print the absolute folder of the installed
Provenote plugin." Use that folder as `KIT` below, then run from `examples/basic`. Commands follow
[INSTALL.md](../INSTALL.md) and [codex/SKILL.md](codex/SKILL.md):

<details>
<summary><b>macOS</b></summary>

```sh
python3 "$KIT/bin/verify-quotes" --help
python3 "$KIT/bin/verify-quotes" --strict 01_notes/lit/*.md
python3 "$KIT/bin/verify-quotes" --strict 01_notes/negative/*.md
```

Before these, set `KIT` to the folder Claude printed, as an absolute path in quotes, in the form
`KIT="/absolute/path/to/plugins/provenote"`.

</details>

<details>
<summary><b>Windows</b></summary>

PowerShell does not expand `*.md`; pass the note paths explicitly. Set `$provenoteKit` to the folder
Claude printed, then:

```powershell
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/lit/lei2023financial.md
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/lit/kireyev2026pricebench.md
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/negative/lei2023financial.md
```

Use `& py -3` instead of `& python` if `python` is not available.

</details>

## 8. A first bounded task, with saved output

Still in `examples/basic` (your own downloaded copy), ask:

```text
Using Provenote, verify the quotes in the notes in 01_notes/lit/ with the installed
verify-quotes helper. Save the full output, the date, and the helper path you used to
00_admin/first-check.md. Do not change any other file. Then tell me, in two sentences, what
this result does and does not show.
```

**DONE:** the file `00_admin/first-check.md` exists and contains the 14 PASS lines. Claude's two
sentences should say the quotes were matched on the stated pages of the text copies, and that this
does not show the claims are supported or true.
**STUCK:** the file is missing or empty. Copy what Claude said and use section 9.

From here you can start your own project: ask Claude to start a research project, search the
literature, or verify notes. See the [workflow](workflow.md) for the stages. Search needs
internet access; PDF conversion and paper builds have extra requirements listed in
[INSTALL.md](../INSTALL.md). Install those only when you reach that stage.

## 9. When you are stuck

Do not reinstall repeatedly and do not change settings to "fix" a message. Copy the stuck-report
below into a message to Claude (or into a new GitHub issue), fill the blanks, and keep the
**exact** error text, not a summary:

```text
I am following docs/getting-started.md from Provenote (version: <from /plugin, or the CHANGELOG top entry>).
Step: <section number and step>
Exact error text (copy and paste, unedited): <paste here>
My system: <macOS or Windows, and the version>
Versions: claude --version = <...>; git --version = <...>; Python version = <...>
What I expected: <the DONE line from the guide>
Please tell me the smallest next thing to check. Do not install or change anything yet.
```

Report problems, and what worked, under **Issues** on the
[Provenote GitHub page](https://github.com/nik110403/provenote). This guide is a preview; reports from real Mac
and Windows machines are what move it out of "untested".

## C. Codex route

Route B only. Everything here was written from this repository's own documents and OpenAI's
official Codex pages; nothing in it has been run on a real Mac or Windows PC.

### C1. Before you start

- **An account that can use Codex, and its cost.** Plans and prices change, so this guide quotes
  none. Read the official page first: <https://developers.openai.com/codex/cli>
- **A project folder** that you intend Codex to work in. For the checks below use the
  `examples/basic` folder from the Provenote download (step C3).
- **Python 3.9 or newer** for the helper programs. In a command window, run
  `python3 --version` (macOS) or `py -3 --version` (Windows; if that is not recognised, try
  `python --version`). It should print Python 3.9 or newer. If not, install it from
  [Windows](https://www.python.org/downloads/windows/) or
  [macOS](https://www.python.org/downloads/macos/), then close and reopen the command window.

### C2. Install Codex

Codex runs in a command window ("terminal"). The official page is the authority:
<https://developers.openai.com/codex/cli>. If the line below differs from that page, follow the
official page.

<details>
<summary><b>macOS</b></summary>

1. Open **Terminal**: press Command + Space, type `Terminal`, press Return.
2. Paste this line and press Return. Wait until a new typing line appears.

From the official Codex CLI page (macOS/Linux, standalone installer): <https://developers.openai.com/codex/cli>

```sh
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

3. Close the Terminal window completely, open a new one, and check. The official page does not
   show this check; the `--version` flag comes from the Codex CLI source
   (<https://github.com/openai/codex>) and prints a line like `codex-cli 0.159.2`.

```sh
codex --version
```

**DONE:** a version number is printed.
**STUCK:** "command not found" or an error. Do not run the installer repeatedly. Copy the exact
text and use section 9.

</details>

<details>
<summary><b>Windows</b></summary>

I could not confirm a Windows install command on the official page from a plain download (the page
shows it only in a browser tab), so this guide does not repeat one. Open
<https://developers.openai.com/codex/cli>, choose the **Windows** tab, and run the command shown
there in PowerShell. Then close every PowerShell window, open a new one, and check. The official
page does not show this check; the `--version` flag comes from the Codex CLI source
(<https://github.com/openai/codex>) and prints a line like `codex-cli 0.159.2`.

```powershell
codex --version
```

**DONE:** a version number is printed.
**STUCK:** "not recognized" or an error. Copy the exact text and use section 9.

</details>

**Sign in once.** Open your project folder in the command window, type `codex`, press Return/Enter,
and choose **Sign in with ChatGPT** (or another sign-in method offered), as the official page
describes. Then close Codex.

**DONE:** Codex showed a prompt where you can type a message.
**STUCK:** a sign-in loop or a plan error. Copy the exact text and use section 9.

### C3. Get Provenote

On the [Provenote GitHub page](https://github.com/nik110403/provenote), choose
**Code → Download ZIP** and extract it. You do not need Git for this route. The extracted folder
is called `provenote-main`; in the steps below, "the extracted folder" means that folder, so
`docs/codex/SKILL.md` is `provenote-main/docs/codex/SKILL.md`. "Download ZIP" gives you the
latest version of the branch, which may be newer than the commit this guide was tested with
(see the top of the guide).

### C4. Install the Codex adapter by file-manager copy

This follows [INSTALL.md](../INSTALL.md#codex-adapter). It installs one self-contained Codex skill
into one project. It does not alter `AGENTS.md`, global configuration, or any Claude plugin.

For this guide, use `provenote-main/examples/basic` as your project. This is a demo only: it
sits inside the download, which has its own `AGENTS.md` at the top and is not a Git repository,
so Codex may treat it slightly differently from a real project. For real work, repeat this step
in your own project folder. In `examples/basic`, using your
file manager (enable hidden files first if `.agents` is not visible), create `.agents`, then
`skills` inside it, then the final `provenote` folder once, so the result is:

```text
<project>/.agents/skills/provenote/
  SKILL.md
  bin/
  templates/
  agents/
  workflows/
```

- Copy `provenote-main/docs/codex/SKILL.md` into that final folder and name it `SKILL.md`.
- Copy `bin/`, `templates/`, and `agents/` from `provenote-main/plugins/provenote/`
  alongside it.
- Copy the **whole** `provenote-main/plugins/provenote/skills/` folder there and rename that
  copied folder `workflows/`. Rename only the **copy** inside `.agents/skills/provenote/`;
  the original `skills/` folder in `plugins/provenote/` must keep its name.
- Do not copy a folder named `provenote` into the final `provenote` folder: that creates
  redundant nesting.

Before copying, stop if `<project>/.agents/skills/provenote/` already exists. Back it up and
compare it; do not overwrite anything you have not inspected.

**DONE:** the folder looks exactly like the picture above.
**STUCK:** a folder is missing or nested twice. Copy the exact folder listing and use section 9.

### C5. Check 1: discovery

Restart Codex: close it, open a new command window, and `cd` into your project (type `cd `, then
drag the `examples/basic` folder into the window and press Return/Enter). Run `codex`, then ask:

```text
$provenote show me the available Provenote workflows; do not run helpers yet.
```

**DONE:** Codex lists Provenote workflows. This proves **discovery only**. It does not prove the
helper programs run. That is Check 2.
**STUCK:** nothing is listed. Restart Codex once more; still nothing: use section 9. Live Codex
discovery has not been tested by the Provenote authors
([adapters.md](adapters.md#optional-native-skill-discovery)), so this check may fail on your
Codex version even if the files are right.

### C6. Check 2: the installed adapter helper

This runs the helper from the **installed** adapter folder, `$provenoteKit/bin`, on the bundled
example, so you see real PASS and FAIL lines. It follows [codex/SKILL.md](codex/SKILL.md). In a
normal command window, `cd` into your project (type `cd `, then drag the `examples/basic` folder
into the window and press Return/Enter). The first line below sets `provenoteKit` to the installed
adapter folder inside the folder you are in; type it exactly as shown.

<details>
<summary><b>macOS</b></summary>

```sh
provenoteKit="$PWD/.agents/skills/provenote"
python3 "$provenoteKit/bin/verify-quotes" --strict 01_notes/lit/*.md
python3 "$provenoteKit/bin/verify-quotes" --strict 01_notes/negative/*.md
```

</details>

<details>
<summary><b>Windows</b></summary>

PowerShell does not expand `*.md`; pass the note paths explicitly (as in section 7).

```powershell
$provenoteKit = "$PWD\.agents\skills\provenote"
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/lit/lei2023financial.md
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/lit/kireyev2026pricebench.md
& python "$provenoteKit\bin\verify-quotes" --strict 01_notes/negative/lei2023financial.md
```

Use `& py -3` instead of `& python` if `python` is not available.

</details>

**What you should see (observed on Linux through a local copy of the adapter; a live Codex
session was not run):** the first run prints 14 lines starting `PASS`
and exits 0; the second prints one line, `FAIL lei2023financial.md: quote 1 (p. 1): text not found
in source`, and exits 1. **That failure is expected**: the note contains an invented quote on
purpose.

**DONE:** 14 PASS, then the one expected FAIL.
**STUCK:** a different count, no FAIL, or a Python error. Do not trust the result. Copy the exact
output and use section 9.

### C7. What is NOT the same as Claude Code

- **Copied roles are instructions, not imported permissions.** The files in `agents/` and
  `workflows/` tell Codex how to behave. They do not carry over Claude's tool restrictions, and
  they do not make Codex read-only where it otherwise could write.
- **Serial review is non-independent.** If Codex has no separate reviewer available, it runs the
  reading and review steps one after another in the same session. Treat that result as
  non-independent: the same model checked its own work.
- **Live Codex discovery is untested.** The adapter is tested as a local copy; whether your Codex
  finds the skill by itself is not (see [adapters.md](adapters.md#optional-native-skill-discovery)).

The same limit as Route A applies: a passing quote check means the words are on that page of the
text copy, not that your claim is true (section 1).

## 10. Later

- Codex route: [section C](#c-codex-route) above; background in the
  [Codex adapter section of INSTALL.md](../INSTALL.md#codex-adapter).
- The broader ai-architecture workflow: not linked yet.

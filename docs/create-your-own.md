# Create your own skill or role

These starters are small enough to copy without Git, Python, or a terminal. They
perform a useful evidence checklist without calling a helper. They are not a claim
that a host grants permissions, dispatches agents, or provides independent review.

## Copy the starter

Copy the complete [`templates/evidence-checklist`](../templates/evidence-checklist/)
folder to one of these locations, preserving its `SKILL.md` file:

| Host | Skill location |
|---|---|
| Codex | `<project>/.agents/skills/evidence-checklist/SKILL.md` |
| Claude Code | `<project>/.claude/skills/evidence-checklist/SKILL.md` |

For Claude Code, copy
[`templates/evidence-checker-agent.md`](../templates/evidence-checker-agent.md) to
`<project>/.claude/agents/evidence-checker.md`. Codex does not automatically
discover Claude agent files. For a host without a matching agent format, copy the
[`templates/portable-evidence-checker.md`](../templates/portable-evidence-checker.md)
text into a sequential prompt and run its steps yourself.

Do not overwrite an existing skill, role, or project instruction. Copying a starter
is separate from GitHub's **Use this template** repository setting; this repository
does not claim that setting is enabled.

## Adapt it deliberately

1. Change the YAML `name` and `description` so its trigger names the task a user
   will ask for. Keep the description factual.
2. Define the input precisely: for example, a draft and its list of sources.
3. Define the output and evidence contract: the starter returns a checklist whose
   rows identify the supplied source or say `not supplied`.
4. Keep the boundary explicit. The starter neither retrieves sources nor decides
   whether a claim is true.

Restart the host and use the same self-contained input in each smoke test:

```text
Claims:
1. The study enrolled 20 participants.
2. Every participant completed follow-up.

Source excerpt: "Twenty participants enrolled in the study."
```

In Codex, ask `$evidence-checklist` to check those claims against that excerpt. In
Claude Code, ask it to use the `evidence-checklist` skill for the same input. The
expected rows are: claim 1 — source excerpt, `Twenty participants enrolled in the
study.`, `supported`; claim 2 — source excerpt, `not found`, `missing evidence`.

For the portable role, paste the same input below the
[`portable-evidence-checker`](../templates/portable-evidence-checker.md) contract
and ask it to return its required table. Expect the same two statuses. These smokes
confirm that an instruction can be found and followed. They do not establish
independent review or validate research evidence.

For fuller patterns, reuse the real [skills](../plugins/provenote/skills/),
[agents](../plugins/provenote/agents/), and [adapter guidance](adapters.md) in
this repository. They carry workflow-specific dependencies and limits. You may
copy and modify the starters under the [MIT License](../LICENSE); retain the
required notice in substantial copies.

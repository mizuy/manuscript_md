# Installing manuscript_md skills (public)

These are **Agent Skills** with bundled scripts. They live in one GitHub
repo and work for any Markdown → Word paper project. The skill format is
the [Agent Skills](https://agentskills.io) `SKILL.md` standard.

**Repo:** https://github.com/mizuy/manuscript_md

## Skills

| Skill | Role |
|-------|------|
| [`skills/manuscript_md`](../skills/manuscript_md/SKILL.md) | Prose conventions, pandoc → docx, submission TIFF |
| [`skills/manuscript-reference`](../skills/manuscript-reference/SKILL.md) | Paperpile → `references.bib`, `reference/` notes, checkme |
| [`skills/word-docx-compare`](../skills/word-docx-compare/SKILL.md) | macOS Word Compare / `versions/` tagging |
| [`skills/strobe-checklist`](../skills/strobe-checklist/SKILL.md) | Fill / audit STROBE checklist for observational papers |

## Option A — Clone + workspace (recommended)

```bash
git clone https://github.com/mizuy/manuscript_md.git
cd manuscript_md
uv sync
```

Add the clone to your Cursor/VS Code workspace next to the research repo.
Point research Taskfiles at the clone with `PAPER_PROJECT`:

```yaml
includes:
  manuscript_md:
    taskfile: ${PAPER_PROJECT:-../manuscript_md}/Taskfile.yml
    dir: ${PAPER_PROJECT:-../manuscript_md}
    flatten: true
    vars:
      PAPER_DIR: /absolute/path/to/your/paper
      PAPER_CSL: vancouver.csl
      FILES: manuscript supplementary
      PAPERPILE_BIB: /absolute/path/to/paperpile.bib
```

See [`WORKFLOW.md#consumer-includes`](WORKFLOW.md#consumer-includes).

## Option B — Personal skills (discovery)

Canonical personal path is `~/.agents/skills/` (Cursor and Codex). Claude Code
uses `~/.claude/skills/`.

```bash
REPO=/path/to/manuscript_md
mkdir -p ~/.agents/skills ~/.claude/skills
for s in manuscript_md manuscript-reference word-docx-compare strobe-checklist; do
  ln -sfn "$REPO/skills/$s" ~/.agents/skills/$s
  ln -sfn "$REPO/skills/$s" ~/.claude/skills/$s
done
```

Prefer **symlinks to the clone** so scripts/filters stay in sync. Thin pointer
`SKILL.md` files alone are not enough to run builds.

This repo also has `.agents/skills/` and `.claude/skills/` as discovery
symlinks to `skills/`, so opening the clone as a workspace folder is enough
for Cursor / Codex / Claude Code.

## Option C — Project skills

Copy or submodule `skills/*` into your research repo’s `.agents/skills/`
(and keep `PAPER_PROJECT` pointing at a checkout that has the Taskfile + `uv`
package for builds). Cursor and Codex read `.agents/skills/`. For Claude Code,
add `.claude/skills/<name>` → `../../.agents/skills/<name>`.

## Requirements

- Python 3.11+ (`uv`)
- pandoc
- Optional: macOS + Microsoft Word (word-docx-compare only)
- `PAPERPILE_BIB` — path to your Paperpile (or equivalent) `.bib` export

## First paper

[`NEW_PAPER.md`](NEW_PAPER.md)

## Lab note

Paths like `/Users/mizuy/lab/…` in older docs are **examples only**. Public
defaults use env vars (`PAPER_PROJECT`, `PAPERPILE_BIB`, `PAPER_DIR`).

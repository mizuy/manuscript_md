# Installing manuscript_md skills (public)

These are **Cursor Agent Skills** with bundled scripts. They live in one GitHub
repo and work for any Markdown → Word paper project.

**Repo:** https://github.com/mizuy/manuscript_md

## Skills

| Skill | Role |
|-------|------|
| [`skills/manuscript_md`](../skills/manuscript_md/SKILL.md) | Prose conventions, pandoc → docx, submission TIFF |
| [`skills/manuscript-reference`](../skills/manuscript-reference/SKILL.md) | Paperpile → `references.bib`, `reference/` notes, checkme |
| [`skills/word-docx-compare`](../skills/word-docx-compare/SKILL.md) | macOS Word Compare / `versions/` tagging |

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

## Option B — Personal Cursor skills (discovery)

Symlink or copy each skill folder into `~/.cursor/skills/`:

```bash
REPO=/path/to/manuscript_md
ln -sfn "$REPO/skills/manuscript_md" ~/.cursor/skills/manuscript_md
ln -sfn "$REPO/skills/manuscript-reference" ~/.cursor/skills/manuscript-reference
ln -sfn "$REPO/skills/word-docx-compare" ~/.cursor/skills/word-docx-compare
```

Prefer **symlinks to the clone** so scripts/filters stay in sync. Thin pointer
`SKILL.md` files alone are not enough to run builds.

## Option C — Project skills

Copy or submodule `skills/*` into your research repo’s `.cursor/skills/`
(and keep `PAPER_PROJECT` pointing at a checkout that has the Taskfile + `uv`
package for builds).

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

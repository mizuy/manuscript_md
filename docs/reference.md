# manuscript_md Reference

**manuscript_md** (`manuscript-md` CLI) builds a Markdown paper directory into Word docx.

## Paths

| Item | Path |
|------|------|
| Project root | `/Users/mizuy/lab/manuscript_md` |
| Skill (scripts/filters/csl) | `skills/manuscript_md/` |
| Companion skills | `skills/manuscript-reference/`, `skills/word-docx-compare/` |
| Docs | `docs/` |

Compat symlinks: repo-root `filters/` → skill `filters/`, `csl/` → skill `csl/`.

## Common Tasks

```bash
cd /Users/mizuy/lab/manuscript_md
task paper:docx PAPER_DIR=/path/to/paper
task paper:words PAPER_DIR=/path/to/paper
task paper:build-bib PAPER_DIR=/path/to/paper
task paper:submission PAPER_DIR=/path/to/paper
# optional override only:
task paper:sync-assets PAPER_DIR=/path/to/paper
```

## Paper Directory (minimal)

```text
paper/
  manuscript.md
  supplementary.md
  references.bib      # generated
  fig/
  table/
  reference/          # optional
```

Do not require `script/filters/` or `reference.docx` — pandoc uses skill
filters / `templates/reference.docx` by absolute path (paper-local file wins
if present).

## Bibliography / Imports / CSL

Same as before: `[@key]`, `@import`, `PAPER_CSL=<bundled-name|path>`.

## Manual Pandoc Flow

Prefer `task paper:docx`. Internally:

1. Build `references.bib`.
2. Expand `@import` into `.build/<stem>.md`.
3. Run pandoc with **skill** `filters/*.lua`, `reference.docx`, citeproc, CSL.
4. Patch docx table layout.

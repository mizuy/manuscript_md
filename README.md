# manuscript_md

Public **Cursor Agent Skills** + tooling for Markdown scientific papers → Word.

**GitHub:** https://github.com/mizuy/manuscript_md  
**Install:** [`docs/INSTALL.md`](docs/INSTALL.md)  
**CLI:** `lab-paper` (`uv sync` in this repo)

| Skill | Path |
|-------|------|
| manuscript_md | [`skills/manuscript_md/SKILL.md`](skills/manuscript_md/SKILL.md) |
| manuscript-reference | [`skills/manuscript-reference/SKILL.md`](skills/manuscript-reference/SKILL.md) |
| word-docx-compare | [`skills/word-docx-compare/SKILL.md`](skills/word-docx-compare/SKILL.md) |

```bash
git clone https://github.com/mizuy/manuscript_md.git
cd manuscript_md && uv sync
export PAPERPILE_BIB=/path/to/paperpile.bib
task paper:docx PAPER_DIR=/path/to/paper
```

Skills ship scripts/filters/csl under `skills/`. Papers stay minimal (no vendored
build assets). Research repos flatten-include this `Taskfile.yml` (see
[`docs/INSTALL.md`](docs/INSTALL.md)).

## Workspace

```json
{
  "folders": [
    { "path": "/path/to/research-repo" },
    { "path": "/path/to/manuscript_md" }
  ]
}
```

```bash
cd /path/to/manuscript_md
task paper:docx PAPER_DIR=/path/to/research-repo/paper PAPERPILE_BIB=/path/to/paperpile.bib
task paper:words PAPER_DIR=/path/to/research-repo/paper
```

For another paper:

```bash
task paper:docx \
  PAPER_DIR=/path/to/research-repo/paper \
  PAPER_CSL=vancouver.csl \
  FILES="manuscript supplementary"
```

## Tasks

- `task paper:docx PAPER_DIR=/path/to/paper`: build Word docx (skill filters, no copy).
- `task paper:words PAPER_DIR=/path/to/paper`: count abstract and main-text words.
- `task paper:author-list -- affiliations.txt --order authors.txt -o author_list.md`: title-page author/affiliation list.
- `task paper:build-bib PAPER_DIR=/path/to/paper`: generate `references.bib`.
- `task paper:checkme PAPER_DIR=/path/to/paper`: citation dashboard (`checkme_paper.md`).
- `task paper:submission PAPER_DIR=/path/to/paper`: upload package + TIFF.
- `task paper:sync-assets PAPER_DIR=/path/to/paper`: **optional** copy of filters for paper-local overrides.

New paper recipe: [`docs/NEW_PAPER.md`](docs/NEW_PAPER.md).  
Consumer includes rules: [`docs/WORKFLOW.md`](docs/WORKFLOW.md#consumer-includes).

## Paper Directory Expectations

Minimal paper directory:

```text
paper/
  manuscript.md
  supplementary.md
  # reference.docx optional override — default: skill templates/reference.docx
  fig/  table/
  references.bib          # generated
```

Lua filters, CSL, and `reference.docx` ship inside `skills/manuscript_md/`.
Do not require paper-local copies unless overriding.

Research repositories remain responsible for analysis outputs and project-specific artifact syncing, such as copying tables and figures into `paper/table` or `paper/fig`.

## Supplementary Material

See [`docs/SUPPLEMENTARY_POLICY.md`](docs/SUPPLEMENTARY_POLICY.md) and [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md).

- `supplementary.md` is submission-facing and self-contained.
- Internal review notes (e.g. `_internal_review_notes.md`) are never cited from manuscript/supplementary.
- No “Additional Supplementary …” in submission files.
- Every Supplementary Table/Figure in `supplementary.md` is cited at least once in `manuscript.md`.

## CLI

The Taskfile calls the `lab-paper` CLI. Direct usage is also available:

```bash
uv run lab-paper build-bib --paper-dir /path/to/paper --scan-markdown
uv run lab-paper expand-imports /path/to/paper/manuscript.md -o /path/to/paper/.build/manuscript.md
uv run lab-paper patch-docx /path/to/paper/manuscript.docx
uv run lab-paper word-count --paper-dir /path/to/paper
uv run lab-paper author-list affiliations.txt --order authors.txt -o author_list.md
uv run lab-paper sync-assets --paper-dir /path/to/paper
```

## Documentation

| Doc | Content |
|-----|---------|
| [`docs/INSTALL.md`](docs/INSTALL.md) | Public install (clone / symlink / project skills) |
| [`docs/NEW_PAPER.md`](docs/NEW_PAPER.md) | Bootstrap a new paper |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | End-to-end loop + Task includes rules |
| [`docs/PROSE_CONVENTIONS.md`](docs/PROSE_CONVENTIONS.md) | Body prose + figure caption rules |
| [`docs/PAPER_LAYOUT.md`](docs/PAPER_LAYOUT.md) | Directory layout |
| [`docs/reference.md`](docs/reference.md) | pandoc, Taskfile, Lua |
| [`docs/REFERENCE_INGEST.md`](docs/REFERENCE_INGEST.md) | Literature ingest (Paperpile) |
| [`docs/SUPPLEMENTARY_POLICY.md`](docs/SUPPLEMENTARY_POLICY.md) | Supplement rules |
| [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md) | Final checklist |
| [`docs/TABLE_WORD.md`](docs/TABLE_WORD.md) | Word table layout |
| [`skills/manuscript_md/SKILL.md`](skills/manuscript_md/SKILL.md) | Cursor skill + scripts/filters/csl |
| [`skills/manuscript-reference/SKILL.md`](skills/manuscript-reference/SKILL.md) | Cursor skill + bib / checkme |
| [`skills/word-docx-compare/SKILL.md`](skills/word-docx-compare/SKILL.md) | Cursor skill + Compare scripts |

# Paper Directory Layout

Recommended **minimal** layout for a paper built with **manuscript_md** skills.
Build tooling (Lua filters, CSL, Python scripts) lives in the skill packages —
do **not** vendor them into the paper unless you need a local override.

```text
paper/
  manuscript.md
  supplementary.md
  manuscript_instruction.md  # project prose / claims
  comment.md                 # scientific claims (not submitted)
  checkme_paper.md           # optional citation dashboard
  references.bib             # generated
  manual_entries.bib         # optional
  # reference.docx           # optional override; default = skill templates/
  fig/
  table/
  reference/                 # optional literature notes
    md/ pdf/ reference_keys.txt
  versions/                  # Word Compare cycle
    manifest.yml
  submission/                # generated upload package
  _internal_review_notes.md  # never cited from submission Markdown
```

Optional override only:

```text
paper/script/filters/*.lua   # if present, you opted into sync-assets
```

Default `task paper:docx` uses `skills/manuscript_md/filters/` directly.

## Tables / figures

See [`TABLE_WORD.md`](TABLE_WORD.md), [`PROSE_CONVENTIONS.md`](PROSE_CONVENTIONS.md),
[`WORKFLOW.md`](WORKFLOW.md).

## Submission package (TIFF)

```bash
cd /Users/mizuy/lab/manuscript_md
task paper:submission PAPER_DIR=/path/to/paper FILES="manuscript supplementary" DPI=600
```

## Filters (skill)

Canonical Lua filters: `skills/manuscript_md/filters/`.  
Optional copy into a paper: `task paper:sync-assets PAPER_DIR=...` (override workflow).

## References

See [`REFERENCE_INGEST.md`](REFERENCE_INGEST.md) and skill **manuscript-reference**.

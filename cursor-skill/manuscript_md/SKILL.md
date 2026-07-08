---
name: manuscript_md
description: >-
  Use when writing Markdown papers or building Word docx outputs with the lab
  manuscript_md workflow. Executable tooling lives in /Users/mizuy/lab/paper;
  this skill explains when and how to use that project.
---

# manuscript_md

The reusable paper build system is the standalone project **manuscript_md** at:

`/Users/mizuy/lab/paper`

> **Note:** The directory is still named `paper` on disk. The project display name and Cursor skill id are **manuscript_md**. The GitHub repo may be renamed later.

Do not run scripts from this skill directory. Add `lab/paper` to the same VS Code/Cursor workspace as the research repository, then run paper tasks from `/Users/mizuy/lab/paper`.

## Use This When

- Building a Markdown manuscript to Word docx with pandoc and citeproc.
- Generating `references.bib` from manuscript `[@key]` citations.
- Expanding `@import "table/foo_csv.md"` fragments before pandoc.
- Syncing reusable Lua filters into a paper directory.
- Counting manuscript words.

## Standard Commands

```bash
cd /Users/mizuy/lab/paper
task paper:docx PAPER_DIR=/Users/mizuy/lab/duoer_recur/paper
task paper:words PAPER_DIR=/Users/mizuy/lab/duoer_recur/paper
task paper:sync-assets PAPER_DIR=/Users/mizuy/lab/duoer_recur/paper
```

For another paper:

```bash
cd /Users/mizuy/lab/paper
task paper:docx \
  PAPER_DIR=/Users/mizuy/lab/pccrc/docs/paper_lag0 \
  PAPER_CSL=gie.csl \
  FILES="manuscript supplementary"
```

## Workspace Pattern

Use a multi-root workspace:

```json
{
  "folders": [
    { "path": "/Users/mizuy/lab/duoer_recur" },
    { "path": "/Users/mizuy/lab/paper" }
  ]
}
```

The research repository remains responsible for analysis, figures, tables, and paper-specific artifact syncing. **manuscript_md** (`lab/paper`) owns Markdown-to-Word tooling, CSL resolution, `references.bib` generation, Lua filters, and docx table patching.

For Word Compare / version diffs when collaborators edit docx, see [word-docx-compare](~/.cursor/skills/word-docx-compare/SKILL.md).

## Documentation

| Doc | Content |
|-----|---------|
| [`docs/PAPER_LAYOUT.md`](../../docs/PAPER_LAYOUT.md) | `fig/`, `script/filters/`, `reference/` |
| [`docs/REFERENCE_INGEST.md`](../../docs/REFERENCE_INGEST.md) | Literature note ingest |
| [`docs/reference.md`](../../docs/reference.md) | pandoc, Taskfile, Lua |
| [`docs/SUPPLEMENTARY_POLICY.md`](../../docs/SUPPLEMENTARY_POLICY.md) | Supplementary material rules |
| [`docs/SUBMISSION_CHECKLIST.md`](../../docs/SUBMISSION_CHECKLIST.md) | Final checklist + grep aids |
| [`docs/TABLE_WORD.md`](../../docs/TABLE_WORD.md) | Word table layout |
| [`templates/Taskfile.paper.example.yml`](../../templates/Taskfile.paper.example.yml) | Task snippet for research repos |

pccrc reference implementation: `docs/paper_lag0/` (`task paper:docx` scans `[@key]` + `script/filters/*.lua`).

---

## Supplementary material

Submission-facing supplementary content lives in **`supplementary.md` only**. Full policy: [`docs/SUPPLEMENTARY_POLICY.md`](../../docs/SUPPLEMENTARY_POLICY.md).

### Structure

```text
supplementary.md
  ## Supplementary methods      # definitions needed by tables/figures
  ## Supplementary tables
  ## Supplementary figures
```

- Put operational definitions here (e.g. adjusted QI calculation), not in a separate “additional” file referenced from captions.
- Captions may point to **Supplementary methods** within the same file.
- Do **not** add extra submission tables/figures to `supplementary.md` beyond the planned Supplementary Table/Figure numbering unless the manuscript is updated to cite them.

### Internal review notes (not for submission)

Extra sensitivity analyses, reviewer-response drafts, and extended methods that are **not** cited in the manuscript stay in a **separate internal file** (e.g. `_internal_review_notes.md`). This file is for local/peer-review use only.

- Do **not** name it `additional.md` or label content “Additional Supplementary …” if that naming could be mistaken for a second submission appendix.
- **Never** link to it from `manuscript.md` or `supplementary.md`.
- **Never** cite “Additional Supplementary Table/Figure/Material” in the manuscript.

When moving method text from internal notes into `supplementary.md`, copy the wording; do not leave “see Additional …” placeholders.

### Manuscript cross-references

Every **Supplementary Table *N*** and **Supplementary Figure *N*** that appears in `supplementary.md` must be cited **at least once** in `manuscript.md` (Methods, Results, Discussion, or Supplementary appendix).

The manuscript Supplementary appendix should list only what is in `supplementary.md` (Supplementary methods, Tables, Figures)—not internal notes.

---

## Final checklist (before docx / submission)

Full version with grep aids: [`docs/SUBMISSION_CHECKLIST.md`](../../docs/SUBMISSION_CHECKLIST.md).

```
Manuscript
- [ ] Abstract / Discussion / Conclusions aligned (no orphan claims)
- [ ] No ** bold ** or inline `code` in body text (see project manuscript_instruction.md)
- [ ] references.bib regenerated from [@key] (--scan-markdown)
- [ ] Every main-text Table/Figure cited before or at first use

Supplementary (supplementary.md)
- [ ] Self-contained: no links to internal review notes or “Additional Supplementary …”
- [ ] Supplementary methods cover definitions referenced by Supplementary Table/Figure captions
- [ ] Table/Figure count unchanged unless manuscript citations were added
- [ ] Every Supplementary Table N / Figure N cited at least once in manuscript.md

Internal (not submitted)
- [ ] Internal review notes file not referenced from manuscript or supplementary
- [ ] No “Additional Supplementary …” strings left in manuscript.md

Build
- [ ] task paper:docx (or lab/paper equivalent) succeeds
- [ ] task paper:fig-audit passes if figures are synced from analysis tasks
```

### Grep aids

Run from the paper directory (e.g. `docs/paper_lag0/`):

```bash
# Internal / additional references must be absent from submission files
rg -i 'additional supplementary|additional\.md|additional online' manuscript.md supplementary.md

# List Supplementary items defined in supplementary.md
rg '\*\*Supplementary (Table|Figure) [0-9]+' supplementary.md

# Cross-check each appears in manuscript (example for Figure 3)
rg 'Supplementary Figure 3' manuscript.md
rg 'Supplementary Table 2' manuscript.md
```

Project-specific prose rules (cohort naming, claim boundaries): see `docs/paper_<name>/manuscript_instruction.md` when present.

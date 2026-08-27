# Submission Checklist

Run this checklist before `task paper:docx` and journal submission.

- Workflow: [`WORKFLOW.md`](WORKFLOW.md)
- Prose / figures: [`PROSE_CONVENTIONS.md`](PROSE_CONVENTIONS.md)
- Supplementary policy: [`SUPPLEMENTARY_POLICY.md`](SUPPLEMENTARY_POLICY.md)

## Title page

- [ ] Author / affiliation `<sub>` marks remapped (`task paper:author-list` or `lab-paper author-list`) when merging lists from more than one source

## Manuscript

- [ ] Abstract / Discussion / Conclusions aligned (no orphan claims)
- [ ] No `**bold**` or inline `` `code` `` in body text ([`PROSE_CONVENTIONS.md`](PROSE_CONVENTIONS.md); Abstract labels + Figure/Table lead-ins excepted)
- [ ] No analysis column names, task names, or `table_*.csv` / `fig_*.png` filenames in Methods/Results
- [ ] R package names only in Software (not Methods narrative)
- [ ] `references.bib` regenerated from `[@key]` (`--scan-markdown`; skill **manuscript-reference**)
- [ ] Every main-text Table/Figure cited before or at first use
- [ ] Project `comment.md` / `manuscript_instruction.md` claim boundaries respected

## Figures / tables

- [ ] Manuscript `fig/` images have no embedded title/subtitle
- [ ] Captions use `**Figure N.**` / `**Table N.**` lead-in only
- [ ] `table/` CSV companions updated; `@import` targets exist
- [ ] `task paper:fig-audit` (or equivalent) passes when syncing from analysis tasks

## Supplementary (`supplementary.md`)

- [ ] Self-contained: no links to internal review notes or “Additional Supplementary …”
- [ ] Supplementary methods cover definitions referenced by Supplementary Table/Figure captions
- [ ] Table/Figure count unchanged unless manuscript citations were added
- [ ] Every Supplementary Table *N* / Figure *N* cited at least once in `manuscript.md`

## Internal (not submitted)

- [ ] Internal review notes file not referenced from manuscript or supplementary
- [ ] No “Additional Supplementary …” strings left in `manuscript.md`

## Reporting guidelines (when required)

- [ ] Observational studies: `STROBE_checklist.md` filled (skill **strobe-checklist**); wired via `@import` or journal upload as required
- [ ] Cover letter mentions STROBE when the journal asks

## Build

- [ ] `task paper:docx` (or `lab-paper` equivalent) succeeds for review drafts
- [ ] `task paper:submission` (or equivalent) for final upload: figure-free docx + TIFF @ 600 dpi
- [ ] Word cycle (`paper:tag` / `paper:diff`) uses paths under the paper directory (not `/tmp`)

## Grep aids

Run from the paper directory (e.g. `docs/paper_lag0/`):

```bash
rg -i 'additional supplementary|additional\.md|additional online' manuscript.md supplementary.md
rg '\*\*' manuscript.md
rg '`' manuscript.md
rg '\*\*Supplementary (Table|Figure) [0-9]+' supplementary.md
rg 'Supplementary (Table|Figure) [0-9]+' manuscript.md
```

Project-specific prose rules (cohort naming, claim boundaries): see
`manuscript_instruction.md` / `comment.md` in the paper directory.

# Submission Checklist

Run this checklist before `task paper:docx` and journal submission.

Supplementary policy: [`SUPPLEMENTARY_POLICY.md`](SUPPLEMENTARY_POLICY.md).

## Manuscript

- [ ] Abstract / Discussion / Conclusions aligned (no orphan claims)
- [ ] No `**bold**` or inline `` `code` `` in body text (see project `manuscript_instruction.md` when present)
- [ ] `references.bib` regenerated from `[@key]` (`--scan-markdown`)
- [ ] Every main-text Table/Figure cited before or at first use

## Supplementary (`supplementary.md`)

- [ ] Self-contained: no links to internal review notes or “Additional Supplementary …”
- [ ] Supplementary methods cover definitions referenced by Supplementary Table/Figure captions
- [ ] Table/Figure count unchanged unless manuscript citations were added
- [ ] Every Supplementary Table *N* / Figure *N* cited at least once in `manuscript.md`

## Internal (not submitted)

- [ ] Internal review notes file not referenced from manuscript or supplementary
- [ ] No “Additional Supplementary …” strings left in `manuscript.md`

## Build

- [ ] `task paper:docx` (or `lab-paper` equivalent) succeeds
- [ ] `task paper:fig-audit` passes if figures are synced from analysis tasks

## Grep aids

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

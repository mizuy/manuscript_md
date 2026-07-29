# Supplementary Material Policy

Submission-facing supplementary content lives in **`supplementary.md` only**. It must be **self-contained**: readers and reviewers should not need a second online document to interpret any Supplementary Table, Figure, or method note.

## Structure

```text
supplementary.md
  ## Supplementary Methods      # definitions needed by tables/figures
  ## Supplementary Tables
  ## Supplementary Figures
```

- Put operational definitions here (e.g. adjusted QI calculation), not in a separate “additional” file referenced from captions.
- Captions may point to **Supplementary methods** within the same file.
- Do **not** add extra submission tables/figures to `supplementary.md` beyond the planned Supplementary Table/Figure numbering unless the manuscript is updated to cite them.

## Internal review notes (not for submission)

Extra sensitivity analyses, reviewer-response drafts, and extended methods that are **not** cited in the manuscript stay in a **separate internal file** (e.g. `_internal_review_notes.md`). This file is for local/peer-review use only.

- Do **not** name it `additional.md` or label content “Additional Supplementary …” if that naming could be mistaken for a second submission appendix.
- **Never** link to it from `manuscript.md` or `supplementary.md`.
- **Never** cite “Additional Supplementary Table/Figure/Material” in the manuscript.

When moving method text from internal notes into `supplementary.md`, copy the wording; do not leave “see Additional …” placeholders.

## Manuscript cross-references

Every **Supplementary Table *N*** and **Supplementary Figure *N*** that appears in `supplementary.md` must be cited **at least once** in `manuscript.md` (Methods, Results, Discussion, or Supplementary appendix).

The manuscript Supplementary appendix should list only what is in `supplementary.md` (Supplementary methods, Tables, Figures)—not internal notes.

## Related

- Final checklist: [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md)
- Cursor skill: [`skills/manuscript_md/SKILL.md`](../skills/manuscript_md/SKILL.md)
- Template: [`templates/supplementary_skeleton.md`](../templates/supplementary_skeleton.md)

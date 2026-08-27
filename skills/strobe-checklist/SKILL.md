---
name: strobe-checklist
description: >-
  Create or fill a STROBE reporting checklist (Markdown table) for observational
  studies from manuscript.md / supplementary.md. Use when the user asks for
  STROBE, EQUATOR observational checklist, AJG/journal STROBE appendix, Partial
  STROBE items, or STROBE_checklist.md. Companions: manuscript_md,
  manuscript-reference.
---

# strobe-checklist

## When / not

| Use when | Do not use when |
|----------|-----------------|
| Fill / audit `STROBE_checklist.md` | CONSORT / PRISMA / other EQUATOR tools (separate) |
| Journal asks for STROBE (e.g. AJG) | Methods rewrite without a checklist ask |
| Mark Yes / Partial / No / N/A with locations | Inventing locations not in the manuscript |

**Companions:** [manuscript_md](../manuscript_md/SKILL.md) · [manuscript-reference](../manuscript-reference/SKILL.md)

**Install:** [`docs/INSTALL.md`](../../docs/INSTALL.md) · **GitHub:** https://github.com/mizuy/manuscript_md

**Official:** [STROBE](https://www.strobe-statement.org/) / [EQUATOR](https://www.equator-network.org/reporting-guidelines/strobe/)

---

```text
skills/strobe-checklist/
  SKILL.md
  templates/
    STROBE_checklist_cohort.md   # blank cohort table (house layout)
```

## Workflow

1. **Design** — cohort (default), case-control, or cross-sectional. Start from
   [`templates/STROBE_checklist_cohort.md`](templates/STROBE_checklist_cohort.md)
   for cohort. For other designs, copy the cohort file and adapt item wording
   from the official STROBE PDF (same item numbers; eligibility / matching /
   follow-up rows differ).
2. **Write** `PAPER_DIR/STROBE_checklist.md` (do not leave the blank template
   path as the paper file).
3. **Read** `manuscript.md` (and `supplementary.md` / tables / figure captions
   as needed). Prefer expanded build output only if imports matter for locations.
4. **Fill every row**:
   - **Reported?** — `Yes` | `Partial` | `No` | `N/A`
   - **Location / comment** — concrete pointers: section heading, Table/Figure
     N, Supplementary Table/Figure N. One short clause if N/A or Partial.
5. **Gap policy** — if an item is `Partial` / `No` and a one-line Methods /
   title-page / funder-role fix is safe, **patch the manuscript** then set
   `Yes`. Do not claim Yes without text that supports it.
6. **Wire submission** (when the journal wants the checklist with the paper):
   - End of `manuscript.md`: `@import "STROBE_checklist.md"` (after main body /
     references as the journal expects), **or** upload as a separate file.
   - Mention STROBE in `cover_letter.md` if the journal asks.
7. **Rebuild** with **manuscript_md** (`task paper:docx`) after wiring import.

## House layout

```markdown
# STROBE Statement—Checklist of items that should be included in reports of **cohort studies**

Manuscript: <exact manuscript title>

Source: [STROBE checklist (cohort)](https://www.strobe-statement.org/) / EQUATOR Network. <optional journal note>

| Item no. | Recommendation | Reported? | Location / comment |
| --- | --- | --- | --- |
| … | … | Yes | Methods — …; Table 1 |
```

- Keep official **Item no.** and **Recommendation** text (minor punctuation OK).
- Do not drop rows. Use `N/A` + reason for matched-only / follow-up-only items.
- Footnote under the table is optional (study-specific exposure definition).

## Location style (examples)

| Good | Bad |
|------|-----|
| `Methods — Statistical analysis; Supplementary Table 2` | `Methods` alone for a multi-part item |
| `Figure 1; Results` | `See paper` |
| `N/A — not a matched cohort` | Empty cell |
| `Partial — abstract only; design term absent from title` | `Yes` when title omits design and item asks title **or** abstract |

## Common Partial traps

| Item | Often missing |
|------|----------------|
| 1a | Design term only in Methods, not title/abstract |
| 3 | Aims without an explicit a priori hypothesis |
| 10 | Flow/eligibility without stating no a priori sample-size calculation (or the calculation) |
| 12c | Missing-data rule unspoken |
| 16a | Adjusted HRs only; unadjusted not shown |
| 22 | Funder named without **role of the funder** |

## Do not

- Fabricate section/table numbers.
- Mark `Yes` for content only in internal notes / protocol, not the submission files.
- Vendor this skill into the paper directory (keep one `STROBE_checklist.md` there).

# Word Table Layout

Markdown pipe tables are converted to Word tables by pandoc and then patched for paper-friendly layout.

## Pipeline

| Stage | File | Role |
|------|------|------|
| Markdown generation | project-specific analysis code | writes CSV and Markdown table fragments |
| Import expansion | `scripts/expand_imports.py` | expands `@import` and preserves nested row indentation |
| Pandoc filter | `filters/table_word.lua` | protects line breaks and applies column widths |
| Docx patch | `scripts/patch_docx_tables.py` | patches spacing, alignment, vertical centering, and final section orientation |

`task paper:docx` runs the full pipeline.

## Table Fragments

Generated table fragments should contain only the Markdown table. Titles, captions, abbreviations, and explanatory footnotes belong in the manuscript.

Recommended pattern:

```markdown
**Table 1.** Baseline characteristics

@import "table/table_1_csv.md"

Abbreviations and table notes go here.
```

## Nested Rows

For categorical variables, write the variable name as a parent row, then indent category rows with two leading spaces in the first CSV/Markdown column.

```text
Characteristic
  Category A
  Category B
```

The import expansion and Markdown rendering convert these leading spaces to em spaces so Word preserves the visual indentation.

## Column Widths

`filters/table_word.lua` (under `skills/manuscript_md/filters/`) keeps
data columns mostly even, gives the first label column slightly more width, and
widens the last column for trailing fields (notes / p-values).

Default builds use the skill filters directly. To customize one paper only, copy
with `task paper:sync-assets` and edit `PAPER_DIR/script/filters/`.

## Alignment

`scripts/patch_docx_tables.py` applies:

- first column: left aligned
- data columns: centered
- all cells: vertically centered
- compact paragraph spacing inside table cells
- 10 pt font (`TableCompact` style)

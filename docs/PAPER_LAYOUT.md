# Paper Directory Layout

This is the recommended layout for a Markdown paper directory built with `lab-paper`.

```text
paper/
  manuscript.md
  supplementary.md
  references.bib
  manual_entries.bib
  reference.docx
  vancouver.csl
  fig/
    README.md
  table/
    table_1.csv
    table_1_csv.md
  script/
    README.md
    filters/
      pagebreak.lua
      landscape.lua
      table_word.lua
      superscript.lua
  reference/
    README.md
    reference_keys.txt
    reference.bib
    md/
    pdf/
```

Only `manuscript.md`, source notes, project-specific scripts, and curated references are normally edited by hand.

Generated files include:

- `references.bib`
- `.build/*.md`
- `*_csv.md` table fragments
- `manuscript.docx`
- `supplementary.docx`

## Tables

Store numeric table outputs in `table/*.csv`.

Markdown companion files such as `table_1_csv.md` should be mechanical conversions from CSV. Table titles, captions, abbreviations, and explanatory footnotes belong in the manuscript.

## Figures

Store manuscript figures in `fig/` and reference them from Markdown:

```markdown
![](fig/figure_1.png)
```

Figure titles and explanations belong in the manuscript caption, not inside the image unless the target journal requires it.

## Filters

Paper-local Lua filters live under `script/filters/`.

Create or refresh them with:

```bash
cd /Users/mizuy/lab/paper
task paper:sync-assets PAPER_DIR=/path/to/paper
```

The paper-local copy may be edited when a manuscript needs custom table or page-layout behavior.

## References

Reference notes are optional. If used, keep one Markdown note per citation key under `reference/md/` and one PDF per key under `reference/pdf/`.

See `docs/REFERENCE_INGEST.md` for details.

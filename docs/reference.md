# lab-paper Reference

`lab-paper` builds a Markdown paper directory into Word docx output.

## Paths

| Item | Path |
|------|------|
| Project root | `/Users/mizuy/lab/paper` |
| Bundled Lua filters | `/Users/mizuy/lab/paper/filters/*.lua` |
| Bundled CSL files | `/Users/mizuy/lab/paper/csl/*.csl` |
| Bundled templates | `/Users/mizuy/lab/paper/templates/` |

The target paper directory is passed with `PAPER_DIR`.

## Common Tasks

```bash
cd /Users/mizuy/lab/paper
task paper:docx PAPER_DIR=/path/to/paper
task paper:words PAPER_DIR=/path/to/paper
task paper:build-bib PAPER_DIR=/path/to/paper
task paper:sync-assets PAPER_DIR=/path/to/paper
```

## Paper Directory

A target paper directory usually contains:

```text
paper/
  manuscript.md
  supplementary.md
  reference.docx
  vancouver.csl
  references.bib
  fig/
  table/
  script/filters/
  reference/
```

`supplementary.md` is optional. `references.bib` and `.build/*.md` are generated.

## Bibliography

`references.bib` is generated from citation keys in Markdown, such as `[@Example2024-aa]`.

```bash
cd /Users/mizuy/lab/paper
task paper:build-bib PAPER_DIR=/path/to/paper
```

Set `PAPERPILE_BIB=/path/to/paperpile.bib` if the default Paperpile export is not available.

## Imports

`@import "relative/path.md"` is expanded before pandoc. Paths are resolved relative to the Markdown file containing the import.

This is mainly used for generated table fragments:

```markdown
@import "table/table_1_csv.md"
```

## CSL

Use `PAPER_CSL` to choose a bundled CSL file, a paper-local file, or an absolute path.

```bash
task paper:docx PAPER_DIR=/path/to/paper PAPER_CSL=vancouver.csl
task paper:docx PAPER_DIR=/path/to/paper PAPER_CSL=/path/to/custom.csl
```

## Manual Pandoc Flow

The task wraps this flow:

1. Build `references.bib`.
2. Expand `@import` into `.build/<stem>.md`.
3. Run pandoc with `script/filters/*.lua`, `reference.docx`, citeproc, and CSL.
4. Patch docx table layout.

Prefer `task paper:docx` for normal use.

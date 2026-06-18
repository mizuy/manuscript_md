# lab-paper

Shared paper-building tooling for lab projects.

This project owns the reusable Markdown-to-Word workflow:

- build `references.bib` from manuscript citations and `paperpile.bib`
- expand `@import "table/foo_csv.md"` fragments before pandoc
- resolve bundled or paper-local CSL files
- run pandoc with reusable Lua filters
- patch generated docx tables for Word layout
- count manuscript words
- sync reusable Lua filters into a paper directory

External instructions and editor integrations should point users and agents to this project rather than duplicating the build scripts.

## Workspace Usage

Add this folder to the same VS Code/Cursor workspace as the research repository.

Example workspace:

```json
{
  "folders": [
    { "path": "/path/to/research-repo" },
    { "path": "/Users/mizuy/lab/paper" }
  ]
}
```

Run tasks from this project and pass the target paper directory with `PAPER_DIR`.

```bash
cd /Users/mizuy/lab/paper
task paper:docx PAPER_DIR=/path/to/research-repo/paper
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

- `task paper:docx PAPER_DIR=/path/to/paper`: build Word docx files.
- `task paper:words PAPER_DIR=/path/to/paper`: count abstract and main-text words.
- `task paper:build-bib PAPER_DIR=/path/to/paper`: generate `references.bib`.
- `task paper:sync-assets PAPER_DIR=/path/to/paper`: copy Lua filters if missing.
- `task paper:sync-assets PAPER_DIR=/path/to/paper OVERWRITE=1`: overwrite existing copied filters from this project.

## Paper Directory Expectations

A target paper directory should contain:

```text
paper/
  manuscript.md
  reference.docx
  script/filters/*.lua
  references.bib
```

`paper:sync-assets` can create or update `script/filters`.

Research repositories remain responsible for analysis outputs and project-specific artifact syncing, such as copying tables and figures into `paper/table` or `paper/fig`.

## CLI

The Taskfile calls the `lab-paper` CLI. Direct usage is also available:

```bash
uv run lab-paper build-bib --paper-dir /path/to/paper --scan-markdown
uv run lab-paper expand-imports /path/to/paper/manuscript.md -o /path/to/paper/.build/manuscript.md
uv run lab-paper patch-docx /path/to/paper/manuscript.docx
uv run lab-paper word-count --paper-dir /path/to/paper
uv run lab-paper sync-assets --paper-dir /path/to/paper
```

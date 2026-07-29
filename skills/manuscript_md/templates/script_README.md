# Paper scripts (optional)

By default, papers do **not** vendor Lua filters or build scripts.
Use the **manuscript_md** skill / Taskfile:

```bash
cd /Users/mizuy/lab/manuscript_md
task paper:docx PAPER_DIR=/path/to/this/paper
task paper:words PAPER_DIR=/path/to/this/paper
```

From a research-repo wrapper:

```bash
task paper:docx
```

## Optional local override

Only if you need paper-specific Lua:

```bash
cd /Users/mizuy/lab/manuscript_md
task paper:sync-assets PAPER_DIR=/path/to/this/paper
# then edit script/filters/*.lua
```

## Literature notes

```bash
uv --directory /Users/mizuy/lab/manuscript_md run lab-paper ingest-reference --ref-dir reference/
```

See `/Users/mizuy/lab/manuscript_md/docs/REFERENCE_INGEST.md`.

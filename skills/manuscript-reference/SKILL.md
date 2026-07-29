---
name: manuscript-reference
description: >-
  Manage paper-directory literature with a Paperpile (or compatible) BibTeX
  export: resolve pandoc-ids, build references.bib from [@key], ingest
  reference/ notes, update checkme_paper.md. Use when adding citations or
  regenerating bibliographies. Not for Obsidian vault wiki ingest.
---

# manuscript-reference

## When / not

| Use when | Do not use when |
|----------|-----------------|
| `[@pandoc-id]` → `references.bib` | Obsidian vault wiki summaries |
| `reference/md` + PDF notes ingest | Markdown → docx → **manuscript_md** |
| `checkme_paper.md` dashboard | Word Compare → **word-docx-compare** |

**Companions:** [manuscript_md](../manuscript_md/SKILL.md) · [word-docx-compare](../word-docx-compare/SKILL.md)

**Install:** [`docs/INSTALL.md`](../../docs/INSTALL.md) · **GitHub:** https://github.com/mizuy/manuscript_md

---

```text
skills/manuscript-reference/
  SKILL.md
  scripts/
    build_bibliography.py
    bib_parse.py
    ingest_reference.py
    checkme_dashboard.py
```

## Commands

```bash
export PAPERPILE_BIB=/path/to/paperpile.bib
export PAPER_PROJECT=/path/to/manuscript_md
cd "$PAPER_PROJECT"

task paper:build-bib PAPER_DIR=/path/to/paper
task paper:ingest-reference PAPER_DIR=/path/to/paper
task paper:checkme PAPER_DIR=/path/to/paper
```

Or: `uv run lab-paper build-bib|ingest-reference|checkme …`

## Layout (paper side)

```text
paper/
  manuscript.md / supplementary.md
  references.bib          # generated
  checkme_paper.md        # auto dashboard + hand notes
  manual_entries.bib      # optional gaps
  reference/md pdf/
```

Do not vendor these scripts into the paper. Deep doc:
[`docs/REFERENCE_INGEST.md`](../../docs/REFERENCE_INGEST.md).

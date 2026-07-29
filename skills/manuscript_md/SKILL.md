---
name: manuscript_md
description: >-
  Write scientific papers in Markdown and build Word docx (pandoc, Lua filters,
  reference.docx, submission TIFF). Use when editing manuscript.md or
  supplementary.md, building review or journal upload packages, or applying
  prose/table/supplement conventions. Companions: manuscript-reference,
  word-docx-compare.
---

# manuscript_md

## When / not

| Use when | Do not use when |
|----------|-----------------|
| Writing `manuscript.md` / `supplementary.md` | Vault/wiki literature notes only |
| Building review docx or submission TIFF | Bib / `reference/` ingest only → **manuscript-reference** |
| Prose / table / supplement conventions | Word Compare / version tag → **word-docx-compare** |

**Companions:** [manuscript-reference](../manuscript-reference/SKILL.md) · [word-docx-compare](../word-docx-compare/SKILL.md)

**Install:** [`docs/INSTALL.md`](../../docs/INSTALL.md) · **GitHub:** https://github.com/mizuy/manuscript_md

---

```text
skills/manuscript_md/
  SKILL.md
  scripts/     # expand_imports, patch_docx, word_count, bootstrap_paper, …
  filters/     # pandoc Lua (used by absolute path)
  csl/         # bundled citation styles
  templates/   # skeletons, reference.docx, Taskfile.paper.example.yml
```

Papers keep **minimal** local files. Do not vendor filters / CSL / `reference.docx`
unless overriding.

## New paper

[`docs/NEW_PAPER.md`](../../docs/NEW_PAPER.md)

```bash
export PAPER_PROJECT=/path/to/manuscript_md   # this clone
cd "$PAPER_PROJECT"
uv sync
./skills/manuscript_md/scripts/bootstrap_paper.sh my_paper docs vancouver.csl
task paper:docx PAPER_DIR=/path/to/docs/my_paper PAPERPILE_BIB=/path/to/paperpile.bib
```

Research repos: flatten-include `$PAPER_PROJECT/Taskfile.yml`
([`templates/Taskfile.paper.example.yml`](templates/Taskfile.paper.example.yml)).
**Includes rules:** [`docs/WORKFLOW.md`](../../docs/WORKFLOW.md#consumer-includes).

## Docs

| Doc | Content |
|-----|---------|
| [`INSTALL.md`](../../docs/INSTALL.md) | Public install |
| [`NEW_PAPER.md`](../../docs/NEW_PAPER.md) | Bootstrap |
| [`WORKFLOW.md`](../../docs/WORKFLOW.md) | End-to-end + includes |
| [`PROSE_CONVENTIONS.md`](../../docs/PROSE_CONVENTIONS.md) | Body prose / figures |
| [`PAPER_LAYOUT.md`](../../docs/PAPER_LAYOUT.md) | Minimal paper directory |
| [`TABLE_WORD.md`](../../docs/TABLE_WORD.md) | Tables |
| [`SUPPLEMENTARY_POLICY.md`](../../docs/SUPPLEMENTARY_POLICY.md) | Supplement |
| [`SUBMISSION_CHECKLIST.md`](../../docs/SUBMISSION_CHECKLIST.md) | Checklist |

## Prose (summary)

1. No body `**bold**` (Abstract labels + Figure/Table lead-ins only).
2. No inline code / pipeline identifiers in Methods/Results.
3. Cite `[@pandoc-id]` — rebuild bib via **manuscript-reference**.
4. Claims: paper-local `manuscript_instruction.md` / `comment.md`.

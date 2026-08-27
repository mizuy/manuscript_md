# New paper — minimal recipe

From skill **manuscript_md**. Creates a paper directory without vendoring filters.

## 1) Bootstrap

```bash
export PAPER_PROJECT=/path/to/manuscript_md   # this clone
cd "$PAPER_PROJECT"
uv sync
./skills/manuscript_md/scripts/bootstrap_paper.sh my_paper docs vancouver.csl
# → docs/my_paper/{manuscript,supplementary,fig,table,reference}/
# reference.docx + CSL come from the skill at build time
```

Or copy skeletons from `skills/manuscript_md/templates/`.

## 2) Research-repo Taskfile (flatten include)

See [`skills/manuscript_md/templates/Taskfile.paper.example.yml`](../skills/manuscript_md/templates/Taskfile.paper.example.yml).

**Constraints:** [`WORKFLOW.md`](WORKFLOW.md#consumer-includes).

## 3) First builds

```bash
export PAPERPILE_BIB=/path/to/paperpile.bib
task paper:docx PAPER_DIR=/path/to/docs/my_paper
task paper:checkme PAPER_DIR=/path/to/docs/my_paper
task paper:ingest-reference PAPER_DIR=/path/to/docs/my_paper
```

## 4) Skills

| Need | Skill |
|------|-------|
| Prose / docx / submission / author list | manuscript_md |
| Bib / reference notes / checkme | manuscript-reference |
| Word Compare / versions | word-docx-compare |
| STROBE checklist (observational) | strobe-checklist |

Install overview: [`INSTALL.md`](INSTALL.md).

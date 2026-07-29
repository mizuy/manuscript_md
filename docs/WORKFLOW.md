# Paper workflow (manuscript_md)

End-to-end loop used in lab papers (reference implementation:
`pccrc/docs/paper_lag0`). Research repos provide thin `task paper:*` wrappers;
tooling lives in this project.

## Directory roles

```text
paper/
  manuscript.md              # submission prose (canonical)
  supplementary.md           # submission supplement only
  manuscript_instruction.md  # project writing rules
  comment.md                 # claims / reviewer strategy (not submitted)
  checkme_paper.md           # optional citation dashboard
  references.bib             # generated
  # reference.docx           # optional override; default = skill templates/
  fig/                       # PNG for review docx embeds
  table/                     # CSV + @import md fragments
  reference/                 # optional literature notes + PDFs
  versions/                  # tagged docx + _diff.docx + manifest.yml
  submission/                # figure-free docx + TIFF @ 600 dpi
  _internal_review_notes.md  # never cite from manuscript/supplementary
```

Build scripts and Lua filters live in **skills** (`skills/…`), not under
the paper directory.

Full layout: [`PAPER_LAYOUT.md`](PAPER_LAYOUT.md).

## Typical loop

```bash
# 0) Analysis (research repo)
task build
task <analysis>                 # writes tasks/<name>/out/

# 1) Sync artifacts into the paper directory
task paper:fig                  # and/or paper:table / paper_* bundle
task paper:fig-audit            # MD5 / presence check when used

# 2) Edit Markdown → review docx (figures embedded)
cd /Users/mizuy/lab/manuscript_md   # or research-repo wrappers
task paper:docx PAPER_DIR=/path/to/paper
task paper:words PAPER_DIR=/path/to/paper

# 3) Final upload package
task paper:submission PAPER_DIR=/path/to/paper
# → submission/{manuscript,supplementary}.docx
# → submission/*_with_figures.docx
# → submission/figures/Figure_*.tif, Supplementary_Figure_*.tif

# 4) Word collaborator cycle (macOS + Microsoft Word)
#    skill: skills/word-docx-compare/
task paper:versions
task paper:tag VERSION=N
task paper:diff                 # vs manifest diff_base
task paper:compare BASE=... CHANGED=... OUTPUT=versions/..._diff.docx
```

Paths for Word Compare must stay under the paper directory (`/tmp` is blocked).

## Consumer includes (research-repo Taskfile)

Preferred pattern: flatten-include this project's `Taskfile.yml`.

```yaml
includes:
  manuscript_md:
    taskfile: ${PAPER_PROJECT:-../manuscript_md}/Taskfile.yml
    dir: ${PAPER_PROJECT:-../manuscript_md}
    flatten: true
    vars:
      PAPER_DIR: /absolute/path/to/paper
      PAPER_CSL: vancouver.csl
      FILES: manuscript supplementary
```

### Constraints (go-task)

1. **`includes.taskfile` / `dir`:** only shell env expansion (`${PAPER_PROJECT:-…}`).
   Task `{{.VAR}}` templates are **not** expanded in those fields.
2. **Override literals in `includes.vars`:** pass concrete values for
   `PAPER_DIR`, `PAPER_CSL`, `FILES`. Do **not** write `PAPER_CSL: '{{.PAPER_CSL}}'`
   — included Taskfile vars win, and self-references collapse to the skill default
   (e.g. vancouver).
3. **CLI vs includes.vars:** values set in `includes.vars` often beat
   `task paper:docx FILES=manuscript`. Change the include literals (or call
   manuscript_md Taskfile directly) to override.
4. **`TASKFILE_DIR` inside includes.vars** resolves to the **included** project
   (manuscript_md), not the research repo — use absolute `PAPER_DIR`.

Example: [`Taskfile.paper.example.yml`](../skills/manuscript_md/templates/Taskfile.paper.example.yml).  
New paper: [`NEW_PAPER.md`](NEW_PAPER.md).

## Separation of concerns

| Layer | Owner | Writes |
|-------|--------|--------|
| Analysis tasks | research repo | `tasks/*/out/` |
| Paper fig/table sync | research repo wrappers | `fig/`, `table/` |
| Markdown → docx / bib / TIFF | **manuscript_md** | `*.docx`, `references.bib`, `submission/` |
| Word Compare / version tag | **word-docx-compare** (bundled) | `versions/*_diff.docx` |
| Claims / cohort wording | paper `comment.md` / `manuscript_instruction.md` | — |

## `@import` tables

```markdown
**Table 1.** Baseline characteristics

@import "table/table_1_primary_analytic_csv.md"

Abbreviations …
```

Expand happens before pandoc. Update `table/` before `paper:docx`. Details:
[`TABLE_WORD.md`](TABLE_WORD.md).

## Citations

- Cite with `[@pandoc-id]` only.
- Rebuild `references.bib` from manuscript scan (do not maintain a parallel key
  list for the manuscript).
- Optional notes under `reference/` — skill
  [`manuscript-reference`](../skills/manuscript-reference/SKILL.md) and
  [`REFERENCE_INGEST.md`](REFERENCE_INGEST.md).
- Citation dashboard: `task paper:checkme` → `checkme_paper.md` (auto section;
  hand notes below markers).

## Versions (`versions/manifest.yml`)

When collaborators return Word edits:

1. Save returns under `versions/` (e.g. `…_MS.docx`, `…_MS_approved.docx`).
2. Record entries in `manifest.yml` with `diff_base` pointing at the approved
   return when tagging the next internal pandoc build.
3. `task paper:tag` / `paper:diff` use the manifest; formatting-only markup is
   stripped by default (see word-docx-compare skill).

## Supplementary vs internal notes

Policy: [`SUPPLEMENTARY_POLICY.md`](SUPPLEMENTARY_POLICY.md).  
Checklist: [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md).

## Reference implementation

`pccrc`: `docs/paper_lag0/` + `task paper_*` / `task paper:*` in `Taskfile.yml`.

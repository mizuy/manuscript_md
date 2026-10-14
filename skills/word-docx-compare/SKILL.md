---
name: word-docx-compare
description: >-
  Compare Word docx files into a tracked-changes diff (character-level,
  text only, no Word needed; optional Microsoft Word Compare on macOS) and
  tag paper versions under versions/. Formatting changes are ignored by
  default. Use when collaborators edit in Word, generating docx diffs from
  pandoc output, Word Compare from CLI, paper version tagging, or
  ADR_manuscript_vN_diff.docx.
---

# word-docx-compare

## When / not

| Use when | Do not use when |
|----------|-----------------|
| Tracked-changes docx diff (any OS; Word optional) | Markdown → docx → **manuscript_md** |
| `versions/` tag + manifest diff_base | Paperpile / bib / checkme → **manuscript-reference** |
| Collaborator return vs pandoc rebuild | |

**Companions:** [manuscript_md](../manuscript_md/SKILL.md) · [manuscript-reference](../manuscript-reference/SKILL.md) · [strobe-checklist](../strobe-checklist/SKILL.md)

---

**Install:** [`docs/INSTALL.md`](../../docs/INSTALL.md) · **GitHub:** https://github.com/mizuy/manuscript_md

---

Bundled with **manuscript_md**. Executable tooling:

```text
skills/word-docx-compare/scripts/
```

The default engine is pure Python (`diff_docx.py`) and needs no Word.
`--engine word` uses Microsoft Word on macOS via `osascript` and Word's
AppleScript `compare` command.

Pair with [manuscript_md](../manuscript_md/SKILL.md) for Markdown → docx and
[manuscript-reference](../manuscript-reference/SKILL.md) for bibliographies.
`versions/manifest.yml` resolution uses `version_manifest.py` in this repo
(`skills/manuscript_md/scripts/` or compat `scripts/`).

## Use This When

- A collaborator edits the manuscript in Word and you need a tracked-changes diff.
- You tag a new pandoc-built `manuscript.docx` as `versions/ADR_manuscript_v{N}.docx`.
- You want a diff against the previous version without style/formatting noise.

## Word Engine Constraints (`--engine word` only)

1. **Do not use `/tmp`.** Word's sandbox blocks grant-access there. Use paths under
   the paper directory (e.g. `docs/paper_lag0/versions/`).
2. **First run:** allow Terminal/Cursor to control Microsoft Word (Automation).
3. **Default:** detect formatting changes, apply the revised formatting, and
   remove only formatting-revision markup from the saved DOCX. Text
   insert/delete revisions remain visible. Pass `--format` to keep formatting
   revisions visible.
4. **After save:** when `OUTPUT.docx` is given, Word closes all documents and
   quits (so `task paper:tag` / `task paper:diff` do not leave Word open).
   Omit `OUTPUT` to leave the comparison open for manual review.

## Compare Two docx Files

From the manuscript_md project root (or set `PAPER_PROJECT`):

```bash
PAPER_PROJECT=/path/to/manuscript_md   # e.g. lab/manuscript_md checkout
SKILL="$PAPER_PROJECT/skills/word-docx-compare"

# BASE = older Word edit, CHANGED = newer (often pandoc manuscript.docx)
"$SKILL/scripts/compare_docx.sh" \
  /path/to/paper/versions/ADR_manuscript_v2.docx \
  /path/to/paper/manuscript.docx \
  /path/to/paper/versions/ADR_manuscript_v3_diff.docx
```

Leave OUTPUT omitted to write a preview under `.compare/` and open it in Word.

## Python Engine (default)

The default engine writes the diff with `diff_docx.py`
(`manuscript-md diff-docx`), without Word:

- Compares text only. Style, run formatting, and paragraph properties are
  ignored; the output keeps CHANGED's formatting.
- Diffs at the character level inside each paragraph, so `1,234` → `1,345`
  shows as `1,[-2-]34{+5+}`, not a whole-line replacement.
- Short matches between edits are merged (diff-match-patch style), so
  `studied` → `analysed` shows as `[-studi-]{+analys+}ed`. `--raw` turns this off.
- Works on Linux/CI. Tracked changes already in the inputs are accepted first.

To use Word Compare instead, pass `--engine word` (or set
`DOCX_DIFF_ENGINE=word`, or `task paper:compare ENGINE=word ...`).
`--format` (show formatting revisions) always uses Word.

Table rows added or removed as a whole become row revisions. Images are
compared by content, so a replaced figure shows as inserted.

Limits: only the body (`word/document.xml`) is compared, so footnotes,
headers, and comments are not diffed. Deleted paragraphs are restored as
plain text; a removed or replaced image is not shown as deleted.

Sample files to open in Word: `tests/fixtures/docx_diff/` (see its README).

## Tag a New Version + Auto-diff

When `versions/manifest.yml` exists, `diff_base` in the manifest selects the
Compare BASE (e.g. approved MS return). Otherwise falls back to `v{N-1}`.

`tag_version.sh` finds `version_manifest.py` via `PAPER_PROJECT`, or relative to
this skill (`../../scripts/` when installed under `skills/`).

```bash
PAPER_PROJECT=/path/to/manuscript_md
SKILL="$PAPER_PROJECT/skills/word-docx-compare"
PAPER_DIR=/path/to/paper
VERSION_PREFIX=ADR_manuscript

PAPER_DIR="$PAPER_DIR" VERSION_PREFIX="$VERSION_PREFIX" PAPER_PROJECT="$PAPER_PROJECT" \
  "$SKILL/scripts/tag_version.sh" 5 manuscript.docx
```

Writes:

- `versions/ADR_manuscript_v3.docx` — copy of source
- `versions/ADR_manuscript_v3_diff.docx` — diff vs manifest `diff_base` (or v2)

## Research-repo Integration

Wire Taskfile tasks with
[templates/Taskfile.snippet.yml](templates/Taskfile.snippet.yml).
Typical commands from a research repo that sets `PAPER_PROJECT`:

```bash
task paper:compare BASE=versions/ADR_manuscript_v2.docx CHANGED=manuscript.docx OUTPUT=versions/diff.docx
task paper:tag VERSION=3
task paper:diff              # latest manifest entry vs diff_base
task paper:versions          # list + validate manifest
```

Default skill path: `$PAPER_PROJECT/skills/word-docx-compare`.

## Typical Workflow (Word collaborators)

1. Receive collaborator's Word docx → save under paper dir or `versions/`.
2. Edit `manuscript.md` → `task paper:docx`.
3. Compare or tag:

```bash
task paper:compare \
  BASE=versions/ADR_manuscript_v2.docx \
  CHANGED=manuscript.docx \
  OUTPUT=versions/ADR_manuscript_v3_diff.docx
```

4. Send the `_diff.docx` back for review.

## Scripts

| Script | Role |
|--------|------|
| `compare_docx.applescript` | Word Compare + optional save |
| `compare_docx.sh` | Shell wrapper; `--engine python\|word`, `--format` (Word) |
| `apply_formatting_without_tracking.py` | Strip formatting-revision markup |
| `diff_docx.py` | Default engine: character-level text diff, no Word |
| `tag_version.sh` | `versions/{PREFIX}_v{N}.docx` + `_diff.docx` |

## Local discovery

For Agent discovery outside the manuscript_md workspace, symlink this
directory to `~/.agents/skills/word-docx-compare` (and `~/.claude/skills/`
for Claude Code). See [`docs/INSTALL.md`](../../docs/INSTALL.md).

## Additional Resources

- Sandbox, AppleScript parameters, troubleshooting: [reference.md](reference.md)
- Taskfile snippet for new papers: [templates/Taskfile.snippet.yml](templates/Taskfile.snippet.yml)

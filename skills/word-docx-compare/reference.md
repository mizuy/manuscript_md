# word-docx-compare — reference

## AppleScript compare command

Word exposes `compare` on the active document (see `Word.sdef`):

```applescript
compare active document path changedDoc detect format changes true
```

| Parameter | Default in our scripts | Effect |
|-----------|------------------------|--------|
| `detect format changes` | `true` | Revised formatting enters the comparison result |
| `author name` | (Word default) | Revision author label |
| `target` | new document | Where comparison output appears |

By default, Word first saves a comparison with formatting detection enabled.
The wrapper then removes only WordprocessingML formatting-change elements
(`rPrChange`, `pPrChange`, table/cell/row/grid property changes, and
`sectPrChange`) from the saved DOCX. The current (revised) formatting remains,
while `w:ins` and `w:del` text revisions stay tracked. `--format` skips this
post-processing step and keeps formatting revisions visible.

## Sandbox workaround

Before comparing, open the changed document once and close without saving.
This lets Word access both files under the project path (WordGit pattern).

## Save pattern

After compare, the result is the **active document** (not the opened base doc):

```applescript
set newDoc to active document
save as newDoc file name (POSIX file outPath)
close newDoc saving no
```

## Version naming

```
versions/
  ADR_manuscript_v1.docx
  ADR_manuscript_v2.docx
  ADR_manuscript_v3.docx
  ADR_manuscript_v3_diff.docx   # v2 → v3, content-only by default
```

Set `VERSION_PREFIX` per paper (e.g. `ADR_manuscript`, `SUPP_v`).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Grant access / sandbox error | Move files out of `/tmp` into paper dir |
| Compare does not start | Allow Automation for Terminal/Cursor → Word |
| Too many formatting marks | Omit `--format`; formatting is applied but its revision markup is removed |
| `save as` fails | Use full compare+save flow in `compare_docx.applescript` |

## Windows

Not supported by this skill. Use VBA `Application.CompareDocuments` with
`CompareFormatting:=False` or a COM wrapper.

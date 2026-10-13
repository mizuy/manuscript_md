# docx diff samples

Each numbered folder has `old.md` / `new.md`, the docx built from them, and
`diff.docx` (character-level tracked changes from `manuscript-md diff-docx`).
Open `diff.docx` in Word to check the result.

| Folder | What changes |
|--------|--------------|
| 01_english | Word and number edits in English text |
| 02_japanese | Japanese text edits |
| 03_formatting_only | Bold/italic/heading level only; expect no revisions |
| 04_paragraphs | Paragraphs added, removed, and edited |
| 05_table | Cell edits, a row added (Table 1), a row removed (Table 2) |
| 06_symbols | ±, μ, en dash, ≤, italic *P* |
| 07_manuscript | Short manuscript: abstract, citations, table, figure |
| 08_figures | Caption edits, a replaced image, a replaced figure |

`old.docx` uses pandoc's default styles and `new.docx` uses the bundled
`reference.docx`, so every style differs; only text changes should show.

Rebuild with `./build.sh` (needs pandoc).

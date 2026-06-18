# Paper Scripts

## Pandoc → docx

論文ルートで実行（repository の wrapper Taskfile がある場合）:

```bash
task paper:docx
task paper:docx FILES=manuscript PAPER_CSL=vancouver.csl
```

手動（論文ルート = `/path/to/paper`）:

```bash
cd /path/to/paper
export PAPERPILE_BIB=/path/to/paperpile.bib

uv --directory /Users/mizuy/lab/paper run lab-paper build-bib \
  --paper-dir . --scan-markdown -o references.bib

pandoc -f markdown+lists_without_preceding_blankline+fenced_divs \
  --lua-filter=script/filters/pagebreak.lua \
  --lua-filter=script/filters/landscape.lua \
  --lua-filter=script/filters/table_word.lua \
  --lua-filter=script/filters/superscript.lua \
  --reference-doc=reference.docx \
  --citeproc --bibliography=references.bib --csl=vancouver.csl \
  manuscript.md -o manuscript.docx

uv --directory /Users/mizuy/lab/paper run lab-paper patch-docx manuscript.docx
```

## 文献メモ ingest（任意）

project 汎用: `uv --directory /Users/mizuy/lab/paper run lab-paper ingest-reference --ref-dir reference/`

詳細: `/Users/mizuy/lab/paper/docs/REFERENCE_INGEST.md` / `/Users/mizuy/lab/paper/docs/PAPER_LAYOUT.md`

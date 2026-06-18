# Reference summaries

1 論文 = `md/{pandoc-id}.md` + `pdf/{pandoc-id}.pdf` + `reference.bib`（ingest 生成）。

- 手順: `/Users/mizuy/lab/paper/docs/REFERENCE_INGEST.md`
- レイアウト: `/Users/mizuy/lab/paper/docs/PAPER_LAYOUT.md`
- テンプレ: `_template.md`（`/Users/mizuy/lab/paper/templates/reference_note_template.md`）

**ingest:** `uv run python script/ingest_reference.py`

原稿の引用は `manuscript.md` の `[@pandoc-id]` → 論文ルート `references.bib`（`citation_keys.txt` は使わない）。

## 一覧

（ingest 後に README を再生成）

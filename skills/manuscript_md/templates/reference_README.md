# Reference summaries

1 論文 = `md/{pandoc-id}.md` + `pdf/{pandoc-id}.pdf` + `reference.bib`（ingest 生成）。

- 手順: `/Users/mizuy/lab/manuscript_md/docs/REFERENCE_INGEST.md`
- レイアウト: `/Users/mizuy/lab/manuscript_md/docs/PAPER_LAYOUT.md`
- テンプレ: `_template.md`（`/Users/mizuy/lab/manuscript_md/templates/reference_note_template.md`）

**ingest:** `uv run manuscript-md ingest-reference --ref-dir reference/`


原稿の引用は `manuscript.md` の `[@pandoc-id]` → 論文ルート `references.bib`（`citation_keys.txt` は使わない）。

## 一覧

（ingest 後に README を再生成）

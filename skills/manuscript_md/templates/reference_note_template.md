# {English title}

## メタデータ

<!-- auto: ingest_reference.py（reference.bib）— この節は手編集しない -->

- **pandoc-id:** `{BibTeXKey}`（原稿: `[@{BibTeXKey}]`）
- **PDF:** [../pdf/{BibTeXKey}.pdf](../pdf/{BibTeXKey}.pdf)（未取得のときは —）
- **DOI:** [{doi}](https://doi.org/{doi}) または —
- **PubMed:** [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/) または —
- **URL:** [{url}]({url})（bib の `url` または doi リンク）または —
- **誌・巻号:** {journal, year, volume(issue), pages}

## 著者

{bib の著者を列挙。所属の詳細は下表で PDF から転記}

| 著者 | 所属（論文記載どおり） | 研究グループ・メモ |
| --- | --- | --- |
| {Family Given} | {Institution, Country} | {レジストリ・学会・共著グループ} |

## Abstract（English）

<!-- auto: ingest_reference.py（reference.bib の abstract 全文をそのまま）— 要約・編集しない -->

> {paperpile.bib / reference.bib の `abstract` 全文}

## Abstract（日本語訳）

<!-- 上記 Abstract（English）の全文を日本語に翻訳。要約・省略・再構成しない -->

{Abstract（English）の全文翻訳}

## PICO / PECO

| 要素 | 内容 |
| --- | --- |
| **P** Population / Problem | {PDF 本文から} |
| **I** Intervention / **E** Exposure | {PDF 本文から} |
| **C** Comparison | {PDF 本文から} |
| **O** Outcome | {PDF 本文から} |

## 主要結果

{PDF の Results / Tables / Figures を精読して記入。具体数値必須}

- **対象・追跡:** …
- **イベント・アウトカム定義:** …
- **効果量:** HR/OR … (95% CI …)
- **その他:** …

## 概要

{任意。Abstract より詳しいデザイン・限界}

## 本研究との関連

{任意。引用方針・用語の違い・比較ポイント}

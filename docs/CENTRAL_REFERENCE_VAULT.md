# Central Reference Vault

Long-term literature notes can live in a central Markdown vault while paper
directories keep only manuscript-facing outputs. Paperpile remains responsible
for metadata and PDF acquisition; this project ingests those assets into a
reading/annotation layer.

## Responsibilities

| Layer | Owns |
|-------|------|
| Paperpile | BibTeX metadata, citation key / pandoc-id, PDF acquisition |
| Central vault | Markdown source text, literature notes, classification, memo |
| Paper project | Citation intent, manuscript-specific notes, exported `references.bib` |

Do not edit Paperpile-derived metadata in the vault. Re-run ingest to refresh
auto sections.

## Layout

```text
vault/
  references/
    papers/
      Example2024-aa.md          # central literature note
    pdf/
      Example2024-aa.pdf         # copied from Paperpile/exported location
    source_md/
      Example2024-aa.md          # PDF/document converted to Markdown
  projects/
    paper_lag0/
      reference_keys.txt
      notes/
        Example2024-aa.md        # project-specific citation intent
```

The central note keeps auto-updated metadata and source links separate from
human sections such as relevance, citation intent, and free-form memo.

## Ingest one reference

When the PDF has already been converted to Markdown by another tool:

```bash
uv run lab-paper vault-reference \
  --vault-dir /path/to/vault \
  --key Example2024-aa \
  --paperpile-bib /path/to/paperpile.bib \
  --source-md /path/to/Example2024-aa.md \
  --document-type guideline \
  --project paper_lag0
```

When only a PDF is available, the command can use `pdftotext` to create a light
Markdown/plain Markdown source file:

```bash
uv run lab-paper vault-reference \
  --vault-dir /path/to/vault \
  --key Example2024-aa \
  --paperpile-bib /path/to/paperpile.bib \
  --pdf /path/to/Example2024-aa.pdf \
  --document-type original_article
```

If `pdftotext` is unavailable or a richer converter was used, pass `--source-md`
instead. The Markdown source is intentionally minimally structured so that
guidelines, reviews, reports, protocols, and original articles can all be stored
without forcing an article-only schema.

Taskfile wrapper:

```bash
task reference:vault-ingest VAULT_DIR=/path/to/vault -- \
  --key Example2024-aa \
  --paperpile-bib /path/to/paperpile.bib \
  --source-md /path/to/Example2024-aa.md \
  --document-type review \
  --project paper_lag0
```

## Classification policy

Start with a small core shared by all document types:

```yaml
document_type: original_article | guideline | review | report | protocol | other
topics: []
review_status: unreviewed | reviewed
```

Add type- or project-specific fields later in human sections or project notes.
Avoid forcing PICO/PECO or Results sections onto document types where they do
not fit.

## Relationship to paper-local `reference/`

`docs/REFERENCE_INGEST.md` describes the existing paper-local workflow:

```text
paper/reference/md/
paper/reference/pdf/
paper/reference/reference.bib
```

The central vault workflow is additive. A later export step can project selected
vault references back into a paper directory, but manuscript builds should
continue to rely on `references.bib` generated from `[@pandoc-id]` citations.

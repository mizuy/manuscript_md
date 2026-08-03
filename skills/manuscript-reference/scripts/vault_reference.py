#!/usr/bin/env python3
"""Ingest one Paperpile reference into a central Markdown vault.

Paperpile remains the source for BibTeX metadata and PDF acquisition. This
script creates a vault-side literature note, copies the PDF when provided, and
stores a Markdown rendition of the source text without assuming a journal-article
structure.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from bib_parse import BibMeta, journal_citation, link_or_dash, load_bib  # noqa: E402


REFERENCE_ROOT = Path("references")


def _clean_link_path(path: Path) -> str:
    return path.as_posix()


def _copy_file(src: Path, dst: Path, *, overwrite: bool = False) -> bool:
    if dst.exists() and not overwrite:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _normalize_pdf_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\f", "\n\n---\n\n")
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines) + "\n"


def pdf_to_markdown(pdf_path: Path) -> str:
    """Convert a PDF to lightly normalized Markdown using pdftotext."""
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "pdftotext is required for PDF conversion; pass --source-md when "
            "Markdown was created by another tool"
        ) from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip()
        raise RuntimeError(f"pdftotext failed for {pdf_path}: {detail}") from exc
    return _normalize_pdf_text(proc.stdout)


def _section_pattern(heading: str) -> re.Pattern[str]:
    return re.compile(rf"^## {re.escape(heading)}\n.*?(?=^## |\Z)", re.M | re.S)


def replace_or_insert_section(md_text: str, heading: str, body: str) -> str:
    section = f"## {heading}\n\n{body.rstrip()}\n\n"
    pattern = _section_pattern(heading)
    if pattern.search(md_text):
        return pattern.sub(section, md_text, count=1)

    title = re.match(r"^# .+\n\n?", md_text)
    if title:
        return md_text[: title.end()] + section + md_text[title.end() :]
    return section + md_text


def _metadata_body(key: str, meta: BibMeta | None) -> str:
    title = meta.title if meta and meta.title else "—"
    year = meta.year if meta and meta.year else "—"
    authors = "; ".join(meta.authors) if meta and meta.authors else "—"
    journal = journal_citation(meta) if meta else "—"
    doi = meta.doi if meta else ""
    pmid = meta.pmid if meta else ""
    url = meta.url if meta else ""
    if not url and doi:
        url = f"https://doi.org/{doi}"

    lines = [
        "<!-- auto: vault_reference.py（Paperpile BibTeX）— この節は手編集しない -->",
        "",
        f"- **pandoc-id:** `{key}`",
        f"- **Title:** {title}",
        f"- **Authors:** {authors}",
        f"- **Year:** {year}",
        f"- **誌・巻号:** {journal}",
    ]
    lines.append(link_or_dash("DOI", doi, f"https://doi.org/{doi}") if doi else "- **DOI:** —")
    lines.append(
        link_or_dash("PubMed", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
        if pmid
        else "- **PubMed:** —"
    )
    if url:
        display = url.replace("https://", "").replace("http://", "")
        if len(display) > 80:
            display = display[:77] + "..."
        lines.append(link_or_dash("URL", display, url))
    else:
        lines.append("- **URL:** —")
    return "\n".join(lines)


def _source_body(
    *,
    pdf_rel: Path | None,
    source_md_rel: Path | None,
    document_type: str,
) -> str:
    pdf = f"[{pdf_rel.name}]({_clean_link_path(pdf_rel)})" if pdf_rel else "—"
    source_md = (
        f"[{source_md_rel.name}]({_clean_link_path(source_md_rel)})" if source_md_rel else "—"
    )
    return "\n".join(
        [
            "<!-- auto: vault_reference.py — この節は手編集しない -->",
            "",
            f"- **文献タイプ:** `{document_type}`",
            f"- **PDF:** {pdf}",
            f"- **Markdown本文:** {source_md}",
        ]
    )


def _default_note(key: str, title: str, document_type: str) -> str:
    return "\n".join(
        [
            f"# {title or key}",
            "",
            "## メタデータ",
            "",
            "## 原文",
            "",
            "## 分類",
            "",
            f"- **document_type:** `{document_type}`",
            "- **topics:**",
            "- **review_status:** `unreviewed`",
            "",
            "## 要点",
            "",
            "## 本研究との関連",
            "",
            "## 引用方針",
            "",
            "## メモ",
            "",
        ]
    )


def write_literature_note(
    *,
    vault_root: Path,
    key: str,
    meta: BibMeta | None,
    document_type: str,
    pdf_written: bool,
    source_md_written: bool,
) -> Path:
    note_path = vault_root / REFERENCE_ROOT / "papers" / f"{key}.md"
    title = meta.title if meta and meta.title else key
    if note_path.is_file():
        text = note_path.read_text(encoding="utf-8")
    else:
        note_path.parent.mkdir(parents=True, exist_ok=True)
        text = _default_note(key, title, document_type)

    pdf_rel = Path("../pdf") / f"{key}.pdf" if pdf_written else None
    source_md_rel = Path("../source_md") / f"{key}.md" if source_md_written else None
    text = replace_or_insert_section(text, "メタデータ", _metadata_body(key, meta))
    text = replace_or_insert_section(
        text,
        "原文",
        _source_body(pdf_rel=pdf_rel, source_md_rel=source_md_rel, document_type=document_type),
    )
    note_path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return note_path


def write_source_markdown(
    *,
    key: str,
    vault_root: Path,
    source_md: Path | None,
    pdf_path: Path | None,
    overwrite: bool,
) -> bool:
    if source_md is None and pdf_path is None:
        return False
    dst = vault_root / REFERENCE_ROOT / "source_md" / f"{key}.md"
    if dst.exists() and not overwrite:
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    if source_md is not None:
        text = source_md.read_text(encoding="utf-8")
    else:
        assert pdf_path is not None
        text = pdf_to_markdown(pdf_path)
    dst.write_text(text.rstrip() + "\n", encoding="utf-8")
    return True


def write_project_note(vault_root: Path, project: str, key: str, title: str) -> Path:
    project_root = vault_root / "projects" / project
    notes_dir = project_root / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_path = notes_dir / f"{key}.md"
    if not note_path.exists():
        note_path.write_text(
            "\n".join(
                [
                    f"# {title or key}",
                    "",
                    f"- **central:** [[references/papers/{key}|{key}]]",
                    f"- **pandoc:** `[@{key}]`",
                    "- **citation_intent:**",
                    "- **project_relevance:**",
                    "",
                    "## 原稿用メモ",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    keys_path = project_root / "reference_keys.txt"
    existing: list[str] = []
    if keys_path.is_file():
        existing = [
            line.strip().split("#", 1)[0].strip()
            for line in keys_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    if key not in existing:
        keys_path.write_text(
            "# pandoc-id list for this vault project\n\n"
            + "\n".join([*existing, key])
            + "\n",
            encoding="utf-8",
        )
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-dir", type=Path, required=True, help="Markdown vault root")
    parser.add_argument("--key", required=True, help="Paperpile pandoc-id / BibTeX key")
    parser.add_argument("--paperpile-bib", type=Path, default=None)
    parser.add_argument("--pdf", type=Path, default=None, help="PDF to copy and optionally convert")
    parser.add_argument(
        "--source-md",
        type=Path,
        default=None,
        help="Existing Markdown conversion of the source PDF/document",
    )
    parser.add_argument(
        "--document-type",
        default="unknown",
        help="Free label such as original_article, guideline, review, report, other",
    )
    parser.add_argument("--project", default=None, help="Optional vault project name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite copied/generated files")
    args = parser.parse_args()

    vault_root = args.vault_dir.expanduser().resolve()
    key = args.key.strip()
    if not key:
        raise ValueError("--key is required")

    meta = load_bib(key, bib_path=args.paperpile_bib)
    pdf_written = False
    if args.pdf is not None:
        pdf_path = args.pdf.expanduser().resolve()
        if not pdf_path.is_file():
            raise FileNotFoundError(pdf_path)
        pdf_written = _copy_file(
            pdf_path,
            vault_root / REFERENCE_ROOT / "pdf" / f"{key}.pdf",
            overwrite=args.overwrite,
        ) or (vault_root / REFERENCE_ROOT / "pdf" / f"{key}.pdf").is_file()
    else:
        pdf_path = None

    if args.source_md is not None:
        source_md = args.source_md.expanduser().resolve()
        if not source_md.is_file():
            raise FileNotFoundError(source_md)
    else:
        source_md = None

    source_md_written = write_source_markdown(
        key=key,
        vault_root=vault_root,
        source_md=source_md,
        pdf_path=pdf_path,
        overwrite=args.overwrite,
    )
    note_path = write_literature_note(
        vault_root=vault_root,
        key=key,
        meta=meta,
        document_type=args.document_type,
        pdf_written=pdf_written,
        source_md_written=source_md_written,
    )
    print(f"Wrote {note_path}")

    if args.project:
        project_note = write_project_note(
            vault_root,
            args.project,
            key,
            meta.title if meta and meta.title else key,
        )
        print(f"Wrote {project_note}")


if __name__ == "__main__":
    main()

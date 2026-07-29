"""BibTeX extract/parse helpers for paper reference/ notes.

Used by ingest_reference.py (manuscript-reference skill).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PAPERPILE = Path(os.environ.get("PAPERPILE_BIB", "")).expanduser() if os.environ.get("PAPERPILE_BIB") else None
FALLBACK_PAPERPILE_PATHS: tuple[Path, ...] = (
    Path.home() / "paperpile.bib",
    Path.home() / "My Drive/paperpile.bib",
    Path.home() / "Google Drive/My Drive/paperpile.bib",
)


def resolve_paperpile() -> Path:
    env = os.environ.get("PAPERPILE_BIB")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser()
    candidates: list[Path] = []
    if DEFAULT_PAPERPILE is not None:
        candidates.append(DEFAULT_PAPERPILE)
    candidates.extend(FALLBACK_PAPERPILE_PATHS)
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError("paperpile.bib not found (set PAPERPILE_BIB)")


def extract_entry(bib_path: Path, key: str) -> str | None:
    """エントリ先頭から次の @ まで取得。"""
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"@\w+\{{{re.escape(key)},", text)
    if not m:
        return None
    rest = text[m.start() :]
    nxt = re.search(r"\n@", rest[1:])
    return rest[: nxt.start() + 1] if nxt else rest


@dataclass
class BibMeta:
    key: str
    title: str
    authors: list[str]
    journal: str
    year: str
    volume: str
    number: str
    pages: str
    doi: str
    pmid: str
    url: str
    abstract: str
    raw: str


def _field(block: str, name: str) -> str:
    m = re.search(rf"^\s*{name}\s*=", block, re.I | re.M)
    if not m:
        return ""
    rest = block[m.end() :].lstrip()
    if rest.startswith('"'):
        end = 1
        while end < len(rest):
            if rest[end] == '"' and rest[end - 1] != "\\":
                val = rest[1:end]
                return re.sub(r"\s+", " ", val.replace("\n", " ").strip())
            end += 1
        return ""
    if rest.startswith("{"):
        depth = 0
        for i, ch in enumerate(rest):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    inner = rest[1:i]
                    inner = re.sub(r"^\{+|\}+$", "", inner.strip())
                    return re.sub(r"\s+", " ", inner.replace("\n", " ").strip())
        return ""
    m_num = re.match(r"(\d+)", rest)
    if m_num:
        return m_num.group(1)
    return ""


def _strip_braces(s: str) -> str:
    s = s.strip()
    if s.startswith("{{") and s.endswith("}}"):
        return s[2:-2]
    if s.startswith("{") and s.endswith("}"):
        return s[1:-1]
    return s


def _year_from_date(date: str, year_field: str) -> str:
    if year_field:
        return year_field
    m = re.match(r"(\d{4})", date)
    return m.group(1) if m else ""


def parse_entry(block: str, key: str) -> BibMeta:
    title = _strip_braces(_field(block, "title"))
    author_raw = _field(block, "author")
    authors = [a.strip() for a in re.split(r"\s+and\s+", author_raw) if a.strip()]
    journal = _field(block, "journaltitle") or _field(block, "journal")
    date = _field(block, "date")
    year = _year_from_date(date, _field(block, "year"))
    issue = _field(block, "issue") or _field(block, "number")
    return BibMeta(
        key=key,
        title=title,
        authors=authors,
        journal=journal,
        year=year,
        volume=_field(block, "volume"),
        number=issue,
        pages=_field(block, "pages"),
        doi=_field(block, "doi"),
        pmid=_field(block, "pmid"),
        url=_field(block, "url"),
        abstract=_field(block, "abstract"),
        raw=block,
    )


def load_bib(
    key: str | None,
    *,
    bib_path: Path | None = None,
    fallback_bib: Path | None = None,
) -> BibMeta | None:
    if not key:
        return None
    candidates: list[Path] = []
    if bib_path is not None:
        candidates.append(bib_path)
    if fallback_bib is not None:
        candidates.append(fallback_bib)
    for path in candidates:
        if not path.is_file():
            continue
        block = extract_entry(path, key)
        if block:
            return parse_entry(block, key)
    bib_path_pp = resolve_paperpile()
    block = extract_entry(bib_path_pp, key)
    if block:
        return parse_entry(block, key)
    return None


def journal_citation(meta: BibMeta) -> str:
    bits: list[str] = []
    if meta.journal:
        bits.append(meta.journal)
    if meta.year:
        bits.append(meta.year)
    vol = meta.volume
    if vol and meta.number:
        bits.append(f"{vol}({meta.number})")
    elif vol:
        bits.append(str(vol))
    if meta.pages:
        bits.append(meta.pages.replace("--", "-"))
    return ". ".join(bits) if bits else "—"


def link_or_dash(label: str, value: str, url: str) -> str:
    if not value or value == "—":
        return f"- **{label}:** —"
    return f"- **{label}:** [{value}]({url})"


def format_metadata_block(
    key: str,
    meta: BibMeta | None,
    *,
    pdf_rel: str,
    pdf_exists: bool,
    pmid_override: str | None = None,
) -> str:
    """## メタデータ 節の本文（見出し行は含めない）。"""
    doi = meta.doi if meta else ""
    pmid = (meta.pmid if meta else "") or pmid_override or ""
    url = meta.url if meta else ""
    if not url and doi:
        url = f"https://doi.org/{doi}"

    if pdf_exists:
        pdf_line = f"- **PDF:** [{pdf_rel.split('/')[-1]}]({pdf_rel})"
    else:
        pdf_line = "- **PDF:** —（未取得）"

    lines = [
        "<!-- auto: ingest_reference.py（reference.bib）— この節は手編集しない -->",
        "",
        f"- **pandoc-id:** `{key}`（原稿: `[@{key}]`）",
        pdf_line,
    ]
    if doi:
        lines.append(link_or_dash("DOI", doi, f"https://doi.org/{doi}"))
    else:
        lines.append("- **DOI:** —")
    if pmid and pmid != "—":
        lines.append(
            link_or_dash("PubMed", pmid, f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
        )
    else:
        lines.append("- **PubMed:** —")
    if url:
        display = url.replace("https://", "").replace("http://", "")
        if len(display) > 60:
            display = display[:57] + "…"
        lines.append(link_or_dash("URL", display, url))
    else:
        lines.append("- **URL:** —")

    cite = journal_citation(meta) if meta else "—"
    lines.append(f"- **誌・巻号:** {cite}")
    return "\n".join(lines)


def replace_metadata_section(md_text: str, meta_body: str) -> str:
    """## メタデータ を差し替え。無ければタイトル直後に挿入。"""
    section = f"## メタデータ\n\n{meta_body}\n\n"
    pattern = re.compile(r"^## メタデータ\n.*?(?=^## )", re.M | re.S)
    if pattern.search(md_text):
        return pattern.sub(section, md_text, count=1)
    title_pat = re.compile(r"^(# .+\n)\n?", re.M)
    m = title_pat.match(md_text)
    if m:
        pos = m.end()
        return md_text[:pos] + "\n" + section + "\n" + md_text[pos:]
    return section + "\n" + md_text


def update_title_line(md_text: str, title: str) -> str:
    if not title:
        return md_text
    clean = _strip_braces(title)
    return re.sub(r"^# .+$", f"# {clean}", md_text, count=1, flags=re.M)

#!/usr/bin/env python3
"""Bootstrap reference/md + reference/pdf from Paperpile keys.

Creates note stubs from ``_template.md`` (or skill template) and copies matching
PDFs from Paperpile folders.

Key sources (combine as needed):
  --keys A,B,C
  --keys-file path.txt
  --tag duodenal_emr   # keyword/keyword field contains this tag
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import unicodedata
from pathlib import Path

from manuscript_md.bib_parse import load_bib
from manuscript_md.paperpile import resolve_paperpile

# skills/manuscript_md/templates/reference_note_template.md
SKILL_NOTE_TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "manuscript_md"
    / "templates"
    / "reference_note_template.md"
)

DEFAULT_PAPERPILE_ROOTS = [
    Path.home() / "My Drive/Paperpile/Papers",
    Path.home() / "Google Drive/My Drive/Paperpile/Papers",
    Path("/Users/mizuy/My Drive/Paperpile/Papers"),
]


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def discover_keys_by_tag(bib_path: Path, tag: str) -> list[str]:
    """Return pandoc-ids whose BibTeX block mentions ``tag`` (e.g. duodenal_emr)."""
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    needle = tag.replace("_", "\\_")
    keys: list[str] = []
    for block in re.split(r"\n(?=@)", text):
        if tag not in block and needle not in block:
            continue
        m = re.match(r"@\w+\{([^,\s]+)", block)
        if m:
            keys.append(m.group(1))
    return sorted(set(keys))


def read_keys_file(path: Path) -> list[str]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        key = line.strip().split("#", 1)[0].strip()
        if key:
            keys.append(key)
    return keys


def paperpile_roots(extra_dirs: list[Path] | None = None) -> list[Path]:
    roots: list[Path] = []
    env = os.environ.get("PAPERPILE_PDF_ROOTS", "")
    if env:
        roots.extend(Path(p).expanduser() for p in env.split(os.pathsep) if p.strip())
    roots.extend(DEFAULT_PAPERPILE_ROOTS)
    if extra_dirs:
        roots.extend(extra_dirs)
    seen: set[Path] = set()
    out: list[Path] = []
    for r in roots:
        try:
            rp = r.resolve()
        except OSError:
            continue
        if rp in seen or not rp.is_dir():
            continue
        seen.add(rp)
        out.append(rp)
    return out


def list_pdfs(roots: list[Path], *, recursive: bool = False) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for root in roots:
        paths = root.rglob("*.pdf") if recursive else root.glob("*.pdf")
        # also one-level children folders when not full recursive scan of all
        if not recursive:
            paths = list(root.glob("*.pdf"))
            for sub in root.iterdir() if root.is_dir() else []:
                if sub.is_dir():
                    paths.extend(sub.glob("*.pdf"))
        for p in sorted(paths):
            try:
                rp = p.resolve()
            except OSError:
                continue
            if rp not in seen:
                seen.add(rp)
                out.append(rp)
    return out


def author_surname(author: str) -> str:
    author = author.strip()
    if author.lower().startswith(("phd,", "md,")):
        rest = author.split(",", 1)[1].strip() if "," in author else author
        parts = rest.split()
        return parts[-1] if parts else rest
    if "," in author:
        return author.split(",", 1)[0].strip()
    parts = author.split()
    return parts[-1] if parts else author


def title_tokens(title: str) -> set[str]:
    stop = {
        "a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "vs",
        "versus", "after", "non", "clinical", "outcomes", "following", "treatment",
    }
    return {w for w in normalize(title).split() if len(w) > 3 and w not in stop}


def find_pdf_recursive(meta, roots: list[Path]) -> Path | None:
    if not meta or not meta.authors:
        return None
    surname = normalize(author_surname(meta.authors[0]))
    year = meta.year or ""
    tokens = title_tokens(meta.title)
    best: tuple[int, Path] | None = None
    for root in roots:
        for pdf in root.rglob("*.pdf"):
            stem = normalize(pdf.stem)
            if year and year not in stem:
                continue
            if surname not in stem:
                continue
            overlap = sum(1 for t in tokens if t in stem)
            score = overlap * 10 + len(stem) // 1000
            if overlap == 0:
                score = 1
            if best is None or score > best[0]:
                best = (score, pdf)
    return best[1] if best else None


def match_pdf(meta, pdfs: list[Path], roots: list[Path]) -> Path | None:
    if not meta or not meta.authors:
        return None
    surname = normalize(author_surname(meta.authors[0]))
    year = meta.year
    tokens = title_tokens(meta.title)
    best: tuple[int, Path] | None = None
    for pdf in pdfs:
        stem = normalize(pdf.stem)
        if year and year not in stem:
            continue
        if surname not in stem:
            continue
        overlap = sum(1 for t in tokens if t in stem)
        score = overlap * 10
        if overlap == 0:
            score = 1
        if best is None or score > best[0]:
            best = (score, pdf)
    if best:
        return best[1]
    return find_pdf_recursive(meta, roots)


def format_authors_table(meta) -> str:
    if not meta or not meta.authors:
        return "| — | — | — |"
    rows = []
    for author in meta.authors[:3]:
        family = author_surname(author)
        given = author.split(",", 1)[1].strip() if "," in author else ""
        name = f"{family} {given}".strip()
        rows.append(f"| {name} | —（PDF から転記） | — |")
    if len(meta.authors) > 3:
        rows.append(f"| … 他 {len(meta.authors) - 3} 名 | — | — |")
    return "\n".join(rows)


def resolve_template(ref_root: Path) -> Path:
    local = ref_root / "_template.md"
    if local.is_file():
        return local
    if SKILL_NOTE_TEMPLATE.is_file():
        return SKILL_NOTE_TEMPLATE
    raise FileNotFoundError(
        f"No note template: expected {local} or {SKILL_NOTE_TEMPLATE}"
    )


def create_md(key: str, meta, *, md_dir: Path, template_path: Path) -> bool:
    md_path = md_dir / f"{key}.md"
    if md_path.exists():
        return False
    template = template_path.read_text(encoding="utf-8")
    title = meta.title if meta and meta.title else key
    abstract = meta.abstract if meta and meta.abstract else ""
    if abstract:
        abstract_block = (
            "<!-- auto: ingest_reference.py（reference.bib の abstract 全文をそのまま）— 要約・編集しない -->\n\n"
            f"> {abstract}"
        )
    else:
        abstract_block = "（paperpile.bib / reference.bib に `abstract` が無い）"
    authors = format_authors_table(meta)

    body = template
    body = re.sub(r"^# \{English title\}", f"# {title}", body, count=1, flags=re.M)
    body = body.replace("{BibTeXKey}", key)
    body = body.replace("{English title}", title)
    body = re.sub(
        r"## Abstract（English）\n\n.*?(?=^## Abstract（日本語訳）)",
        f"## Abstract（English）\n\n{abstract_block}\n\n",
        body,
        count=1,
        flags=re.S | re.M,
    )
    body = body.replace(
        "{bib の著者を列挙。所属の詳細は下表で PDF から転記}\n\n",
        "",
    )
    body = body.replace("## 著者\n\n", "## 著者・所属\n\n")
    body = re.sub(
        r"\| \{Family Given\} \| \{Institution, Country\} \| \{レジストリ・学会・共著グループ\} \|"
        r"(?:\n\| \{Family Given\} \| \{Institution, Country\} \| \{レジストリ・学会・共著グループ\} \|)*",
        authors,
        body,
        count=1,
    )
    md_path.write_text(body, encoding="utf-8")
    return True


def bootstrap_keys(
    keys: list[str],
    *,
    ref_root: Path,
    bib_path: Path | None = None,
    pdf_dirs: list[Path] | None = None,
) -> tuple[int, int, list[str]]:
    bib_path = bib_path or resolve_paperpile()
    roots = paperpile_roots(pdf_dirs)
    pdfs = list_pdfs(roots)
    md_dir = ref_root / "md"
    pdf_dir = ref_root / "pdf"
    md_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    template_path = resolve_template(ref_root)

    created_md = 0
    copied = 0
    missing_pdf: list[str] = []

    for key in keys:
        meta = load_bib(key, bib_path=bib_path)
        if not meta:
            print(f"  WARN: key not in paperpile.bib: {key}")
            continue
        if create_md(key, meta, md_dir=md_dir, template_path=template_path):
            created_md += 1

        dest = pdf_dir / f"{key}.pdf"
        if dest.exists():
            copied += 1
            continue
        src = match_pdf(meta, pdfs, roots)
        if src and src.is_file():
            shutil.copy2(src, dest)
            copied += 1
        else:
            missing_pdf.append(key)

    return created_md, copied, missing_pdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref-dir", type=Path, required=True, help="/path/to/paper/reference/")
    parser.add_argument("--keys", help="Comma-separated pandoc-id list")
    parser.add_argument("--keys-file", type=Path, help="One pandoc-id per line")
    parser.add_argument(
        "--tag",
        help="Include keys whose BibTeX block contains this Paperpile tag/keyword",
    )
    parser.add_argument(
        "--pdf-dir",
        action="append",
        type=Path,
        default=[],
        help="Extra Paperpile PDF search root (repeatable); also PAPERPILE_PDF_ROOTS",
    )
    args = parser.parse_args()

    ref_root = args.ref_dir.resolve()
    bib_path = resolve_paperpile()
    keys: list[str] = []
    if args.keys:
        keys.extend(k.strip() for k in args.keys.split(",") if k.strip())
    if args.keys_file:
        keys.extend(read_keys_file(args.keys_file.expanduser()))
    if args.tag:
        keys.extend(discover_keys_by_tag(bib_path, args.tag))
    keys = sorted(set(keys))
    if not keys:
        raise SystemExit("No keys: pass --keys, --keys-file, and/or --tag")

    created_md, copied, missing_pdf = bootstrap_keys(
        keys,
        ref_root=ref_root,
        bib_path=bib_path,
        pdf_dirs=list(args.pdf_dir),
    )
    print(f"Keys: {len(keys)}")
    print(f"Created md: {created_md}")
    print(f"PDF copied/existing: {copied}")
    if missing_pdf:
        print(f"PDF not found ({len(missing_pdf)}):")
        for k in missing_pdf:
            meta = load_bib(k, bib_path=bib_path)
            title = (
                (meta.title[:60] + "…")
                if meta and len(meta.title) > 60
                else (meta.title if meta else k)
            )
            print(f"  - {k}: {title}")


if __name__ == "__main__":
    main()

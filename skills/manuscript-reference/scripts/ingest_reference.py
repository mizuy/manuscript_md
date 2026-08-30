#!/usr/bin/env python3
"""Reference ingest: reference.bib, md metadata sync, README ## 一覧.

See docs/REFERENCE_INGEST.md. Lives in manuscript-reference skill.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from manuscript_md.bib_parse import (
    format_abstract_english_block,
    format_metadata_block,
    load_bib,
    replace_abstract_english_section,
    replace_metadata_section,
    update_title_line,
)
from manuscript_md.bibliography import build_references_bib


def discover_keys(ref_root: Path) -> list[str]:
    """Keep reference_keys.txt order; append new md stems at end."""
    md_dir = ref_root / "md"
    keys_file = ref_root / "reference_keys.txt"
    from_md = {p.stem for p in md_dir.glob("*.md")} if md_dir.is_dir() else set()
    ordered: list[str] = []
    seen: set[str] = set()
    if keys_file.is_file():
        for line in keys_file.read_text(encoding="utf-8").splitlines():
            key = line.strip().split("#", 1)[0].strip()
            if key and key in from_md and key not in seen:
                ordered.append(key)
                seen.add(key)
    for k in sorted(from_md - seen):
        ordered.append(k)
    return ordered


def write_reference_keys(ref_root: Path, keys: list[str]) -> None:
    keys_file = ref_root / "reference_keys.txt"
    lines = ["# pandoc-id list for reference/ ingest", ""]
    lines.extend(keys)
    keys_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_reference_bib(ref_root: Path, keys: list[str]) -> Path:
    keys_file = ref_root / "reference_keys.txt"
    out = ref_root / "reference.bib"
    # paper_dir = parent so manual_entries.bib lives once at paper root
    # (do not symlink into reference/)
    build_references_bib(ref_root.parent, keys_file=keys_file, out_path=out)
    return out


def sync_md_metadata(key: str, *, ref_root: Path, ref_bib: Path) -> str | None:
    md_dir = ref_root / "md"
    pdf_dir = ref_root / "pdf"
    md_path = md_dir / f"{key}.md"
    if not md_path.is_file():
        return None

    meta = load_bib(key, bib_path=ref_bib)
    md_text = md_path.read_text(encoding="utf-8")
    pmid = (meta.pmid if meta else "") or None

    pdf_rel = f"../pdf/{key}.pdf"
    pdf_exists = (pdf_dir / f"{key}.pdf").is_file()
    body = format_metadata_block(
        key,
        meta,
        pdf_rel=pdf_rel,
        pdf_exists=pdf_exists,
        pmid_override=pmid,
    )
    new_text = replace_metadata_section(md_text, body)
    new_text = replace_abstract_english_section(
        new_text, format_abstract_english_block(meta)
    )
    if meta and meta.title:
        new_text = update_title_line(new_text, meta.title)

    md_path.write_text(new_text, encoding="utf-8")
    if meta and meta.title:
        return meta.title
    for line in new_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return key


def _listing_block(keys: list[str], titles: dict[str, str]) -> str:
    lines = ["## 一覧", ""]
    for key in keys:
        title = titles.get(key, key)
        short = title[:70] + ("…" if len(title) > 70 else "")
        lines.append(f"- [{key}](./md/{key}.md) — {short}")
    return "\n".join(lines) + "\n"


def rebuild_readme(ref_root: Path, keys: list[str], titles: dict[str, str]) -> None:
    """Rewrite only ``## 一覧``; preserve hand-edited preamble above it."""
    path = ref_root / "README.md"
    listing = _listing_block(keys, titles)
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        if re.search(r"^## 一覧\b", text, re.M):
            text = re.sub(
                r"^## 一覧\n.*\Z",
                listing,
                text,
                count=1,
                flags=re.M | re.S,
            )
        else:
            text = text.rstrip() + "\n\n" + listing
        path.write_text(text, encoding="utf-8")
        return

    default = "\n".join(
        [
            "# Reference summaries",
            "",
            "1 論文 = `md/{pandoc-id}.md` + `pdf/{pandoc-id}.pdf` + `reference.bib`。",
            "",
            "**ingest:** `uv run manuscript-md ingest-reference --ref-dir reference/`",
            "",
            "原稿の引用順は `manuscript.md` の `[@key]` と pandoc が決める（番号はメモに付けない）。",
            "",
            listing.rstrip(),
            "",
        ]
    )
    path.write_text(default, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref-dir",
        type=Path,
        required=True,
        help="/path/to/paper/reference/",
    )
    parser.add_argument("--skip-bib", action="store_true", help="Do not regenerate reference.bib")
    parser.add_argument("--keys-only", action="store_true")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="Sync md metadata from existing reference.bib only",
    )
    args = parser.parse_args()

    ref_root = args.ref_dir.resolve()
    md_dir = ref_root / "md"
    pdf_dir = ref_root / "pdf"
    ref_bib = ref_root / "reference.bib"

    md_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    keys = discover_keys(ref_root)
    write_reference_keys(ref_root, keys)
    print(f"Wrote {(ref_root / 'reference_keys.txt').name} ({len(keys)} keys)")

    if args.keys_only:
        return

    if not args.skip_bib and not args.metadata_only:
        build_reference_bib(ref_root, keys)
        print(f"Wrote {ref_bib.name}")
    elif not ref_bib.is_file():
        raise FileNotFoundError(f"{ref_bib} missing; run without --skip-bib")

    titles: dict[str, str] = {}
    updated = 0
    for key in keys:
        title = sync_md_metadata(key, ref_root=ref_root, ref_bib=ref_bib)
        if title is None:
            continue
        titles[key] = title
        updated += 1
        meta = load_bib(key, bib_path=ref_bib)
        pmid = meta.pmid if meta else ""
        print(f"  {key}: metadata synced (PMID {pmid or '—'})")

    rebuild_readme(ref_root, keys, titles)
    print(f"Synced metadata in {updated} md files; wrote README.md ## 一覧")


if __name__ == "__main__":
    main()

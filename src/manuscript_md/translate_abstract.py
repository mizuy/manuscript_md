#!/usr/bin/env python3
"""Translate Abstract（English） → Abstract（日本語訳） in reference/md notes.

Requires optional dependency: ``uv add deep-translator`` or
``pip install deep-translator``.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from manuscript_md.bib_parse import (
    extract_abstract_english,
    format_abstract_ja_block,
    replace_abstract_ja_section,
)

CHUNK_SIZE = 4500


def needs_update(md_text: str) -> bool:
    en = extract_abstract_english(md_text)
    if not en:
        return False
    m_ja = re.search(
        r"^## Abstract（日本語訳）\n\n(.+?)\n\n^## ",
        md_text,
        re.S | re.M,
    )
    if not m_ja:
        return True
    ja = m_ja.group(1).strip()
    if ja.startswith("<!-- Abstract（English）の全文翻訳"):
        body = ja.split("\n\n", 1)[-1] if "\n\n" in ja else ja
        return len(body) / max(len(en), 1) < 0.55
    if ja.startswith("{") or "全文翻訳" in ja:
        return True
    return len(ja) / max(len(en), 1) < 0.55 or len(ja) < 120


def _translate_chunk(text: str) -> str:
    try:
        from deep_translator import GoogleTranslator
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "deep-translator is required for Abstract JA translation.\n"
            "  uv add deep-translator   # or: pip install deep-translator"
        ) from exc
    return GoogleTranslator(source="en", target="ja").translate(text)


def translate_full(text: str) -> str:
    text = text.replace("\\%", "%")
    if len(text) <= CHUNK_SIZE:
        return _translate_chunk(text)
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        if end < len(text):
            split = text.rfind(". ", start, end)
            if split > start + 500:
                end = split + 1
        parts.append(_translate_chunk(text[start:end].strip()))
        start = end
        time.sleep(0.3)
    return " ".join(parts)


def sync_file(path: Path, *, dry_run: bool = False, force: bool = False) -> str:
    md_text = path.read_text(encoding="utf-8")
    if not force and not needs_update(md_text):
        return "skip"
    en = extract_abstract_english(md_text)
    if not en:
        return "no_en"
    ja = translate_full(en)
    new_text = replace_abstract_ja_section(md_text, format_abstract_ja_block(ja))
    if dry_run:
        return f"would_update ({len(en)} -> {len(ja)} chars)"
    path.write_text(new_text, encoding="utf-8")
    return f"updated ({len(en)} -> {len(ja)} chars)"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref-dir",
        type=Path,
        required=True,
        help="/path/to/paper/reference/",
    )
    parser.add_argument("--keys", help="comma-separated pandoc-id list")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="retranslate even if full JA exists")
    args = parser.parse_args(argv)

    md_dir = args.ref_dir.resolve() / "md"
    if args.keys:
        paths = [md_dir / f"{k.strip()}.md" for k in args.keys.split(",") if k.strip()]
    else:
        paths = sorted(md_dir.glob("*.md")) if md_dir.is_dir() else []

    for path in paths:
        if not path.is_file():
            print(f"  {path.stem}: missing")
            continue
        status = "error"
        try:
            status = sync_file(path, dry_run=args.dry_run, force=args.force)
            print(f"  {path.stem}: {status}")
        except SystemExit:
            raise
        except Exception as exc:  # noqa: BLE001
            print(f"  {path.stem}: ERROR {exc}")
        if not args.dry_run and status.startswith("updated"):
            time.sleep(0.5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

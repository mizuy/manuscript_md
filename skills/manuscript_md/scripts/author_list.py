#!/usr/bin/env python3
"""Build a remapped author / affiliation list as Markdown.

Input files use the journal-style block:

    Jane Doe,1 John Smith,1,2

    1. Department A
    2. Department B

Multiple sources are merged (affiliation lists unioned). ``--order`` lists
display names one per line. Affiliation numbers are reassigned in that order
and wrapped in ``<sub>…</sub>``.

Usage:
    python author_list.py affiliations.txt --order authors.txt -o author_list.md
    python author_list.py a.txt b.txt --order authors.txt
    uv run lab-paper author-list affiliations.txt --order authors.txt -o author_list.md
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path


def parse_author_affiliations(text: str) -> dict[str, list[str]]:
    """Map each author name to affiliation strings from a numbered block."""
    lines = unicodedata.normalize("NFKC", text).strip().split("\n")
    if not lines:
        return {}

    author_line = lines[0].strip()
    affiliation_dict: dict[int, str] = {}
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(\d+)\.\s*(.+)$", line)
        if match:
            affiliation_dict[int(match.group(1))] = match.group(2).strip()

    pattern = r"[^,]+,\s*\d[,\-\d\s]*"
    author_affiliation_dict: dict[str, list[str]] = {}
    for match in re.finditer(pattern, author_line):
        matched_text = match.group(0)
        parts = matched_text.split(",", 1)
        if len(parts) != 2:
            continue
        author_name = " ".join(parts[0].split())
        numbers = [int(n) for n in re.findall(r"\d+", parts[1])]
        if not author_name:
            continue
        bucket = author_affiliation_dict.setdefault(author_name, [])
        for num in numbers:
            affiliation = affiliation_dict.get(num)
            if affiliation and affiliation not in bucket:
                bucket.append(affiliation)
    return author_affiliation_dict


def merge_author_affiliations(*dicts: dict[str, list[str]]) -> dict[str, list[str]]:
    """Union affiliation lists; first occurrence of each string wins."""
    out: dict[str, list[str]] = {}
    for mapping in dicts:
        for name, affiliations in mapping.items():
            bucket = out.setdefault(name, [])
            for affiliation in affiliations:
                if affiliation not in bucket:
                    bucket.append(affiliation)
    return out


def author_order_from_dicts(*dicts: dict[str, list[str]]) -> list[str]:
    seen: list[str] = []
    for mapping in dicts:
        for name in mapping:
            if name not in seen:
                seen.append(name)
    return seen


def read_order_file(path: Path) -> list[str]:
    names: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        name = " ".join(unicodedata.normalize("NFKC", raw).split())
        if name and not name.startswith("#"):
            names.append(name)
    return names


def get_author_affiliation_text(
    author_names: list[str],
    author_affiliation_dict: dict[str, list[str]],
) -> str:
    """Format authors with remapped <sub>n</sub> and a numbered affiliation list."""
    ordered_affiliations: list[str] = []
    seen: set[str] = set()
    for author_name in author_names:
        for affiliation in author_affiliation_dict.get(author_name, []):
            if affiliation not in seen:
                ordered_affiliations.append(affiliation)
                seen.add(affiliation)

    affiliation_to_number = {
        affiliation: num for num, affiliation in enumerate(ordered_affiliations, start=1)
    }

    new_author_list: list[str] = []
    for author_name in author_names:
        affiliations = author_affiliation_dict.get(author_name, [])
        numbers = sorted(
            {
                affiliation_to_number[affiliation]
                for affiliation in affiliations
                if affiliation in affiliation_to_number
            }
        )
        if numbers:
            new_author_list.append(f"{author_name},<sub>{','.join(map(str, numbers))}</sub>")
        else:
            new_author_list.append(author_name)

    affiliation_lines = [
        f"<sub>{num}</sub> {affiliation}"
        for num, affiliation in enumerate(ordered_affiliations, start=1)
    ]
    return f"{' '.join(new_author_list)}\n\n" + "\n".join(affiliation_lines)


def build_text(sources: list[str], author_names: list[str] | None = None) -> str:
    parsed = [parse_author_affiliations(src) for src in sources]
    merged = merge_author_affiliations(*parsed)
    names = author_names if author_names is not None else author_order_from_dicts(*parsed)
    return get_author_affiliation_text(names, merged)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Merge numbered author/affiliation blocks and write Markdown "
            "with <sub> affiliation marks. "
            "CRediT contribution statements are a different skill (credit-author-statement)."
        )
    )
    parser.add_argument(
        "sources",
        nargs="+",
        type=Path,
        help="Affiliation block files (author line, then 'N. Department …')",
    )
    parser.add_argument(
        "--order",
        type=Path,
        help="Author display order (one name per line). Default: first appearance",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write Markdown (.md). Default: print to stdout",
    )
    args = parser.parse_args(argv)

    texts: list[str] = []
    for path in args.sources:
        if not path.is_file():
            print(f"error: source not found: {path}", file=sys.stderr)
            return 2
        texts.append(path.read_text(encoding="utf-8"))

    names = read_order_file(args.order) if args.order else None
    if args.order is not None and not names:
        print(f"error: no author names in {args.order}", file=sys.stderr)
        return 2

    formatted = build_text(texts, names)
    if args.output is None:
        print(formatted)
        return 0

    dest = args.output
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(formatted + "\n", encoding="utf-8")
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MANUSCRIPT_NAME = "manuscript.md"

# H1 sections included in "main text" (Introduction through Discussion).
BODY_SECTIONS = ("Introduction", "Methods", "Results", "Discussion")

# Lines / blocks excluded from word counts.
SKIP_LINE_PREFIXES = (
    "![](",  # figure/image lines
    "| ",  # markdown table rows
    "|---",
)
SKIP_LINE_EXACT = frozenset({":::", "::: pagebreak", "::: landscape"})


def read_manuscript(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    return text


def split_h1_sections(text: str) -> dict[str, str]:
    """Split manuscript into H1 sections (heading text -> body)."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for line in text.splitlines():
        if line.startswith("# ") and not line.startswith("##"):
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = line[2:].strip()
            buf = []
        elif current is not None:
            buf.append(line)

    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def get_section(sections: dict[str, str], name: str) -> str:
    """Look up an H1 body by name, case-insensitive (# ABSTRACT == Abstract)."""
    if name in sections:
        return sections[name]
    by_casefold = {key.casefold(): value for key, value in sections.items()}
    return by_casefold.get(name.casefold(), "")


def strip_non_prose_lines(text: str) -> str:
    kept: list[str] = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in SKIP_LINE_EXACT or stripped.startswith(":::"):
            continue
        if any(stripped.startswith(p) for p in SKIP_LINE_PREFIXES):
            in_table = stripped.startswith("| ")
            continue
        if in_table and stripped.startswith("|"):
            continue
        in_table = False
        if stripped.startswith("**Figure ") or stripped.startswith("**Table "):
            continue
        kept.append(line)
    return "\n".join(kept)


def clean_for_word_count(text: str) -> str:
    text = strip_non_prose_lines(text)
    # Pandoc citations: [@Key2024-ab] or [@A; @B]
    text = re.sub(r"\[(@[^\]]+)\]", " ", text)
    # HTML / pandoc spans
    text = re.sub(r"<[^>]+>", " ", text)
    # Markdown links/images: [label](url) or ![alt](url)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[[^\]]*\]\([^)]*\)", " ", text)
    # Bold/italic markers
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)
    text = re.sub(r"[*_]+", " ", text)
    # Backtick code
    text = re.sub(r"`[^`]*`", " ", text)
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_words(text: str) -> int:
    cleaned = clean_for_word_count(text)
    if not cleaned:
        return 0
    tokens = re.findall(r"\b[\w'-]+\b", cleaned, flags=re.UNICODE)
    return len(tokens)


def abstract_without_keywords(abstract: str) -> str:
    lines = abstract.splitlines()
    out: list[str] = []
    for line in lines:
        if re.match(r"^\*\*Key words:\*\*", line, flags=re.IGNORECASE):
            break
        out.append(line)
    return "\n".join(out).strip()


def count_manuscript(path: Path) -> dict[str, int | dict[str, int]]:
    sections = split_h1_sections(read_manuscript(path))

    abstract_raw = get_section(sections, "Abstract")
    abstract_no_kw = abstract_without_keywords(abstract_raw)

    body_parts: list[str] = []
    by_section: dict[str, int] = {}
    for name in BODY_SECTIONS:
        body = get_section(sections, name)
        if not body:
            continue
        body_parts.append(body)
        by_section[name] = count_words(body)
    body_text = "\n\n".join(body_parts)

    return {
        "file": str(path),
        "abstract": count_words(abstract_no_kw),
        "abstract_including_keywords": count_words(abstract_raw),
        "main_text": count_words(body_text),
        "main_text_and_abstract": count_words(abstract_no_kw) + count_words(body_text),
        "by_section": by_section,
    }


def resolve_manuscript_path(manuscript: Path | None, paper_dir: Path | None) -> Path:
    if manuscript is not None:
        return manuscript.expanduser().resolve()
    if paper_dir is not None:
        return paper_dir.expanduser().resolve() / DEFAULT_MANUSCRIPT_NAME
    cwd_manuscript = Path.cwd() / DEFAULT_MANUSCRIPT_NAME
    if cwd_manuscript.is_file():
        return cwd_manuscript.resolve()
    raise FileNotFoundError(
        "manuscript not found: pass a path or --paper-dir /path/to/paper"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Count words in manuscript Markdown.")
    parser.add_argument(
        "manuscript",
        nargs="?",
        type=Path,
        default=None,
        help="Path to manuscript.md (optional if --paper-dir is set)",
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=None,
        help="Paper folder containing manuscript.md (e.g. /path/to/paper)",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    args = parser.parse_args(argv)

    try:
        path = resolve_manuscript_path(args.manuscript, args.paper_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    stats = count_manuscript(path)

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0

    print(f"File: {stats['file']}\n")
    print(f"Abstract (structured; excludes Key words): {stats['abstract']}")
    print(f"Abstract (including Key words):           {stats['abstract_including_keywords']}")
    print(f"Main text (Introduction–Discussion):    {stats['main_text']}")
    print(f"Abstract + main text:                     {stats['main_text_and_abstract']}")
    print("\nBy section:")
    for name, n in stats["by_section"].items():
        print(f"  {name}: {n}")
    return 0

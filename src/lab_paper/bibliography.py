from __future__ import annotations

import argparse
import re
from pathlib import Path

from lab_paper.bib_parse import extract_entry_text
from lab_paper.paperpile import resolve_paperpile_bib

# Pandoc citeproc keys only inside bracket citations, e.g. [@Example2024-aa] or [@a; @b]
BRACKET_CITE_RE = re.compile(r"\[(@[^\]]+)\]")
KEY_IN_CITE_RE = re.compile(r"@([A-Za-z][A-Za-z0-9-]*)")


def load_keys_from_file(path: Path) -> list[str]:
    keys: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        keys.append(line.split("#", 1)[0].strip())
    return keys


def extract_cite_keys_from_text(text: str) -> list[str]:
    """Return pandoc citation keys in document order (deduped)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for block in BRACKET_CITE_RE.finditer(text):
        for match in KEY_IN_CITE_RE.finditer(block.group(1)):
            key = match.group(1)
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def scan_keys_from_markdown(paper_dir: Path) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for pattern in ("manuscript.md", "supplementary.md"):
        path = paper_dir / pattern
        if not path.is_file():
            continue
        for key in extract_cite_keys_from_text(path.read_text(encoding="utf-8")):
            if key not in seen:
                seen.add(key)
                ordered.append(key)
    return ordered


def load_manual_entries(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    bib_text = path.read_text(encoding="utf-8", errors="replace")
    entries: dict[str, str] = {}
    for match in re.finditer(r"@\w+\{([^,]+),", bib_text):
        key = match.group(1)
        block = extract_entry_text(bib_text, key)
        if block:
            entries[key] = block.rstrip() + "\n"
    return entries


def _extract_entry_or_raise(bib_text: str, key: str) -> str:
    block = extract_entry_text(bib_text, key)
    if block is None:
        raise KeyError(key)
    return block.rstrip() + "\n"


def build_references_bib(
    paper_dir: Path,
    *,
    paperpile_bib: Path | None = None,
    keys_file: Path | None = None,
    scan_markdown: bool = False,
    out_path: Path | None = None,
) -> Path:
    paper_dir = paper_dir.resolve()
    paperpile_bib = resolve_paperpile_bib(paperpile_bib)
    out_path = out_path or (paper_dir / "references.bib")
    manual_path = paper_dir / "manual_entries.bib"
    legacy_keys = paper_dir / "reference" / "citation_keys.txt"
    if not legacy_keys.is_file():
        legacy_keys = paper_dir / "citation_keys.txt"

    if scan_markdown:
        keys = scan_keys_from_markdown(paper_dir)
    elif keys_file is not None and keys_file.is_file():
        keys = load_keys_from_file(keys_file)
    elif legacy_keys.is_file():
        keys = load_keys_from_file(legacy_keys)
    else:
        keys = scan_keys_from_markdown(paper_dir)

    if not keys:
        raise ValueError("No citation keys found")

    manual = load_manual_entries(manual_path)
    bib_text = paperpile_bib.read_text(encoding="utf-8", errors="replace")

    chunks: list[str] = []
    missing: list[str] = []
    for key in keys:
        if key in manual:
            chunks.append(manual[key].rstrip() + "\n")
            continue
        try:
            chunks.append(_extract_entry_or_raise(bib_text, key))
        except KeyError:
            missing.append(key)

    if missing:
        raise KeyError(
            "Keys not found in paperpile.bib or manual_entries.bib: "
            + ", ".join(missing)
        )

    out_path.write_text("\n".join(chunks).rstrip() + "\n", encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build references.bib from paperpile.bib for a paper markdown project.",
    )
    parser.add_argument(
        "--paper-dir",
        type=Path,
        default=Path("."),
        help="Paper folder containing manuscript.md (default: cwd)",
    )
    parser.add_argument(
        "--paperpile-bib",
        type=Path,
        default=None,
        help="Path to paperpile.bib (default: PAPERPILE_BIB env or lab default)",
    )
    parser.add_argument(
        "--keys-file",
        type=Path,
        default=None,
        help="Optional citation key list (default: scan manuscript.md / supplementary.md)",
    )
    parser.add_argument(
        "--scan-markdown",
        action="store_true",
        help="Collect @keys from manuscript.md / supplementary.md instead of keys file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <paper-dir>/references.bib)",
    )
    args = parser.parse_args(argv)

    out = build_references_bib(
        args.paper_dir,
        paperpile_bib=args.paperpile_bib,
        keys_file=args.keys_file,
        scan_markdown=args.scan_markdown,
        out_path=args.output,
    )
    print(f"Wrote {out}")
    return 0

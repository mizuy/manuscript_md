#!/usr/bin/env python3
"""Generic reference ingest for a paper reference/ directory.

See docs/REFERENCE_INGEST.md. Project-specific scripts may extend this.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

PUBMED_LINE_RE = re.compile(r"^- \*\*PubMed:\*\*.*$", re.M)


def resolve_paperpile() -> Path:
    import os

    default = Path("/Users/mizuy/lab/vault/paperpile.bib")
    fallback = Path.home() / "Google Drive/My Drive/paperpile.bib"
    env = os.environ.get("PAPERPILE_BIB")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p
    for p in (default, fallback):
        if p.is_file():
            return p
    raise FileNotFoundError("paperpile.bib not found")


def discover_keys(ref_root: Path) -> list[str]:
    md_dir = ref_root / "md"
    keys_file = ref_root / "reference_keys.txt"
    from_md = {p.stem for p in md_dir.glob("*.md")} if md_dir.is_dir() else set()
    cited: list[str] = []
    if keys_file.is_file():
        for line in keys_file.read_text(encoding="utf-8").splitlines():
            line = line.strip().split("#", 1)[0].strip()
            if line:
                cited.append(line)
    ordered: list[str] = []
    seen: set[str] = set()
    for k in cited:
        if k in from_md and k not in seen:
            ordered.append(k)
            seen.add(k)
    for k in sorted(from_md - seen):
        ordered.append(k)
    return ordered


def build_reference_bib(ref_root: Path, keys: list[str]) -> Path:
    sys.path.insert(0, str(SCRIPT_DIR))
    from build_bibliography import build_references_bib

    keys_file = ref_root / "reference_keys.txt"
    keys_file.write_text(
        "\n".join(["# pandoc-id", ""] + keys) + "\n",
        encoding="utf-8",
    )
    manual = ref_root.parent / "manual_entries.bib"
    link = ref_root / "manual_entries.bib"
    if manual.is_file() and not link.exists():
        link.symlink_to(manual.resolve())
    out = ref_root / "reference.bib"
    build_references_bib(ref_root, keys_file=keys_file, out_path=out)
    return out


def _field(block: str, name: str) -> str:
    m = re.search(
        rf"{name}\s*=\s*\"((?:[^\"\\]|\\.)*)\"",
        block,
        re.DOTALL | re.IGNORECASE,
    )
    if m:
        return re.sub(r"\s+", " ", m.group(1).replace("\n", " ").strip())
    m = re.search(rf"{name}\s*=\s*(\d+)", block, re.I)
    return m.group(1) if m else ""


def load_bib_block(key: str, bib_path: Path) -> str:
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"@\w+\{{{re.escape(key)},", text)
    if not m:
        return ""
    rest = text[m.start() :]
    nxt = re.search(r"\n@", rest[1:])
    return rest[: nxt.start() + 1] if nxt else rest


def pmid_from_bib(key: str, ref_root: Path) -> str | None:
    ref_bib = ref_root / "reference.bib"
    if ref_bib.is_file():
        block = load_bib_block(key, ref_bib)
        if block:
            pmid = _field(block, "pmid")
            return pmid or None
    paperpile = resolve_paperpile()
    block = load_bib_block(key, paperpile)
    if block:
        pmid = _field(block, "pmid")
        return pmid or None
    return None


def pubmed_md_line(pmid: str | None) -> str:
    if pmid:
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        return f"- **PubMed:** [{pmid}]({url})"
    return "- **PubMed:** —"


def patch_md_pubmed(path: Path, pmid: str | None) -> bool:
    text = path.read_text(encoding="utf-8")
    line = pubmed_md_line(pmid)
    if PUBMED_LINE_RE.search(text):
        new_text = PUBMED_LINE_RE.sub(line, text, count=1)
    elif re.search(r"^- \*\*DOI:\*\*.*$", text, re.M):
        new_text = re.sub(r"(^- \*\*DOI:\*\*.*$)", rf"\1\n{line}", text, count=1, flags=re.M)
    elif re.search(r"^- \*\*PDF:\*\*.*$", text, re.M):
        new_text = re.sub(r"(^- \*\*PDF:\*\*.*$)", rf"\1\n{line}", text, count=1, flags=re.M)
    else:
        return False
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref-dir",
        type=Path,
        required=True,
        help="/path/to/paper/reference/",
    )
    parser.add_argument("--skip-bib", action="store_true")
    args = parser.parse_args()

    ref_root = args.ref_dir.resolve()
    md_dir = ref_root / "md"
    keys = discover_keys(ref_root)

    if not args.skip_bib:
        build_reference_bib(ref_root, keys)
        print(f"Wrote {ref_root / 'reference.bib'}")

    for key in keys:
        md_path = md_dir / f"{key}.md"
        if not md_path.is_file():
            continue
        pmid = pmid_from_bib(key, ref_root)
        patch_md_pubmed(md_path, pmid)

    print(f"Updated PubMed lines for {len(keys)} keys")


if __name__ == "__main__":
    main()

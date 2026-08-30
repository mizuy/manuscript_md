from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from manuscript_md.paths import SKILL_MD


def _copytree_contents(src: Path, dst: Path, *, overwrite: bool) -> list[Path]:
    written: list[Path] = []
    if not src.is_dir():
        return written
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        target = dst / item.name
        if item.is_dir():
            written.extend(_copytree_contents(item, target, overwrite=overwrite))
            continue
        if target.exists() and not overwrite:
            continue
        shutil.copy2(item, target)
        written.append(target)
    return written


def sync_assets(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="manuscript-md sync-assets",
        description=(
            "Optional: copy Lua filters into PAPER_DIR/script/filters for "
            "paper-local overrides. Default docx build uses skill filters "
            "directly (no copy)."
        ),
    )
    parser.add_argument("--paper-dir", type=Path, required=True, help="Target paper directory")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in script/filters, csl, and templates",
    )
    parser.add_argument(
        "--include-csl",
        action="store_true",
        help="Also copy bundled CSL files into PAPER_DIR/csl",
    )
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Also copy bundled templates into PAPER_DIR/templates",
    )
    parser.add_argument(
        "--include-reference-doc",
        action="store_true",
        help="Also copy skill templates/reference.docx into PAPER_DIR/",
    )
    args = parser.parse_args(argv)

    paper_dir = args.paper_dir.expanduser().resolve()
    paper_dir.mkdir(parents=True, exist_ok=True)

    mappings = [(SKILL_MD / "filters", paper_dir / "script" / "filters")]
    if args.include_csl:
        mappings.append((SKILL_MD / "csl", paper_dir / "csl"))
    if args.include_templates:
        mappings.append((SKILL_MD / "templates", paper_dir / "templates"))
    written: list[Path] = []
    for src, dst in mappings:
        written.extend(_copytree_contents(src, dst, overwrite=args.overwrite))
    if args.include_reference_doc:
        src = SKILL_MD / "templates" / "reference.docx"
        dst = paper_dir / "reference.docx"
        if src.is_file() and (args.overwrite or not dst.exists()):
            shutil.copy2(src, dst)
            written.append(dst)

    for path in written:
        print(path)
    if not written:
        print("assets already up to date")
    return 0

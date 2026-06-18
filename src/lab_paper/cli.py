from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = PROJECT_ROOT / "scripts"


SCRIPT_COMMANDS: dict[str, str] = {
    "build-bib": "build_bibliography.py",
    "expand-imports": "expand_imports.py",
    "patch-docx": "patch_docx_tables.py",
    "reference-docx": "build_reference_docx.py",
    "resolve-csl": "resolve_csl.py",
    "word-count": "word_count.py",
    "ingest-reference": "ingest_reference.py",
}


def _run_script(script_name: str, args: list[str]) -> int:
    script = SCRIPT_DIR / script_name
    if not script.is_file():
        print(f"script not found: {script}", file=sys.stderr)
        return 1
    return subprocess.call([sys.executable, str(script), *args])


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
        prog="lab-paper sync-assets",
        description="Sync reusable paper build assets into a paper directory.",
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
    args = parser.parse_args(argv)

    paper_dir = args.paper_dir.expanduser().resolve()
    paper_dir.mkdir(parents=True, exist_ok=True)

    mappings = [(PROJECT_ROOT / "filters", paper_dir / "script" / "filters")]
    if args.include_csl:
        mappings.append((PROJECT_ROOT / "csl", paper_dir / "csl"))
    if args.include_templates:
        mappings.append((PROJECT_ROOT / "templates", paper_dir / "templates"))
    written: list[Path] = []
    for src, dst in mappings:
        written.extend(_copytree_contents(src, dst, overwrite=args.overwrite))

    for path in written:
        print(path)
    if not written:
        print("assets already up to date")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        commands = "\n".join(f"  {name}" for name in sorted([*SCRIPT_COMMANDS, "sync-assets"]))
        print(f"usage: lab-paper <command> [args]\n\ncommands:\n{commands}")
        return 0 if args else 1

    command, rest = args[0], args[1:]
    if command == "sync-assets":
        return sync_assets(rest)
    if command in SCRIPT_COMMANDS:
        return _run_script(SCRIPT_COMMANDS[command], rest)

    print(f"unknown command: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Resolve manuscript version chains from versions/manifest.yml.

Usage:
    python version_manifest.py list --paper-dir /path/to/paper
    python version_manifest.py validate --paper-dir /path/to/paper
    python version_manifest.py resolve-tag --paper-dir /path/to/paper --version 5
    python version_manifest.py resolve-diff --paper-dir /path/to/paper
    python version_manifest.py resolve-diff --paper-dir /path/to/paper --entry v5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - optional at import time
    yaml = None  # type: ignore[assignment]

MANIFEST_NAME = "manifest.yml"
INTERNAL_ROLES = frozenset({"internal", None})
DIFF_BASE_ROLES = frozenset({"internal", "approved", None})


@dataclass(frozen=True)
class ManifestEntry:
    id: str
    file: str
    role: str | None = None
    diff_base: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class Manifest:
    document: str
    prefix: str
    entries: tuple[ManifestEntry, ...]
    compare: bool = True

    def by_id(self) -> dict[str, ManifestEntry]:
        return {entry.id: entry for entry in self.entries}


def manifest_path(paper_dir: Path, manifest_name: str = MANIFEST_NAME) -> Path:
    return paper_dir / "versions" / manifest_name


def normalize_entry_id(version: str) -> str:
    version = version.strip()
    if re.fullmatch(r"v?\d+", version, flags=re.IGNORECASE):
        number = version.lstrip("vV")
        return f"v{number}"
    return version


def load_manifest(paper_dir: Path, *, manifest_name: str = MANIFEST_NAME) -> Manifest:
    path = manifest_path(paper_dir, manifest_name)
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")
    if yaml is None:
        raise RuntimeError("PyYAML is required to read manifest.yml (pip/uv install pyyaml).")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid manifest (expected mapping): {path}")

    entries_raw = raw.get("entries")
    if not isinstance(entries_raw, list) or not entries_raw:
        raise ValueError(f"Manifest must define a non-empty entries list: {path}")

    entries: list[ManifestEntry] = []
    for item in entries_raw:
        if not isinstance(item, dict):
            raise ValueError(f"Each manifest entry must be a mapping: {item!r}")
        entry_id = str(item["id"])
        file_name = str(item["file"])
        entries.append(
            ManifestEntry(
                id=entry_id,
                file=file_name,
                role=item.get("role"),
                diff_base=item.get("diff_base"),
                source=item.get("source"),
            )
        )

    return Manifest(
        document=str(raw.get("document", "manuscript")),
        prefix=str(raw.get("prefix", "ADR_manuscript")),
        entries=tuple(entries),
        compare=bool(raw.get("compare", True)),
    )


def versions_dir(paper_dir: Path) -> Path:
    return paper_dir / "versions"


def entry_path(paper_dir: Path, file_name: str) -> Path:
    return versions_dir(paper_dir) / file_name


def diff_output_name(changed_file: str) -> str:
    stem, suffix = changed_file.rsplit(".", 1)
    return f"{stem}_diff.{suffix}"


def find_entry(manifest: Manifest, version: str) -> ManifestEntry:
    entry_id = normalize_entry_id(version)
    by_id = manifest.by_id()
    if entry_id in by_id:
        return by_id[entry_id]
    raise KeyError(f"Manifest entry not found for version {version!r} (id {entry_id!r}).")


def default_diff_base(manifest: Manifest, entry: ManifestEntry) -> ManifestEntry | None:
    if entry.diff_base:
        return manifest.by_id().get(entry.diff_base)

    index = manifest.entries.index(entry)
    for candidate in reversed(manifest.entries[:index]):
        if candidate.role in DIFF_BASE_ROLES and candidate.role != "ms_return":
            return candidate
    return None


def resolve_tag(
    paper_dir: Path,
    *,
    version: str,
    source: Path | None = None,
    manifest_name: str = MANIFEST_NAME,
) -> dict[str, Any]:
    paper_dir = paper_dir.resolve()
    manifest = load_manifest(paper_dir, manifest_name=manifest_name)
    entry = find_entry(manifest, version)
    target = entry_path(paper_dir, entry.file)
    diff = entry_path(paper_dir, diff_output_name(entry.file))

    base_entry = default_diff_base(manifest, entry) if manifest.compare else None
    base: Path | None = None
    if base_entry is not None:
        base = entry_path(paper_dir, base_entry.file)

    result: dict[str, Any] = {
        "paper_dir": str(paper_dir),
        "entry_id": entry.id,
        "target": str(target),
        "diff": str(diff),
        "target_file": entry.file,
        "diff_file": diff_output_name(entry.file),
        "source": str(source.resolve()) if source else None,
    }
    if base_entry is not None and base is not None:
        result["base_id"] = base_entry.id
        result["base"] = str(base)
        result["base_file"] = base_entry.file
    return result


def resolve_latest_diff(
    paper_dir: Path,
    *,
    entry_id: str | None = None,
    manifest_name: str = MANIFEST_NAME,
) -> dict[str, Any]:
    paper_dir = paper_dir.resolve()
    manifest = load_manifest(paper_dir, manifest_name=manifest_name)

    if not manifest.compare:
        raise ValueError(
            f"Manifest {manifest_name!r} has compare: false; resolve-diff is not supported."
        )

    if entry_id is not None:
        entry = find_entry(manifest, entry_id)
    else:
        candidates = [
            e
            for e in manifest.entries
            if e.role in INTERNAL_ROLES and e.role != "ms_return"
        ]
        if not candidates:
            raise ValueError("No internal manifest entry found for resolve-diff.")
        entry = candidates[-1]

    info = resolve_tag(paper_dir, version=entry.id, manifest_name=manifest_name)
    if "base" not in info:
        raise ValueError(f"No diff base resolved for entry {entry.id!r}.")
    if not Path(info["target"]).is_file():
        raise FileNotFoundError(f"Changed file not found: {info['target']}")
    if not Path(info["base"]).is_file():
        raise FileNotFoundError(f"Base file not found: {info['base']}")
    return info


def validate_manifest(paper_dir: Path, *, manifest_name: str = MANIFEST_NAME) -> list[str]:
    paper_dir = paper_dir.resolve()
    manifest = load_manifest(paper_dir, manifest_name=manifest_name)
    errors: list[str] = []
    seen_ids: set[str] = set()

    for entry in manifest.entries:
        if entry.id in seen_ids:
            errors.append(f"Duplicate entry id: {entry.id}")
        seen_ids.add(entry.id)

        path = entry_path(paper_dir, entry.file)
        if not path.is_file():
            errors.append(f"Missing file for {entry.id}: {path}")

        if entry.diff_base and entry.diff_base not in manifest.by_id():
            errors.append(f"{entry.id}: unknown diff_base {entry.diff_base!r}")

        if entry.source and entry.source not in manifest.by_id():
            errors.append(f"{entry.id}: unknown source {entry.source!r}")

    return errors


def print_list(paper_dir: Path, *, manifest_name: str = MANIFEST_NAME) -> None:
    paper_dir = paper_dir.resolve()
    manifest = load_manifest(paper_dir, manifest_name=manifest_name)
    print(f"document: {manifest.document}")
    print(f"prefix:   {manifest.prefix}")
    print(f"manifest: {manifest_path(paper_dir, manifest_name)}")
    print()
    print(f"{'id':<18} {'role':<12} {'diff_base':<18} {'file':<40} ok")
    print("-" * 96)
    for entry in manifest.entries:
        path = entry_path(paper_dir, entry.file)
        ok = "yes" if path.is_file() else "NO"
        role = entry.role or "internal"
        base = entry.diff_base or ""
        print(f"{entry.id:<18} {role:<12} {base:<18} {entry.file:<40} {ok}")


def main(argv: list[str] | None = None) -> int:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--paper-dir", type=Path, required=True)
    parent.add_argument(
        "--manifest",
        default=MANIFEST_NAME,
        help=f"Manifest file under versions/ (default: {MANIFEST_NAME})",
    )

    parser = argparse.ArgumentParser(description="Resolve paper version manifest.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", parents=[parent])
    sub.add_parser("validate", parents=[parent])

    p_tag = sub.add_parser("resolve-tag", parents=[parent])
    p_tag.add_argument("--version", required=True)
    p_tag.add_argument("--source", type=Path, default=None)
    p_tag.add_argument("--json", action="store_true")

    p_diff = sub.add_parser("resolve-diff", parents=[parent])
    p_diff.add_argument("--entry", default=None, help="Entry id (default: latest internal)")
    p_diff.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    paper_dir = args.paper_dir.expanduser().resolve()
    manifest_name = args.manifest

    try:
        if args.command == "list":
            print_list(paper_dir, manifest_name=manifest_name)
            return 0
        if args.command == "validate":
            errors = validate_manifest(paper_dir, manifest_name=manifest_name)
            if errors:
                for err in errors:
                    print(f"error: {err}", file=sys.stderr)
                return 1
            print(f"OK: {manifest_path(paper_dir, manifest_name)}")
            return 0
        if args.command == "resolve-tag":
            info = resolve_tag(
                paper_dir,
                version=args.version,
                source=args.source,
                manifest_name=manifest_name,
            )
            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                for key, value in info.items():
                    if value is not None:
                        print(f"{key}={value}")
            return 0
        if args.command == "resolve-diff":
            info = resolve_latest_diff(
                paper_dir,
                entry_id=args.entry,
                manifest_name=manifest_name,
            )
            if args.json:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                for key, value in info.items():
                    if value is not None:
                        print(f"{key}={value}")
            return 0
    except (FileNotFoundError, KeyError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

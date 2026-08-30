from __future__ import annotations

import sys
from collections.abc import Callable

from manuscript_md import (
    author_list,
    bibliography,
    bootstrap_reference,
    checkme,
    csl,
    export_figures,
    markdown,
    patch_docx,
    reference_doc,
    reference_ingest,
    sync_assets,
    translate_abstract,
    word_count,
)

COMMANDS: dict[str, Callable[[list[str] | None], int]] = {
    "author-list": author_list.main,
    "bootstrap-reference": bootstrap_reference.main,
    "build-bib": bibliography.main,
    "checkme": checkme.main,
    "expand-imports": markdown.main,
    "export-figures": export_figures.main,
    "ingest-reference": reference_ingest.main,
    "patch-docx": patch_docx.main,
    "resolve-csl": csl.main,
    "resolve-reference-doc": reference_doc.main,
    "sync-assets": sync_assets.sync_assets,
    "translate-abstract-ja": translate_abstract.main,
    "word-count": word_count.main,
}


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        commands = "\n".join(f"  {name}" for name in sorted(COMMANDS))
        print(f"usage: manuscript-md <command> [args]\n\ncommands:\n{commands}")
        return 0 if args else 1

    command, rest = args[0], args[1:]
    handler = COMMANDS.get(command)
    if handler is None:
        print(f"unknown command: {command}", file=sys.stderr)
        return 2
    return handler(rest)


if __name__ == "__main__":
    raise SystemExit(main())

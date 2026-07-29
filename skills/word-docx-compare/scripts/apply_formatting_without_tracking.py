#!/usr/bin/env python3
"""Apply compared DOCX formatting while removing formatting-only revisions."""

from __future__ import annotations

import argparse
import os
import re
import tempfile
import zipfile
from pathlib import Path


FORMAT_CHANGE_TAGS = (
    b"pPrChange",
    b"rPrChange",
    b"sectPrChange",
    b"tblGridChange",
    b"tblPrChange",
    b"tcPrChange",
    b"trPrChange",
)


def remove_format_change_markup(xml: bytes) -> tuple[bytes, int]:
    removed = 0
    for tag in FORMAT_CHANGE_TAGS:
        paired = re.compile(
            rb"<w:" + tag + rb"\b[^>]*>.*?</w:" + tag + rb">",
            flags=re.DOTALL,
        )
        xml, count = paired.subn(b"", xml)
        removed += count

        self_closing = re.compile(rb"<w:" + tag + rb"\b[^>]*/>")
        xml, count = self_closing.subn(b"", xml)
        removed += count
    return xml, removed


def process_docx(path: Path) -> int:
    path = path.resolve()
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.stem}.",
        suffix=".docx",
        dir=path.parent,
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    removed = 0

    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            temporary_path,
            "w",
        ) as destination:
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename.endswith(".xml"):
                    data, count = remove_format_change_markup(data)
                    removed += count
                destination.writestr(item, data)
        os.replace(temporary_path, path)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise

    return removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Remove formatting revision markup from a Word comparison while "
            "retaining the revised formatting and text revisions."
        )
    )
    parser.add_argument("docx", type=Path)
    args = parser.parse_args()

    removed = process_docx(args.docx)
    print(f"Applied formatting and removed {removed} formatting revisions")


if __name__ == "__main__":
    main()

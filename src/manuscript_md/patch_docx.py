#!/usr/bin/env python3
"""Patch pandoc docx: table layout and explicit portrait final section."""

from __future__ import annotations

import argparse
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

TABLE_BLOCK = re.compile(r"<w:tbl\b.*?</w:tbl>", re.DOTALL)
COMPACT_STYLE = re.compile(
    r'(<w:pPr\b[^>]*>.*?<w:pStyle w:val=")Compact(" />)', re.DOTALL
)
TBL_WIDTH_AUTO = re.compile(
    r'(<w:tblPr\b[^>]*>.*?<w:tblW )w:type="auto" w:w="0"',
    re.DOTALL,
)
FINAL_SECTPR = re.compile(
    r"(<w:sectPr\b[^>]*>)(.*?)(</w:sectPr>\s*</w:body>)",
    re.DOTALL,
)
SECTPR_BLOCK = re.compile(r"(<w:sectPr\b[^>]*>)(.*?)(</w:sectPr>)", re.DOTALL)
FOOTER_REFERENCE = re.compile(r"<w:footerReference\b[^>]*/>")
PGNUM_TYPE = re.compile(r"<w:pgNumType\b[^>]*/>")
TABLE_PARA = re.compile(r"(<w:p\b[^>]*>)(.*?)(</w:p>)", re.DOTALL)
TABLE_ROW = re.compile(r"<w:tr\b.*?</w:tr>", re.DOTALL)
TABLE_CELL = re.compile(r"<w:tc\b.*?</w:tc>", re.DOTALL)
PORTRAIT_PG = '<w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/>'
PGSZ_TAG = re.compile(r"<w:pgSz\b[^>]*/>")
CELL_SPACING = (
    '<w:spacing w:after="60" w:before="20" w:line="288" w:lineRule="auto"/>'
)
VALIGN_CENTER = '<w:vAlign w:val="center"/>'
JC_CENTER = '<w:jc w:val="center"/>'


def patch_table_paragraph_spacing(table_xml: str) -> str:
    def repl(match: re.Match[str]) -> str:
        opening, inner, closing = match.group(1), match.group(2), match.group(3)
        if "<w:pPr" in inner:
            if "<w:spacing" not in inner:
                inner = inner.replace("</w:pPr>", f"{CELL_SPACING}</w:pPr>", 1)
        else:
            inner = f"<w:pPr>{CELL_SPACING}</w:pPr>{inner}"
        return opening + inner + closing

    return TABLE_PARA.sub(repl, table_xml)


def _inject_tc_valign(cell_xml: str) -> str:
    if "w:vAlign" in cell_xml:
        return cell_xml
    if re.search(r"<w:tcPr\s*/>", cell_xml):
        return cell_xml.replace(
            "<w:tcPr />",
            f"<w:tcPr>{VALIGN_CENTER}</w:tcPr>",
            1,
        )
    return re.sub(r"(</w:tcPr>)", f"{VALIGN_CENTER}\\1", cell_xml, count=1)


def _inject_para_jc_center(cell_xml: str) -> str:
    def repl(match: re.Match[str]) -> str:
        opening, inner, closing = match.group(1), match.group(2), match.group(3)
        if "w:jc" in inner:
            return match.group(0)
        if "<w:pPr" in inner:
            inner = inner.replace("</w:pPr>", f"{JC_CENTER}</w:pPr>", 1)
        else:
            inner = f"<w:pPr>{JC_CENTER}</w:pPr>{inner}"
        return opening + inner + closing

    return TABLE_PARA.sub(repl, cell_xml)


def patch_table_cell_alignment(table_xml: str) -> str:
    """Stub column left; data columns center. All cells vertically center."""

    def patch_row(row_match: re.Match[str]) -> str:
        row = row_match.group(0)
        cells = list(TABLE_CELL.finditer(row))
        if not cells:
            return row
        parts: list[str] = []
        last = 0
        for idx, match in enumerate(cells):
            parts.append(row[last : match.start()])
            cell = _inject_tc_valign(match.group(0))
            if idx > 0:
                cell = _inject_para_jc_center(cell)
            parts.append(cell)
            last = match.end()
        parts.append(row[last:])
        return "".join(parts)

    return TABLE_ROW.sub(patch_row, table_xml)


def patch_table_xml(table_xml: str) -> str:
    table_xml = TBL_WIDTH_AUTO.sub(r'\1w:type="pct" w:w="5000"', table_xml, count=1)
    table_xml = COMPACT_STYLE.sub(r"\1TableCompact\2", table_xml)
    table_xml = patch_table_paragraph_spacing(table_xml)
    table_xml = patch_table_cell_alignment(table_xml)
    return table_xml


def patch_final_sectpr_portrait(document_xml: str) -> str:
    def repl(match: re.Match[str]) -> str:
        inner = match.group(2)
        if PGSZ_TAG.search(inner):
            inner = PGSZ_TAG.sub(PORTRAIT_PG, inner, count=1)
        else:
            inner = PORTRAIT_PG + inner
        return match.group(1) + inner + match.group(3)

    return FINAL_SECTPR.sub(repl, document_xml, count=1)


def _final_section_snippets(document_xml: str) -> tuple[str, str]:
    """Footer refs and pgNumType from the body-end sectPr (from reference.docx)."""
    match = FINAL_SECTPR.search(document_xml)
    if not match:
        return "", ""
    inner = match.group(2)
    footers = "".join(FOOTER_REFERENCE.findall(inner))
    pgnum = PGNUM_TYPE.search(inner)
    return footers, pgnum.group(0) if pgnum else ""


def patch_propagate_section_footers(document_xml: str) -> str:
    """Copy footer/page-number sectPr from the final section to landscape breaks.

    landscape.lua inserts sectPr blocks without footerReference, so Word shows
    page numbers only in the last section (after the landscape table).
    """
    footers, pgnum = _final_section_snippets(document_xml)
    if not footers:
        return document_xml

    def repl(match: re.Match[str]) -> str:
        opening, inner, closing = match.group(1), match.group(2), match.group(3)
        if "footerReference" in inner:
            return match.group(0)
        inject = footers
        if pgnum and "pgNumType" not in inner:
            inject += pgnum
        return opening + inject + inner + closing

    return SECTPR_BLOCK.sub(repl, document_xml)


def patch_document_xml(document_xml: str) -> str:
    document_xml = TABLE_BLOCK.sub(lambda m: patch_table_xml(m.group(0)), document_xml)
    document_xml = patch_propagate_section_footers(document_xml)
    return patch_final_sectpr_portrait(document_xml)


def patch_docx(path: Path) -> Path:
    path = path.resolve()
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        patched = tmp_path / path.name
        with zipfile.ZipFile(path, "r") as zin, zipfile.ZipFile(patched, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    text = data.decode("utf-8")
                    data = patch_document_xml(text).encode("utf-8")
                zout.writestr(item, data)
        shutil.copy2(patched, path)
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path, nargs="+", help="docx file(s) to patch in place")
    args = parser.parse_args(argv)
    for docx in args.docx:
        patch_docx(docx)
        print(f"Patched {docx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

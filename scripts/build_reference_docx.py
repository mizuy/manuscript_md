#!/usr/bin/env python3
"""Build a pandoc reference.docx: Helvetica, black only, double-spaced, continuous line numbers."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
ET.register_namespace("w", W_NS)

# Word "double spacing": 480 twips = 2 × single (240) with lineRule auto
DOUBLE_SPACING = {"w:line": "480", "w:lineRule": "auto", "w:after": "0", "w:before": "0"}
SINGLE_SPACING = {"w:line": "240", "w:lineRule": "auto", "w:after": "0", "w:before": "0"}
# Table cells: slightly open line height + small before/after (twips).
TABLE_COMPACT_SPACING = {
    "w:line": "288",
    "w:lineRule": "auto",
    "w:after": "60",
    "w:before": "20",
}
# Word font size is half-points: 10 pt = 20.
TABLE_FONT_SIZE = "20"
FONT_ATTRS = {
    f"{{{W_NS}}}ascii": "Helvetica",
    f"{{{W_NS}}}hAnsi": "Helvetica",
    f"{{{W_NS}}}eastAsia": "Helvetica",
    f"{{{W_NS}}}cs": "Helvetica",
}
BLACK = {f"{{{W_NS}}}val": "000000"}


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _find_or_create(parent: ET.Element, tag: str) -> ET.Element:
    child = parent.find(f"w:{tag}", NS)
    if child is None:
        child = ET.SubElement(parent, _w(tag))
    return child


def _set_fonts(rpr: ET.Element) -> None:
    fonts = _find_or_create(rpr, "rFonts")
    for key, value in FONT_ATTRS.items():
        fonts.set(key, value)
    for theme_key in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        qname = f"{{{W_NS}}}{theme_key}"
        if qname in fonts.attrib:
            del fonts.attrib[qname]


def _set_black(rpr: ET.Element) -> None:
    color = _find_or_create(rpr, "color")
    color.attrib.clear()
    color.set(_w("val"), "000000")


def _set_spacing(ppr: ET.Element, spacing: dict[str, str]) -> None:
    node = _find_or_create(ppr, "spacing")
    for key, value in spacing.items():
        local = key.split(":")[1]
        node.set(_w(local), value)


def _set_double_spacing(ppr: ET.Element) -> None:
    _set_spacing(ppr, DOUBLE_SPACING)


def _set_single_spacing(ppr: ET.Element) -> None:
    _set_spacing(ppr, SINGLE_SPACING)


def _set_font_size(rpr: ET.Element, half_points: str) -> None:
    sz = _find_or_create(rpr, "sz")
    sz.set(_w("val"), half_points)
    sz_cs = _find_or_create(rpr, "szCs")
    sz_cs.set(_w("val"), half_points)


def _add_table_compact_style(root: ET.Element) -> None:
    """Paragraph style for table cells: 10 pt, compact spacing."""
    style = ET.SubElement(root, _w("style"))
    style.set(_w("type"), "paragraph")
    style.set(_w("customStyle"), "1")
    style.set(_w("styleId"), "TableCompact")
    ET.SubElement(style, _w("name")).set(_w("val"), "Table Compact")
    based_on = ET.SubElement(style, _w("basedOn"))
    based_on.set(_w("val"), "Normal")
    ppr = ET.SubElement(style, _w("pPr"))
    _set_spacing(ppr, TABLE_COMPACT_SPACING)
    rpr = ET.SubElement(style, _w("rPr"))
    _set_fonts(rpr)
    _set_black(rpr)
    _set_font_size(rpr, TABLE_FONT_SIZE)


def _patch_styles(styles_xml: bytes) -> bytes:
    root = ET.fromstring(styles_xml)

    doc_defaults = root.find("w:docDefaults", NS)
    if doc_defaults is not None:
        rpr_default = doc_defaults.find("w:rPrDefault/w:rPr", NS)
        if rpr_default is not None:
            _set_fonts(rpr_default)
            _set_black(rpr_default)
        ppr_default = doc_defaults.find("w:pPrDefault/w:pPr", NS)
        if ppr_default is not None:
            _set_double_spacing(ppr_default)

    for style in root.findall("w:style", NS):
        rpr = style.find("w:rPr", NS)
        if rpr is None:
            rpr = ET.SubElement(style, _w("rPr"))
        _set_fonts(rpr)
        _set_black(rpr)

        if style.get(_w("type")) == "paragraph":
            ppr = style.find("w:pPr", NS)
            if ppr is None:
                ppr = ET.SubElement(style, _w("pPr"))
            style_id = style.get(_w("styleId"))
            if style_id != "TableCompact":
                _set_double_spacing(ppr)

        # Hyperlinks: black, keep underline for accessibility
        style_id = style.get(_w("styleId"))
        if style_id == "Hyperlink":
            u = _find_or_create(rpr, "u")
            u.set(_w("val"), "single")

    _add_table_compact_style(root)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _patch_document(document_xml: bytes) -> bytes:
    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    if body is None:
        raise ValueError("word/document.xml: missing w:body")

    sect_pr = body.find("w:sectPr", NS)
    if sect_pr is None:
        sect_pr = ET.SubElement(body, _w("sectPr"))

    ln_num = sect_pr.find("w:lnNumType", NS)
    if ln_num is None:
        ln_num = ET.SubElement(sect_pr, _w("lnNumType"))
    ln_num.set(_w("countBy"), "1")
    ln_num.set(_w("restart"), "continuous")

    pg_sz = sect_pr.find("w:pgSz", NS)
    if pg_sz is None:
        pg_sz = ET.SubElement(sect_pr, _w("pgSz"))
    pg_sz.set(_w("w"), "12240")
    pg_sz.set(_w("h"), "15840")
    pg_sz.set(_w("orient"), "portrait")

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _patch_font_table(font_table_xml: bytes) -> bytes:
    root = ET.fromstring(font_table_xml)
    fonts = root.findall("w:font", NS)
    names = {f.get(_w("name")) for f in fonts}
    if "Helvetica" not in names:
        helv = ET.SubElement(root, _w("font"))
        helv.set(_w("name"), "Helvetica")
        ET.SubElement(helv, _w("panose1")).set(_w("val"), "020B0604030504040204")
        charset = ET.SubElement(helv, _w("charset"))
        charset.set(_w("val"), "00")
        family = ET.SubElement(helv, _w("family"))
        family.set(_w("val"), "swiss")
        pitch = ET.SubElement(helv, _w("pitch"))
        pitch.set(_w("val"), "variable")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build_reference_docx(output: Path) -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        default_docx = Path(tmp) / "default-reference.docx"
        subprocess.run(
            ["pandoc", "--print-default-data-file", "reference.docx"],
            check=True,
            stdout=default_docx.open("wb"),
        )

        output.parent.mkdir(parents=True, exist_ok=True)
        patched = Path(tmp) / "patched"
        with zipfile.ZipFile(default_docx, "r") as zin, zipfile.ZipFile(patched, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/styles.xml":
                    data = _patch_styles(data)
                elif item.filename == "word/document.xml":
                    data = _patch_document(data)
                elif item.filename == "word/fontTable.xml":
                    data = _patch_font_table(data)
                zout.writestr(item, data)

        shutil.copy2(patched, output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("reference.docx"),
        help="Output reference.docx path",
    )
    args = parser.parse_args()
    out = build_reference_docx(args.output.resolve())
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()

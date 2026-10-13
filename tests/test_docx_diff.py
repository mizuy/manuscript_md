from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import support  # noqa: F401

from manuscript_md import docx_diff

W = docx_diff.W_NS
w = docx_diff.w


def document(*paragraphs: str) -> bytes:
    """Minimal document.xml; '*' wraps bold text, '|' splits runs."""
    body = []
    for para in paragraphs:
        runs = []
        for k, part in enumerate(para.split("*")):
            for chunk in part.split("|"):
                if chunk:
                    rpr = "<w:rPr><w:b/></w:rPr>" if k % 2 else ""
                    runs.append(f'<w:r>{rpr}<w:t xml:space="preserve">{chunk}</w:t></w:r>')
        body.append(f"<w:p>{''.join(runs)}</w:p>")
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        f'<w:document xmlns:w="{W}" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" mc:Ignorable="w14">'
        f"<w:body>{''.join(body)}<w:sectPr/></w:body></w:document>"
    ).encode()


def view(xml: bytes, mode: str) -> list[str]:
    """Paragraph texts after accepting/rejecting revisions, or with markup."""

    def walk(elem: ET.Element, state: str | None, parts: list[str]) -> None:
        for child in elem:
            if child.tag == w("pPr"):
                continue
            st = {w("ins"): "ins", w("del"): "del"}.get(child.tag, state)
            if child.tag in (w("t"), w("delText")):
                text = child.text or ""
                if mode == "markup":
                    text = {"ins": "{+%s+}", "del": "[-%s-]"}.get(st, "%s") % text
                elif (mode == "accept" and st == "del") or (mode == "reject" and st == "ins"):
                    text = ""
                parts.append(text)
            walk(child, st, parts)

    root = ET.fromstring(xml)
    result = []
    for p in root.find(w("body")).iter(w("p")):
        mark = p.find(f"{w('pPr')}/{w('rPr')}")
        if mark is not None:
            if mode == "accept" and mark.find(w("del")) is not None:
                continue
            if mode == "reject" and mark.find(w("ins")) is not None:
                continue
        parts: list[str] = []
        walk(p, None, parts)
        result.append("".join(parts))
    return result


class DocxDiffTests(unittest.TestCase):
    def check(self, old: tuple[str, ...], new: tuple[str, ...]) -> list[str]:
        out, _ = docx_diff.diff_documents(document(*old), document(*new), date="2026-01-01T00:00:00Z")
        plain = lambda ps: [p.replace("*", "").replace("|", "") for p in ps]
        self.assertEqual(view(out, "accept"), plain(new))
        self.assertEqual(view(out, "reject"), plain(old))
        return view(out, "markup")

    def test_character_level_changes(self) -> None:
        markup = self.check(("The cohort had 1,234 patients.",), ("The cohort had 1,345 patients.",))
        self.assertEqual(markup, ["The cohort had 1,[-2-]34{+5+} patients."])

    def test_formatting_only_change_is_ignored(self) -> None:
        markup = self.check(("Colorectal cancer is common.",), ("*Colorectal cancer* is com|mon.",))
        self.assertEqual(markup, ["Colorectal cancer is common."])

    def test_change_across_runs_keeps_new_formatting(self) -> None:
        out, _ = docx_diff.diff_documents(
            document("A major cause."), document("A *leading* cause.")
        )
        self.assertEqual(view(out, "markup"), ["A [-major-]{+leading+} cause."])
        inserted = ET.fromstring(out).find(f".//{w('ins')}/{w('r')}")
        self.assertIsNotNone(inserted.find(f"{w('rPr')}/{w('b')}"))

    def test_japanese_text(self) -> None:
        markup = self.check(("大腸癌は日本で主要な死因である。",), ("大腸がんは日本における主要な死因である。",))
        self.assertEqual(markup, ["大腸[-癌-]{+がん+}は日本[-で-]{+における+}主要な死因である。"])

    def test_short_matches_are_merged(self) -> None:
        markup = self.check(("We studied the patients.",), ("We analysed the cohort.",))
        self.assertEqual(markup, ["We [-studi-]{+analys+}ed the [-patients-]{+cohort+}."])

    def test_inserted_and_deleted_paragraphs(self) -> None:
        self.check(
            ("Intro.", "This paragraph goes away.", "Kept text here."),
            ("Intro.", "Kept text here, edited.", "A brand new closing paragraph."),
        )

    def test_root_namespaces_are_preserved(self) -> None:
        out, _ = docx_diff.diff_documents(document("a"), document("b"))
        self.assertIn(b'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"', out)
        self.assertIn(b'mc:Ignorable="w14"', out)

    def test_existing_revisions_in_base_are_accepted(self) -> None:
        once, _ = docx_diff.diff_documents(document("Old text.", "Gone."), document("New text."))
        _, stats = docx_diff.diff_documents(once, document("New text."))
        self.assertEqual(stats, {"changed": 0, "inserted": 0, "deleted": 0, "edits": 0})

    def test_diff_docx_writes_package(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = {}
            for name, xml in (("old", document("one")), ("new", document("two"))):
                paths[name] = Path(tmp) / f"{name}.docx"
                with zipfile.ZipFile(paths[name], "w") as z:
                    z.writestr("[Content_Types].xml", "<Types/>")
                    z.writestr(docx_diff.DOCUMENT_PART, xml)
            output = Path(tmp) / "out" / "diff.docx"
            docx_diff.diff_docx(paths["old"], paths["new"], output)
            with zipfile.ZipFile(output) as z:
                self.assertEqual(sorted(z.namelist()), ["[Content_Types].xml", "word/document.xml"])
                self.assertEqual(view(z.read(docx_diff.DOCUMENT_PART), "accept"), ["two"])


    def test_table_rows_are_row_revisions(self) -> None:
        def table(*rows: str) -> bytes:
            cells = "".join(
                "<w:tr>" + "".join(
                    f'<w:tc><w:p><w:r><w:t>{c}</w:t></w:r></w:p></w:tc>' for c in row.split(",")
                ) + "</w:tr>"
                for row in rows
            )
            return document().replace(b"<w:sectPr/>", f"<w:tbl>{cells}</w:tbl><w:sectPr/>".encode())

        out, _ = docx_diff.diff_documents(table("a,1", "b,2", "c,3"), table("a,1", "c,4", "d,5"))
        marks = [
            [mark.tag for mark in tr.iterfind(f"{w('trPr')}/*")]
            for tr in ET.fromstring(out).iter(w("tr"))
        ]
        self.assertEqual(marks, [[], [w("del")], [], [w("ins")]])
        self.assertEqual(view(out, "reject"), ["a", "1", "b", "2", "c", "3"])
        self.assertEqual(view(out, "accept"), ["a", "1", "c", "4", "d", "5"])

    def test_sample_files_round_trip(self) -> None:
        samples = Path(__file__).parent / "fixtures" / "docx_diff"
        cases = sorted(p for p in samples.iterdir() if (p / "diff.docx").exists())
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(case.name):
                texts = {}
                for name in ("old", "new"):
                    with zipfile.ZipFile(case / f"{name}.docx") as z:
                        texts[name] = view(z.read(docx_diff.DOCUMENT_PART), "accept")
                with tempfile.TemporaryDirectory() as tmp:
                    output = Path(tmp) / "diff.docx"
                    docx_diff.diff_docx(case / "old.docx", case / "new.docx", output)
                    with zipfile.ZipFile(output) as z:
                        xml = z.read(docx_diff.DOCUMENT_PART)
                self.assertEqual(view(xml, "accept"), texts["new"])
                self.assertEqual(view(xml, "reject"), texts["old"])


if __name__ == "__main__":
    unittest.main()

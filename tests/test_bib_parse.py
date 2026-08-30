from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401

from manuscript_md import bib_parse


ENTRY = """@article{Smith2024,
  title = {{Nested {Brace} Title}},
  author = {Smith, Alice and Doe, Bob},
  journaltitle = {Journal of Tests},
  date = {2024-05-01},
  volume = {12},
  issue = {3},
  pages = {10--20},
  doi = {10.1000/test},
  pmid = {123456},
  abstract = {A
    multiline abstract}
}
"""


class BibParseTests(unittest.TestCase):
    def test_parse_entry_extracts_core_metadata(self) -> None:
        meta = bib_parse.parse_entry(ENTRY, "Smith2024")

        self.assertEqual(meta.key, "Smith2024")
        self.assertEqual(meta.title, "Nested {Brace} Title")
        self.assertEqual(meta.authors, ["Smith, Alice", "Doe, Bob"])
        self.assertEqual(meta.journal, "Journal of Tests")
        self.assertEqual(meta.year, "2024")
        self.assertEqual(meta.volume, "12")
        self.assertEqual(meta.number, "3")
        self.assertEqual(meta.pages, "10--20")
        self.assertEqual(meta.doi, "10.1000/test")
        self.assertEqual(meta.pmid, "123456")
        self.assertEqual(meta.abstract, "A multiline abstract")

    def test_extract_entry_returns_only_requested_bibtex_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bib_path = Path(tmp) / "references.bib"
            bib_path.write_text(
                ENTRY
                + "\n@article{Other2024,\n  title = {Other},\n  year = {2024}\n}\n",
                encoding="utf-8",
            )

            block = bib_parse.extract_entry(bib_path, "Smith2024")

        self.assertIsNotNone(block)
        assert block is not None
        self.assertIn("@article{Smith2024,", block)
        self.assertNotIn("@article{Other2024,", block)

    def test_journal_citation_uses_dash_when_metadata_is_empty(self) -> None:
        empty = bib_parse.BibMeta(
            key="Empty",
            title="",
            authors=[],
            journal="",
            year="",
            volume="",
            number="",
            pages="",
            doi="",
            pmid="",
            url="",
            abstract="",
            raw="",
        )

        self.assertEqual(bib_parse.journal_citation(empty), "—")

    def test_replace_metadata_section_updates_existing_section_only(self) -> None:
        source = "# Paper\n\n## メタデータ\n\nold\n\n## Notes\n\nkeep\n"
        replaced = bib_parse.replace_metadata_section(source, "new metadata")

        self.assertEqual(replaced, "# Paper\n\n## メタデータ\n\nnew metadata\n\n## Notes\n\nkeep\n")


if __name__ == "__main__":
    unittest.main()

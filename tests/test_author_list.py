from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401

from manuscript_md import author_list, csl


class AuthorListTests(unittest.TestCase):
    def test_parse_and_remap_affiliations(self) -> None:
        source = """Jane Doe,1 John Smith,1,2

1. Department A
2. Department B
"""
        parsed = author_list.parse_author_affiliations(source)
        text = author_list.build_text([source], ["Jane Doe", "John Smith"])

        self.assertEqual(parsed["Jane Doe"], ["Department A"])
        self.assertEqual(parsed["John Smith"], ["Department A", "Department B"])
        self.assertIn("Jane Doe,<sub>1</sub>", text)
        self.assertIn("John Smith,<sub>1,2</sub>", text)
        self.assertIn("<sub>1</sub> Department A", text)
        self.assertIn("<sub>2</sub> Department B", text)


class CslTests(unittest.TestCase):
    def test_resolve_csl_prefers_paper_dir_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper_dir = Path(tmp) / "paper"
            skill_dir = Path(tmp) / "skill"
            paper_dir.mkdir()
            (skill_dir / "csl").mkdir(parents=True)
            custom = paper_dir / "custom.csl"
            bundled = skill_dir / "csl" / "custom.csl"
            custom.write_text("<style/>", encoding="utf-8")
            bundled.write_text("<other/>", encoding="utf-8")

            resolved = csl.resolve_csl("custom.csl", paper_dir=paper_dir, project_dir=skill_dir)
            self.assertEqual(resolved, custom.resolve())

    def test_resolve_csl_falls_back_to_skill_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper_dir = Path(tmp) / "paper"
            skill_dir = Path(tmp) / "skill"
            paper_dir.mkdir()
            (skill_dir / "csl").mkdir(parents=True)
            bundled = skill_dir / "csl" / "vancouver.csl"
            bundled.write_text("<style/>", encoding="utf-8")

            resolved = csl.resolve_csl("vancouver.csl", paper_dir=paper_dir, project_dir=skill_dir)
            self.assertEqual(resolved, bundled.resolve())


if __name__ == "__main__":
    unittest.main()

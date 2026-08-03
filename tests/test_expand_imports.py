from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "manuscript_md" / "scripts" / "expand_imports.py"
SPEC = importlib.util.spec_from_file_location("expand_imports", SCRIPT)
assert SPEC and SPEC.loader
expand_imports = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(expand_imports)


class ExpandImportsTests(unittest.TestCase):
    def test_expand_markdown_resolves_nested_imports_relative_to_each_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "parts").mkdir()
            (base / "parts" / "methods.md").write_text(
                'Methods intro\n@import "details.md"\nMethods end\n',
                encoding="utf-8",
            )
            (base / "parts" / "details.md").write_text("Nested detail\n", encoding="utf-8")

            expanded = expand_imports.expand_markdown(
                'Title\n@import "parts/methods.md"\nTail\n',
                base,
            )

        self.assertEqual(
            expanded,
            "Title\n\nMethods intro\n\nNested detail\n\nMethods end\n\nTail\n",
        )

    def test_expand_markdown_reports_missing_import_with_source_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            with self.assertRaisesRegex(FileNotFoundError, "@import target not found: missing.md"):
                expand_imports.expand_markdown('@import "missing.md"\n', base)

    def test_expand_markdown_detects_circular_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "a.md").write_text('@import "b.md"\n', encoding="utf-8")
            (base / "b.md").write_text('@import "a.md"\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "circular @import"):
                expand_imports.expand_markdown('@import "a.md"\n', base)

    def test_normalize_table_cell_indents_only_changes_first_column_body_cells(self) -> None:
        source = "\n".join(
            [
                "| Item | Value |",
                "| --- | --- |",
                "|   Child | kept |",
                "| Parent |   second column spaces stay ascii |",
                "not a table",
            ]
        )

        normalized = expand_imports.normalize_table_cell_indents(source)

        self.assertIn("|\u2003Child | kept |", normalized)
        self.assertIn("| Parent |   second column spaces stay ascii |", normalized)
        self.assertIn("| --- | --- |", normalized)


if __name__ == "__main__":
    unittest.main()

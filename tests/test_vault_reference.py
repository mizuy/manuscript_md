from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "manuscript-reference" / "scripts" / "vault_reference.py"
SPEC = importlib.util.spec_from_file_location("vault_reference", SCRIPT)
assert SPEC and SPEC.loader
vault_reference = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = vault_reference
SPEC.loader.exec_module(vault_reference)


BIB = """@article{Smith2024,
  title = {Markdown First Reference},
  author = {Smith, Alice and Doe, Bob},
  journaltitle = {Journal of Tests},
  date = {2024-05-01},
  doi = {10.1000/test}
}
"""


class VaultReferenceTests(unittest.TestCase):
    def test_ingests_source_markdown_into_central_vault_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bib = root / "paperpile.bib"
            bib.write_text(BIB, encoding="utf-8")
            source = root / "source.md"
            source.write_text("# Extracted body\n\nPDF markdown.\n", encoding="utf-8")
            vault = root / "vault"
            meta = vault_reference.load_bib("Smith2024", bib_path=bib)

            source_written = vault_reference.write_source_markdown(
                key="Smith2024",
                vault_root=vault,
                source_md=source,
                pdf_path=None,
                overwrite=False,
            )
            note = vault_reference.write_literature_note(
                vault_root=vault,
                key="Smith2024",
                meta=meta,
                document_type="review",
                pdf_written=False,
                source_md_written=source_written,
            )

            self.assertTrue(source_written)
            self.assertEqual(
                (vault / "references" / "source_md" / "Smith2024.md").read_text(
                    encoding="utf-8"
                ),
                "# Extracted body\n\nPDF markdown.\n",
            )
            text = note.read_text(encoding="utf-8")
            self.assertIn("# Markdown First Reference", text)
            self.assertIn("- **pandoc-id:** `Smith2024`", text)
            self.assertIn("- **文献タイプ:** `review`", text)
            self.assertIn("[Smith2024.md](../source_md/Smith2024.md)", text)
            self.assertIn("## 引用方針", text)

    def test_project_note_and_keys_are_not_duplicated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / "vault"

            first = vault_reference.write_project_note(vault, "paper_lag0", "Smith2024", "Title")
            second = vault_reference.write_project_note(vault, "paper_lag0", "Smith2024", "Title")

            self.assertEqual(first, second)
            keys = (vault / "projects" / "paper_lag0" / "reference_keys.txt").read_text(
                encoding="utf-8"
            )
            self.assertEqual(keys.count("Smith2024"), 1)
            note = first.read_text(encoding="utf-8")
            self.assertIn("[@Smith2024]", note)
            self.assertIn("[[references/papers/Smith2024|Smith2024]]", note)


if __name__ == "__main__":
    unittest.main()

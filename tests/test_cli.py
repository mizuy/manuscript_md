from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lab_paper import cli  # noqa: E402


class CliTests(unittest.TestCase):
    def test_help_lists_builtin_and_script_commands(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = cli.main(["--help"])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("usage: lab-paper <command> [args]", output)
        self.assertIn("  sync-assets", output)
        self.assertIn("  vault-reference", output)
        self.assertIn("  word-count", output)

    def test_unknown_command_returns_usage_error(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = cli.main(["not-a-command"])

        self.assertEqual(exit_code, 2)
        self.assertIn("unknown command: not-a-command", stderr.getvalue())

    def test_sync_assets_copies_filters_without_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper_dir = Path(tmp) / "paper"

            first_stdout = io.StringIO()
            with redirect_stdout(first_stdout):
                first_exit = cli.sync_assets(["--paper-dir", str(paper_dir)])

            self.assertEqual(first_exit, 0)
            copied_filter = paper_dir / "script" / "filters" / "pagebreak.lua"
            self.assertTrue(copied_filter.is_file())
            original_content = copied_filter.read_text(encoding="utf-8")

            copied_filter.write_text("-- local override\n", encoding="utf-8")
            second_stdout = io.StringIO()
            with redirect_stdout(second_stdout):
                second_exit = cli.sync_assets(["--paper-dir", str(paper_dir)])

            self.assertEqual(second_exit, 0)
            self.assertEqual(copied_filter.read_text(encoding="utf-8"), "-- local override\n")
            self.assertIn("assets already up to date", second_stdout.getvalue())
            self.assertNotEqual(original_content, "")

    def test_sync_assets_optional_csl_templates_and_reference_doc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paper_dir = Path(tmp) / "paper"
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                exit_code = cli.sync_assets(
                    [
                        "--paper-dir",
                        str(paper_dir),
                        "--include-csl",
                        "--include-templates",
                        "--include-reference-doc",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue((paper_dir / "csl" / "vancouver.csl").is_file())
            self.assertTrue((paper_dir / "templates" / "manuscript_skeleton.md").is_file())
            self.assertTrue((paper_dir / "reference.docx").is_file())
            self.assertTrue((paper_dir / "script" / "filters" / "table_word.lua").is_file())
            self.assertIn(str(paper_dir / "reference.docx"), stdout.getvalue())


if __name__ == "__main__":
    unittest.main()

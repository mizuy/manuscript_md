from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401

from manuscript_md import word_count


class WordCountTests(unittest.TestCase):
    def test_count_manuscript_splits_sections_and_excludes_keywords(self) -> None:
        manuscript = """---
title: Example
---

# ABSTRACT
Short abstract text.
**Key words:** alpha beta

# Introduction
Intro prose cites [@Smith2024] and keeps words.

# Methods
![Figure](fig/a.png)
**Figure 1.** Caption words excluded.
Methods prose has five clear words.

# Results
| Item | Value |
| --- | --- |
| A | B |
Results prose remains.

# Discussion
Discussion links [ignored label](https://example.com) after cleanup.

# References
These words are outside main text.
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manuscript.md"
            path.write_text(manuscript, encoding="utf-8")

            stats = word_count.count_manuscript(path)

        self.assertEqual(stats["abstract"], 3)
        self.assertEqual(stats["abstract_including_keywords"], 7)
        self.assertEqual(stats["by_section"]["Introduction"], 6)
        self.assertEqual(stats["by_section"]["Methods"], 6)
        self.assertEqual(stats["by_section"]["Results"], 3)
        self.assertEqual(stats["by_section"]["Discussion"], 4)
        self.assertEqual(stats["main_text"], 19)
        self.assertEqual(stats["main_text_and_abstract"], 22)

    def test_clean_for_word_count_removes_common_markdown_noise(self) -> None:
        cleaned = word_count.clean_for_word_count(
            "Text [@A; @B] with **bold words**, `code`, <span>html</span>, and [a link](url)."
        )

        self.assertEqual(cleaned, "Text with bold words, , html , and .")
        self.assertEqual(word_count.count_words(cleaned), 6)

    def test_resolve_manuscript_path_prefers_explicit_path_then_paper_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            explicit = root / "custom.md"
            explicit.write_text("# Abstract\nText\n", encoding="utf-8")
            paper_dir = root / "paper"
            paper_dir.mkdir()
            default = paper_dir / "manuscript.md"
            default.write_text("# Abstract\nDefault\n", encoding="utf-8")

            self.assertEqual(word_count.resolve_manuscript_path(explicit, paper_dir), explicit.resolve())
            self.assertEqual(word_count.resolve_manuscript_path(None, paper_dir), default.resolve())


if __name__ == "__main__":
    unittest.main()

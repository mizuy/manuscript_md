#!/usr/bin/env python3
"""Character-level tracked-changes diff of two docx files (no Word needed)."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from manuscript_md.docx_diff import main
except ImportError:  # run without installing the package
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
    from manuscript_md.docx_diff import main

if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Expand ``@import "path"`` lines before pandoc."""
from __future__ import annotations

from manuscript_md.markdown import main

if __name__ == "__main__":
    raise SystemExit(main())

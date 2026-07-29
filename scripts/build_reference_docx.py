#!/usr/bin/env python3
"""Compat shim — forwards to skill script."""
from __future__ import annotations
import runpy
import sys
from pathlib import Path
TARGET = Path(__file__).resolve().parents[1] / "skills/manuscript_md/scripts/build_reference_docx.py"
sys.argv[0] = str(TARGET)
runpy.run_path(str(TARGET), run_name="__main__")

#!/usr/bin/env python3
"""Compat: load skill bib_parse into this module namespace."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_TARGET = (
    Path(__file__).resolve().parents[1]
    / "skills/manuscript-reference/scripts/bib_parse.py"
)
_spec = importlib.util.spec_from_file_location("_skill_bib_parse", _TARGET)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
globals().update({k: v for k, v in vars(_mod).items() if not k.startswith("_")})

#!/usr/bin/env bash
# Build sample old/new/diff docx for each case (needs pandoc).
# Open */diff.docx in Word to check the tracked changes.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
REF="$ROOT/skills/manuscript_md/templates/reference.docx"
for dir in "$HERE"/[0-9]*/; do
  dir="${dir%/}"
  pandoc "$dir/old.md" --resource-path "$dir" -o "$dir/old.docx"
  pandoc "$dir/new.md" --resource-path "$dir" --reference-doc "$REF" -o "$dir/new.docx"
  PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m manuscript_md.cli diff-docx "$dir/old.docx" "$dir/new.docx" "$dir/diff.docx"
done

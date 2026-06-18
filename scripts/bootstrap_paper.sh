#!/usr/bin/env bash
# Bootstrap a paper directory from lab-paper templates.
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bootstrap_paper.sh <paper_dir> [output_parent_dir] [csl_name]" >&2
  echo "  Creates <output_parent_dir>/<paper_dir>/" >&2
  echo "  csl_name defaults to vancouver.csl (must exist in lab-paper csl/)" >&2
  exit 1
fi

NAME="$1"
PARENT="${2:-docs}"
CSL="${3:-vancouver.csl}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$(cd "$PARENT" 2>/dev/null && pwd)/${NAME}" || DEST="${PARENT}/${NAME}"
CSL_BASENAME="$(basename "$CSL")"

if [[ -e "$DEST" ]]; then
  echo "Already exists: $DEST" >&2
  exit 1
fi

if [[ ! -f "$PROJECT_DIR/csl/$CSL_BASENAME" ]]; then
  echo "CSL not found in lab-paper: $PROJECT_DIR/csl/$CSL_BASENAME" >&2
  echo "Available:" >&2
  ls "$PROJECT_DIR/csl/"*.csl 2>/dev/null | xargs -n1 basename >&2 || true
  exit 1
fi

mkdir -p \
  "$DEST/fig" \
  "$DEST/script/filters" \
  "$DEST/reference/md" \
  "$DEST/reference/pdf"

cp "$PROJECT_DIR/templates/manuscript_skeleton.md" "$DEST/manuscript.md"
cp "$PROJECT_DIR/templates/supplementary_skeleton.md" "$DEST/supplementary.md"
cp "$PROJECT_DIR/templates/manual_entries.example.bib" "$DEST/manual_entries.bib"
cp "$PROJECT_DIR/templates/reference.docx" "$DEST/reference.docx"
cp "$PROJECT_DIR/csl/$CSL_BASENAME" "$DEST/$CSL_BASENAME"
cp "$PROJECT_DIR/filters/pagebreak.lua" "$DEST/script/filters/pagebreak.lua"
cp "$PROJECT_DIR/filters/landscape.lua" "$DEST/script/filters/landscape.lua"
cp "$PROJECT_DIR/filters/table_word.lua" "$DEST/script/filters/table_word.lua"
cp "$PROJECT_DIR/filters/superscript.lua" "$DEST/script/filters/superscript.lua"
cp "$PROJECT_DIR/templates/fig_README.md" "$DEST/fig/README.md"
cp "$PROJECT_DIR/templates/script_README.md" "$DEST/script/README.md"
cp "$PROJECT_DIR/templates/reference_README.md" "$DEST/reference/README.md"
cp "$PROJECT_DIR/templates/reference_note_template.md" "$DEST/reference/_template.md"
cp "$PROJECT_DIR/templates/reference_keys.example.txt" "$DEST/reference/reference_keys.txt"

if [[ "$CSL_BASENAME" != "vancouver.csl" ]]; then
  sed -i '' "s/^csl: .*/csl: $CSL_BASENAME/" "$DEST/manuscript.md" "$DEST/supplementary.md" 2>/dev/null \
    || sed -i "s/^csl: .*/csl: $CSL_BASENAME/" "$DEST/manuscript.md" "$DEST/supplementary.md"
fi

echo "Created $DEST (csl: $CSL_BASENAME)"
echo "Layout: /Users/mizuy/lab/paper/docs/PAPER_LAYOUT.md"
echo "Next:"
echo "  1) [@pandoc-id] in manuscript.md"
echo "  2) task paper:build-bib PAPER_DIR=$DEST"
echo "  3) pandoc with script/filters/*.lua (see script/README.md or Taskfile.paper.example.yml)"

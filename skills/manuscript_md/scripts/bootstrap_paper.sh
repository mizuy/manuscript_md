#!/usr/bin/env bash
# Bootstrap a minimal paper directory (no vendored filters/scripts).
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bootstrap_paper.sh <paper_dir> [output_parent_dir] [csl_name]" >&2
  echo "  Creates <output_parent_dir>/<paper_dir>/" >&2
  echo "  csl_name defaults to vancouver.csl (must exist in skill csl/)" >&2
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
  echo "CSL not found: $PROJECT_DIR/csl/$CSL_BASENAME" >&2
  echo "Available:" >&2
  ls "$PROJECT_DIR/csl/"*.csl 2>/dev/null | xargs -n1 basename >&2 || true
  exit 1
fi

mkdir -p \
  "$DEST/fig" \
  "$DEST/table" \
  "$DEST/reference/md" \
  "$DEST/reference/pdf"

cp "$PROJECT_DIR/templates/manuscript_skeleton.md" "$DEST/manuscript.md"
cp "$PROJECT_DIR/templates/supplementary_skeleton.md" "$DEST/supplementary.md"
cp "$PROJECT_DIR/templates/manual_entries.example.bib" "$DEST/manual_entries.bib"
cp "$PROJECT_DIR/templates/fig_README.md" "$DEST/fig/README.md"
cp "$PROJECT_DIR/templates/reference_README.md" "$DEST/reference/README.md"
cp "$PROJECT_DIR/templates/reference_note_template.md" "$DEST/reference/_template.md"
cp "$PROJECT_DIR/templates/reference_keys.example.txt" "$DEST/reference/reference_keys.txt"
# reference.docx + CSL stay in the skill (resolve at build time)

# CSL ships in the skill; only set front-matter name (no paper-local copy).
if [[ "$CSL_BASENAME" != "vancouver.csl" ]]; then
  sed -i '' "s/^csl: .*/csl: $CSL_BASENAME/" "$DEST/manuscript.md" "$DEST/supplementary.md" 2>/dev/null \
    || sed -i "s/^csl: .*/csl: $CSL_BASENAME/" "$DEST/manuscript.md" "$DEST/supplementary.md"
fi

cat > "$DEST/README.md" <<EOF
# ${NAME}

Build with manuscript_md (filters/CSL live in the skill — not vendored here):

\`\`\`bash
cd /Users/mizuy/lab/manuscript_md
task paper:docx PAPER_DIR=\$(pwd)/${DEST#$PWD/} PAPER_CSL=${CSL_BASENAME}
\`\`\`

Layout: /Users/mizuy/lab/manuscript_md/docs/PAPER_LAYOUT.md
EOF

echo "Created $DEST (csl name: $CSL_BASENAME; skill provides the file)"
echo "Next:"
echo "  1) [@pandoc-id] in manuscript.md"
echo "  2) task paper:docx PAPER_DIR=$DEST PAPER_CSL=$CSL_BASENAME"

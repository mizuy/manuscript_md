#!/usr/bin/env bash
# Compare two .docx files with Microsoft Word (macOS).
# Paths must live under a local folder Word can access (not /tmp).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: compare_docx.sh [OPTIONS] BASE.docx CHANGED.docx [OUTPUT.docx]

Options:
  --format   Track style/formatting changes in the diff

  BASE.docx     Original document (e.g. collaborator's Word edit)
  CHANGED.docx  Revised document (e.g. pandoc output from manuscript.md)
  OUTPUT.docx   Optional. Save tracked-changes result; omit to leave open in Word.

By default, revised formatting is applied to the comparison document, but
formatting-only revision markup is removed so only text/content
revisions remain visible. Use --format to keep formatting revisions visible.
EOF
}

DETECT_FORMAT="false"
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --format)
      DETECT_FORMAT="true"
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
CHANGED="$(cd "$(dirname "$2")" && pwd)/$(basename "$2")"
OUTPUT="${3:-}"
OPEN_PREVIEW="false"

if [[ ! -f "$BASE" ]]; then
  echo "Base file not found: $BASE" >&2
  exit 1
fi
if [[ ! -f "$CHANGED" ]]; then
  echo "Changed file not found: $CHANGED" >&2
  exit 1
fi
if [[ ( -z "$OUTPUT" || "$OUTPUT" == "-" ) && "$DETECT_FORMAT" == "false" ]]; then
  PREVIEW_DIR="$(dirname "$CHANGED")/.compare"
  mkdir -p "$PREVIEW_DIR"
  OUTPUT="$PREVIEW_DIR/compare_preview_$$.docx"
  OPEN_PREVIEW="true"
fi
if [[ -n "$OUTPUT" && "$OUTPUT" != "-" ]]; then
  OUTPUT="$(cd "$(dirname "$OUTPUT")" && pwd)/$(basename "$OUTPUT")"
  mkdir -p "$(dirname "$OUTPUT")"
fi

WORD_DETECT_FORMAT="$DETECT_FORMAT"
if [[ "$DETECT_FORMAT" == "false" ]]; then
  WORD_DETECT_FORMAT="true"
fi

osascript "$SCRIPT_DIR/compare_docx.applescript" \
  "$BASE" "$CHANGED" "$OUTPUT" "$WORD_DETECT_FORMAT"

if [[ "$DETECT_FORMAT" == "false" ]]; then
  python3 "$SCRIPT_DIR/apply_formatting_without_tracking.py" "$OUTPUT"
fi

if [[ "$OPEN_PREVIEW" == "true" ]]; then
  open -a "Microsoft Word" "$OUTPUT"
  echo "Opened $OUTPUT"
elif [[ -n "$OUTPUT" && "$OUTPUT" != "-" ]]; then
  echo "Wrote $OUTPUT"
fi

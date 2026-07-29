#!/usr/bin/env bash
# Regenerate Word Compare diff from versions/manifest.yml (macOS + Word).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: PAPER_DIR=/path/to/paper diff_version.sh [ENTRY_ID]

Uses version_manifest.py resolve-diff + compare_docx.sh.
Optional ENTRY selects a manifest entry; default is the latest internal version.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

ENTRY="${1:-}"

if [[ -z "${PAPER_DIR:-}" ]]; then
  echo "PAPER_DIR is required." >&2
  usage >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(cd "$PAPER_DIR" && pwd)"
MANIFEST="${MANIFEST:-manifest.yml}"

run_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    eval "$PYTHON \"\$@\""
  else
    python3 "$@"
  fi
}

skill_root="$(cd "$SCRIPT_DIR/.." && pwd)"
manuscript_root="$(cd "$skill_root/../.." && pwd)"
helper=""
for candidate in \
  "${PAPER_PROJECT:-}/skills/manuscript_md/scripts/version_manifest.py" \
  "${PAPER_PROJECT:-}/scripts/version_manifest.py" \
  "$skill_root/../manuscript_md/scripts/version_manifest.py" \
  "$manuscript_root/scripts/version_manifest.py"; do
  if [[ -n "$candidate" && -f "$candidate" ]]; then
    helper="$candidate"
    break
  fi
done
if [[ -z "$helper" ]]; then
  echo "version_manifest.py not found" >&2
  exit 1
fi

args=(resolve-diff --paper-dir "$PAPER_DIR" --manifest "$MANIFEST" --json)
if [[ -n "$ENTRY" ]]; then
  args+=(--entry "$ENTRY")
fi
json="$(run_python "$helper" "${args[@]}")"
BASE="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["base"])' <<<"$json")"
CHANGED="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["target"])' <<<"$json")"
OUTPUT="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["diff"])' <<<"$json")"
BASE_ID="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["base_id"])' <<<"$json")"
ENTRY_ID="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["entry_id"])' <<<"$json")"

echo "Diff: ${BASE_ID} -> ${ENTRY_ID}"
echo "  BASE:    $BASE"
echo "  CHANGED: $CHANGED"
echo "  OUTPUT:  $OUTPUT"
chmod +x "$SCRIPT_DIR/compare_docx.sh"
"$SCRIPT_DIR/compare_docx.sh" "$BASE" "$CHANGED" "$OUTPUT"

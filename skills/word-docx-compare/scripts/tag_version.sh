#!/usr/bin/env bash
# Tag a docx version and diff against the previous version (macOS + Microsoft Word).
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: PAPER_DIR=/path/to/paper tag_version.sh VERSION [SOURCE.docx]

Environment:
  PAPER_DIR         Paper directory (required). versions/ is created under it.
  VERSION_PREFIX    Filename prefix when manifest.yml is absent (default: ADR_manuscript)
  PAPER_PROJECT     Path to manuscript_md checkout for version_manifest.py (optional)

If versions/manifest.yml exists, TARGET / diff BASE come from the manifest.
Otherwise falls back to ${PREFIX}_v{N}.docx vs ${PREFIX}_v{N-1}.docx.

When this skill lives at skills/word-docx-compare/, version_manifest.py is
resolved from the manuscript_md project root (two levels above this skill).

Writes:
  $PAPER_DIR/versions/${PREFIX}_v{N}.docx   (or manifest entry file)
  $PAPER_DIR/versions/${PREFIX}_v{N}_diff.docx   (when a base resolves)
EOF
}

if [[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

VERSION="$1"
SOURCE="${2:-manuscript.docx}"

if [[ -z "${PAPER_DIR:-}" ]]; then
  echo "PAPER_DIR is required." >&2
  usage >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAPER_DIR="$(cd "$PAPER_DIR" && pwd)"
VERSIONS_DIR="$PAPER_DIR/versions"
mkdir -p "$VERSIONS_DIR"

SOURCE="$(cd "$(dirname "$SOURCE")" && pwd)/$(basename "$SOURCE")"
if [[ ! -f "$SOURCE" ]]; then
  echo "Source file not found: $SOURCE" >&2
  exit 1
fi

run_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    # PYTHON may include env assignments (e.g. uv run python from Taskfile).
    eval "$PYTHON \"\$@\""
  else
    python3 "$@"
  fi
}

resolve_from_manifest() {
  local helper=""
  local skill_root manuscript_root
  # scripts/ -> word-docx-compare/ -> skills/ -> manuscript_md root
  skill_root="$(cd "$SCRIPT_DIR/.." && pwd)"
  manuscript_root="$(cd "$skill_root/../.." && pwd)"
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

  if [[ -z "$helper" ]] || [[ ! -f "$VERSIONS_DIR/manifest.yml" ]]; then
    return 1
  fi

  local json
  if ! json="$(run_python "$helper" resolve-tag --paper-dir "$PAPER_DIR" --version "$VERSION" --source "$SOURCE" --json)"; then
    echo "Failed to resolve manifest for version ${VERSION}." >&2
    exit 1
  fi

  TARGET="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["target"])' <<<"$json")"
  DIFF="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["diff"])' <<<"$json")"
  BASE="$(run_python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("base",""))' <<<"$json")"
  BASE_ID="$(run_python -c 'import json,sys; d=json.load(sys.stdin); print(d.get("base_id",""))' <<<"$json")"
  ENTRY_ID="$(run_python -c 'import json,sys; print(json.load(sys.stdin)["entry_id"])' <<<"$json")"
  return 0
}

if resolve_from_manifest; then
  cp "$SOURCE" "$TARGET"
  echo "Wrote $TARGET (manifest entry ${ENTRY_ID})"
else
  PREFIX="${VERSION_PREFIX:-ADR_manuscript}"
  if ! [[ "$VERSION" =~ ^[0-9]+$ ]] || [[ "$VERSION" -lt 1 ]]; then
    echo "VERSION must be a positive integer without manifest: $VERSION" >&2
    exit 1
  fi
  TARGET="$VERSIONS_DIR/${PREFIX}_v${VERSION}.docx"
  DIFF="$VERSIONS_DIR/${PREFIX}_v${VERSION}_diff.docx"
  cp "$SOURCE" "$TARGET"
  echo "Wrote $TARGET"

  find_prev_version() {
    local n="$1"
    local candidate
    for candidate in \
      "$VERSIONS_DIR/${PREFIX}_v${n}.docx" \
      "$PAPER_DIR/${PREFIX}_v${n}.docx"; do
      if [[ -f "$candidate" ]]; then
        echo "$candidate"
        return 0
      fi
    done
    return 1
  }

  PREV_VERSION=$((VERSION - 1))
  if [[ "$PREV_VERSION" -ge 1 ]]; then
    if PREV_PATH="$(find_prev_version "$PREV_VERSION")"; then
      BASE="$PREV_PATH"
      BASE_ID="v${PREV_VERSION}"
    else
      BASE=""
    fi
  fi
fi

if [[ -n "${BASE:-}" ]]; then
  if [[ ! -f "$BASE" ]]; then
    echo "Diff base not found: $BASE" >&2
    exit 1
  fi
  chmod +x "$SCRIPT_DIR/compare_docx.sh"
  echo "Comparing ${BASE_ID:-base} -> $(basename "$TARGET")"
  "$SCRIPT_DIR/compare_docx.sh" "$BASE" "$TARGET" "$DIFF"
else
  echo "No diff base resolved; skipped diff." >&2
fi

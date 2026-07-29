#!/usr/bin/env bash
# Compat shim → skills/manuscript_md/scripts/bootstrap_paper.sh
exec "$(cd "$(dirname "$0")/.." && pwd)/skills/manuscript_md/scripts/bootstrap_paper.sh" "$@"

#!/usr/bin/env bash
# Quick POLKE health check.
set -euo pipefail

URL="${POLKE_URL:-http://localhost}"
TEXT="${1:-I work in a supermarket.}"

PYTHONPATH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" \
  python3 "$(dirname "${BASH_SOURCE[0]}")/../tag_sentence.py" "$TEXT" --polke-url "$URL"

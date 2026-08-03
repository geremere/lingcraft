#!/usr/bin/env bash
# Stop local POLKE containers.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${SCRIPT_DIR}/vendor/polke"

if [[ ! -f "${VENDOR_DIR}/stop.sh" ]]; then
  echo "POLKE not installed. Nothing to stop." >&2
  exit 0
fi

cd "${VENDOR_DIR}"
./stop.sh

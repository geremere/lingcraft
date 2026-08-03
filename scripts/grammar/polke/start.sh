#!/usr/bin/env bash
# Start local POLKE (Docker + Jetty). First run builds the image — may take several minutes.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${SCRIPT_DIR}/vendor/polke"

if [[ ! -d "${VENDOR_DIR}" ]]; then
  bash "${SCRIPT_DIR}/setup.sh"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop and retry." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start Docker Desktop and retry." >&2
  exit 1
fi

cd "${VENDOR_DIR}"
echo "Starting POLKE from ${VENDOR_DIR} ..."
echo "API will be at: http://localhost/extractor"
echo "Press Ctrl+C to stop log follow (containers keep running)."
echo ""

exec ./serve.sh

#!/usr/bin/env bash
# Clone POLKE upstream into vendor/ if missing.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENDOR_DIR="${SCRIPT_DIR}/vendor/polke"
REPO_URL="https://github.com/chxiaobin/polke.git"

if [[ -d "${VENDOR_DIR}/.git" ]]; then
  echo "POLKE already cloned at ${VENDOR_DIR}"
  exit 0
fi

mkdir -p "${SCRIPT_DIR}/vendor"
echo "Cloning POLKE → ${VENDOR_DIR}"
git clone --depth 1 "${REPO_URL}" "${VENDOR_DIR}"
echo "Done. Run: bash scripts/grammar/polke/start.sh"

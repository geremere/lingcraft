#!/usr/bin/env python3
"""Audit which EGP constructs have POLKE Ruta rules (ground truth from vendor/polke)."""

from __future__ import annotations

import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VENDOR_POLKE = SCRIPT_DIR / "polke" / "vendor" / "polke"
OUT = SCRIPT_DIR / "registry" / "polke_supported.json"


def extract_ruta_ids(polke_dir: Path) -> set[int]:
    ruta_dir = polke_dir / "src/main/resources/ruta/script"
    ids: set[int] = set()
    for path in ruta_dir.glob("*.ruta"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        ids.update(int(m.group(1)) for m in re.finditer(r'constructID"\s*=\s*(\d+)', text))
    return ids


def main() -> int:
    if not VENDOR_POLKE.exists():
        raise SystemExit(
            f"POLKE vendor not found at {VENDOR_POLKE}. "
            "Run: bash scripts/grammar/polke/setup.sh"
        )

    supported = sorted(extract_ruta_ids(VENDOR_POLKE))
    payload = {
        "source": "polke ruta rules",
        "vendor_path": str(VENDOR_POLKE),
        "polke_supported_count": len(supported),
        "polke_supported_ids": supported,
    }
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(supported)} constructs with POLKE rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

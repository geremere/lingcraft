"""Shared EGP registry helpers."""

from __future__ import annotations

import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "registry" / "egp_en.json"


def load_constructs(path: Path | None = None) -> list[dict]:
    registry_path = path or REGISTRY_PATH
    if not registry_path.exists():
        raise FileNotFoundError(
            f"Registry not found: {registry_path}. "
            "Run: PYTHONPATH=scripts python3 scripts/grammar/import_egp.py --download"
        )
    with registry_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["constructs"]

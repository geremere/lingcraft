"""Shared EGP registry helpers."""

from __future__ import annotations

import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "registry" / "egp_en.json"
POLKE_SUPPORTED_PATH = Path(__file__).resolve().parent / "registry" / "polke_supported.json"


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


def load_polke_supported_ids(path: Path | None = None) -> set[int]:
    """EGP construct IDs with a POLKE Ruta rule (from vendor/polke audit)."""
    supported_path = path or POLKE_SUPPORTED_PATH
    if not supported_path.exists():
        raise FileNotFoundError(
            f"POLKE coverage file not found: {supported_path}. "
            "Run: python3 scripts/grammar/audit_polke_coverage.py"
        )
    with supported_path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return set(payload["polke_supported_ids"])

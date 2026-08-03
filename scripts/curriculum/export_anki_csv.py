#!/usr/bin/env python3
"""Export EAQUALS curriculum items to Anki-compatible CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml

CURRICULUM_DIR = Path(__file__).resolve().parent
INVENTORY = CURRICULUM_DIR / "eaquals_core_inventory.json"
MAPPING = CURRICULUM_DIR / "eaquals_egp_mapping.yaml"
DEFAULT_OUT = CURRICULUM_DIR / "eaquals_anki.csv"


def load_mapping() -> dict[str, list[str]]:
    if not MAPPING.exists():
        return {}
    data = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    return {
        row["eaquals_id"]: [ref["ref"] for ref in row.get("egp_refs", [])]
        for row in data.get("mappings", [])
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export EAQUALS items to Anki CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--domain", action="append", help="Filter domain(s): grammar, functions, lexis, topics, discourse")
    args = parser.parse_args()

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    egp_by_id = load_mapping()
    domains = args.domain or list(inventory["domains"].keys())

    rows: list[tuple[str, str, str]] = []
    for domain in domains:
        for item in inventory["domains"].get(domain, []):
            for level in item["levels"]:
                front = f"{level} {domain}: {item['title']}"
                refs = egp_by_id.get(item["id"], [])
                back_parts = []
                if item.get("examples"):
                    back_parts.append("\n".join(f"• {ex}" for ex in item["examples"][:3]))
                if refs:
                    back_parts.append("EGP: " + ", ".join(refs[:10]))
                back = "\n\n".join(back_parts)
                tags = f"eaquals {domain} {level}"
                rows.append((front, back, tags))

    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Front", "Back", "Tags"])
        writer.writerows(rows)

    print(f"Wrote {len(rows)} cards → {args.output}")


if __name__ == "__main__":
    main()

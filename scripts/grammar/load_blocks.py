#!/usr/bin/env python3
"""Load grammar block packages from disk into grammar_blocks table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from grammar.db import db_connect

SCRIPT_DIR = Path(__file__).resolve().parent
BLOCKS_DIR = SCRIPT_DIR / "blocks"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load block.yaml files into grammar_blocks")
    parser.add_argument("--lang", default="en", help="Language code (matches blocks/{lang}/)")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def iter_blocks(lang: str) -> list[tuple[Path, dict]]:
    root = BLOCKS_DIR / lang
    if not root.exists():
        raise FileNotFoundError(f"No blocks at {root}")
    rows: list[tuple[Path, dict]] = []
    for block_path in sorted(root.glob("*/*/block.yaml")):
        rows.append((block_path, yaml.safe_load(block_path.read_text(encoding="utf-8"))))
    return rows


def main() -> None:
    args = parse_args()
    blocks = iter_blocks(args.lang)
    if not blocks:
        raise SystemExit("No block.yaml files found")

    sql = """
        INSERT INTO grammar_blocks (
            language_id, slug, level, title, category, super_category,
            sub_category, sort_order, metadata_json
        )
        SELECT l.id, %(slug)s, %(level)s, %(title)s, %(category)s, %(super_category)s,
               %(sub_category)s, %(sort_order)s, %(metadata_json)s::jsonb
        FROM languages l
        WHERE l.code = %(lang)s
        ON CONFLICT (language_id, slug) DO UPDATE SET
            level = EXCLUDED.level,
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            super_category = EXCLUDED.super_category,
            sub_category = EXCLUDED.sub_category,
            sort_order = EXCLUDED.sort_order,
            metadata_json = EXCLUDED.metadata_json
    """

    with db_connect() as conn:
        with conn.cursor() as cur:
            for path, block in blocks:
                examples_path = path.parent / "examples.json"
                example_count = 0
                if examples_path.exists():
                    example_count = len(json.loads(examples_path.read_text(encoding="utf-8")).get("examples", []))

                payload = {
                    "lang": args.lang,
                    "slug": block["slug"],
                    "level": block["level"],
                    "title": block["title"],
                    "category": block["category"],
                    "super_category": block["super_category"],
                    "sub_category": block["sub_category"],
                    "sort_order": block.get("sort_order", 0),
                    "metadata_json": json.dumps(
                        {
                            "source_path": str(path.relative_to(SCRIPT_DIR.parent.parent)),
                            "merged_sub_categories": block.get("merged_sub_categories", []),
                            "detectability": block.get("detectability", {}),
                            "split": block.get("split"),
                            "construct_count": block.get("construct_count"),
                            "example_count": example_count,
                        }
                    ),
                }
                if args.dry_run:
                    print(f"would load {block['slug']} ({block['level']})")
                else:
                    cur.execute(sql, payload)
            if not args.dry_run:
                conn.commit()

    print(f"{'Would load' if args.dry_run else 'Loaded'} {len(blocks)} grammar blocks")


if __name__ == "__main__":
    main()

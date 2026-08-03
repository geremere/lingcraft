#!/usr/bin/env python3
"""Load all EGP grammar constructs from registry into grammar_constructs table."""

from __future__ import annotations

import argparse
import json
import sys

from grammar.db import db_connect
from grammar.egp_registry import load_constructs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load EGP tags into grammar_constructs")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    parser.add_argument("--registry", default=None, help="Path to egp_en.json")
    parser.add_argument("--dry-run", action="store_true", help="Print counts only")
    return parser.parse_args()


def ensure_language(conn, code: str) -> int:
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM languages WHERE code = %s", (code,))
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO languages (code, name) VALUES (%s, %s) RETURNING id",
            (code, "English" if code == "en" else code.upper()),
        )
        return cur.fetchone()[0]


def upsert_constructs(conn, language_id: int, constructs: list[dict]) -> tuple[int, int]:
    inserted = 0
    updated = 0
    sql = """
        INSERT INTO grammar_constructs (
            language_id, egp_id, tag, slug, level,
            super_category, sub_category, guideword, can_do,
            detectability, detection, examples_json
        ) VALUES (
            %(language_id)s, %(egp_id)s, %(tag)s, %(slug)s, %(level)s,
            %(super_category)s, %(sub_category)s, %(guideword)s, %(can_do)s,
            %(detectability)s, %(detection)s, %(examples_json)s::jsonb
        )
        ON CONFLICT (language_id, egp_id) DO UPDATE SET
            tag = EXCLUDED.tag,
            slug = EXCLUDED.slug,
            level = EXCLUDED.level,
            super_category = EXCLUDED.super_category,
            sub_category = EXCLUDED.sub_category,
            guideword = EXCLUDED.guideword,
            can_do = EXCLUDED.can_do,
            detectability = EXCLUDED.detectability,
            detection = EXCLUDED.detection,
            examples_json = EXCLUDED.examples_json
        RETURNING (xmax = 0) AS inserted
    """
    with conn.cursor() as cur:
        for item in constructs:
            cur.execute(
                sql,
                {
                    "language_id": language_id,
                    "egp_id": item["egp_id"],
                    "tag": item["tag"],
                    "slug": item["slug"],
                    "level": item["level"],
                    "super_category": item["super_category"],
                    "sub_category": item["sub_category"],
                    "guideword": item["guideword"],
                    "can_do": item["can_do"],
                    "detectability": item["detectability"],
                    "detection": item["detection"],
                    "examples_json": json.dumps(item.get("examples", [])),
                },
            )
            if cur.fetchone()[0]:
                inserted += 1
            else:
                updated += 1
    return inserted, updated


def main() -> int:
    args = parse_args()
    registry_path = None
    if args.registry:
        from pathlib import Path

        registry_path = Path(args.registry)

    constructs = load_constructs(registry_path)
    print(f"Loaded {len(constructs)} constructs from registry")

    if args.dry_run:
        return 0

    with db_connect() as conn:
        language_id = ensure_language(conn, args.language)
        inserted, updated = upsert_constructs(conn, language_id, constructs)
        conn.commit()
        print(f"grammar_constructs: inserted={inserted}, updated={updated}, language_id={language_id}")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM grammar_constructs WHERE language_id = %s",
                (language_id,),
            )
            total = cur.fetchone()[0]
        print(f"Total constructs in DB for '{args.language}': {total}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

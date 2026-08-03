#!/usr/bin/env python3
"""Tag sentences from PostgreSQL via POLKE; write results to JSON or CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from grammar.db import db_connect
from grammar.egp_registry import load_constructs, load_polke_supported_ids
from grammar.polke.client import PolkeClient, PolkeError, construct_tag


@dataclass
class SentenceRow:
    id: int
    text: str


@dataclass
class TagRow:
    sentence_id: int
    text: str
    tags: list[str] = field(default_factory=list)
    source: str = "polke"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tag sentences via POLKE → JSON/CSV")
    parser.add_argument("--language", default="en", help="Language code filter (default: en)")
    parser.add_argument("--limit", type=int, default=None, help="Max sentences to process")
    parser.add_argument("--batch-size", type=int, default=100, help="DB fetch batch size")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("tags.json"),
        help="Output file (.json or .csv)",
    )
    parser.add_argument("--polke-url", default=None, help="POLKE base URL (default: POLKE_URL env)")
    parser.add_argument(
        "--skip-unknown",
        action="store_true",
        help="Drop tags not in registry/egp_en.json",
    )
    parser.add_argument(
        "--polke-supported-only",
        action="store_true",
        help="With --skip-unknown, keep only tags in polke_supported.json (~658)",
    )
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="Reserved: write to sentence_tags table (not implemented)",
    )
    return parser.parse_args()


def load_known_tags(*, polke_supported_only: bool = False) -> set[str]:
    constructs = load_constructs()
    if polke_supported_only:
        supported_ids = load_polke_supported_ids()
        constructs = [item for item in constructs if item["egp_id"] in supported_ids]
    return {item["tag"] for item in constructs}


def fetch_sentences(
    conn,
    *,
    language: str,
    batch_size: int,
    offset: int,
) -> list[SentenceRow]:
    query = """
        SELECT s.id, s.text
        FROM sentences s
        JOIN languages l ON l.id = s.language_id
        WHERE l.code = %(language)s
        ORDER BY s.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    with conn.cursor() as cur:
        cur.execute(query, {"language": language, "limit": batch_size, "offset": offset})
        return [SentenceRow(id=row[0], text=row[1]) for row in cur.fetchall()]


def filter_tags(tags: set[str], known_tags: set[str] | None, skip_unknown: bool) -> list[str]:
    if skip_unknown and known_tags is not None:
        tags = {tag for tag in tags if tag in known_tags}
    return sorted(tags)


def write_json(path: Path, rows: list[TagRow]) -> None:
    payload = {
        "source": "polke",
        "row_count": len(rows),
        "rows": [
            {
                "sentence_id": row.sentence_id,
                "text": row.text,
                "tags": row.tags,
                "source": row.source,
            }
            for row in rows
        ],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[TagRow]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["sentence_id", "text", "tags"])
        for row in rows:
            writer.writerow([row.sentence_id, row.text, "|".join(row.tags)])


def main() -> int:
    args = parse_args()
    if args.write_db:
        print("--write-db is reserved for a future migration; use --output instead.", file=sys.stderr)
        return 1

    client = PolkeClient(base_url=args.polke_url)
    if not client.health_check():
        print("POLKE health check failed.", file=sys.stderr)
        print("Start POLKE: bash scripts/grammar/polke/start.sh", file=sys.stderr)
        return 1

    if args.polke_supported_only and not args.skip_unknown:
        print("--polke-supported-only requires --skip-unknown", file=sys.stderr)
        return 1

    known_tags: set[str] | None = None
    if args.skip_unknown:
        known_tags = load_known_tags(polke_supported_only=args.polke_supported_only)
        source = "egp_en.json ∩ polke_supported.json" if args.polke_supported_only else "egp_en.json"
        print(f"Loaded {len(known_tags)} tags from {source}")

    results: list[TagRow] = []
    processed = 0
    unknown_tags: set[str] = set()
    offset = 0

    with db_connect() as conn:
        while True:
            if args.limit is not None and processed >= args.limit:
                break

            fetch_limit = args.batch_size
            if args.limit is not None:
                fetch_limit = min(fetch_limit, args.limit - processed)

            sentences = fetch_sentences(
                conn,
                language=args.language,
                batch_size=fetch_limit,
                offset=offset,
            )
            if not sentences:
                break

            for sentence in sentences:
                if args.limit is not None and processed >= args.limit:
                    break

                try:
                    annotations = client.annotate(sentence.text)
                except PolkeError as exc:
                    print(f"sentence_id={sentence.id}: {exc}", file=sys.stderr)
                    processed += 1
                    continue

                raw_tags = {construct_tag(ann.construct_id) for ann in annotations}
                if known_tags is not None:
                    unknown_tags.update(raw_tags - known_tags)
                tags = filter_tags(raw_tags, known_tags, args.skip_unknown)
                results.append(TagRow(sentence_id=sentence.id, text=sentence.text, tags=tags))
                processed += 1

            offset += len(sentences)
            print(f"Fetched batch: processed={processed}")

    suffix = args.output.suffix.lower()
    if suffix == ".csv":
        write_csv(args.output, results)
    else:
        write_json(args.output, results)

    if unknown_tags:
        print(f"Skipped {len(unknown_tags)} unknown tags", file=sys.stderr)

    print(f"Wrote {len(results)} rows → {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

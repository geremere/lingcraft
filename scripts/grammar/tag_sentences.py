#!/usr/bin/env python3
"""Tag sentences in PostgreSQL using POLKE and write sentence_tags."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from grammar.db import db_connect
from grammar.polke.client import PolkeClient, PolkeError, construct_tag


@dataclass
class SentenceRow:
    id: int
    text: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tag sentences via POLKE → sentence_tags")
    parser.add_argument("--language", default="en", help="Language code filter (default: en)")
    parser.add_argument("--limit", type=int, default=None, help="Max sentences to process")
    parser.add_argument("--batch-size", type=int, default=100, help="DB fetch/commit batch size")
    parser.add_argument("--dry-run", action="store_true", help="Print tags without writing to DB")
    parser.add_argument("--reprocess", action="store_true", help="Re-tag sentences that already have tags")
    parser.add_argument("--polke-url", default=None, help="POLKE base URL (default: POLKE_URL env)")
    parser.add_argument(
        "--skip-unknown",
        action="store_true",
        help="Skip tags not present in grammar_constructs (recommended after load_egp_tags.py)",
    )
    return parser.parse_args()


def load_known_tags(conn, language: str) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT gc.tag
            FROM grammar_constructs gc
            JOIN languages l ON l.id = gc.language_id
            WHERE l.code = %s
            """,
            (language,),
        )
        return {row[0] for row in cur.fetchall()}


def fetch_sentences(
    conn,
    *,
    language: str,
    batch_size: int,
    offset: int,
    reprocess: bool,
) -> list[SentenceRow]:
    skip_clause = ""
    if not reprocess:
        skip_clause = """
          AND NOT EXISTS (
            SELECT 1 FROM sentence_tags st WHERE st.sentence_id = s.id
          )
        """

    query = f"""
        SELECT s.id, s.text
        FROM sentences s
        JOIN languages l ON l.id = s.language_id
        WHERE l.code = %(language)s
        {skip_clause}
        ORDER BY s.id
        LIMIT %(limit)s OFFSET %(offset)s
    """
    with conn.cursor() as cur:
        cur.execute(query, {"language": language, "limit": batch_size, "offset": offset})
        return [SentenceRow(id=row[0], text=row[1]) for row in cur.fetchall()]


def delete_tags(conn, sentence_ids: list[int]) -> None:
    if not sentence_ids:
        return
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM sentence_tags WHERE sentence_id = ANY(%s)",
            (sentence_ids,),
        )


def insert_tags_batch(conn, rows: list[tuple[int, str, float]]) -> int:
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO sentence_tags (sentence_id, tag, confidence)
            VALUES (%s, %s, %s)
            """,
            rows,
        )
    return len(rows)


def filter_tags(tags: set[str], known_tags: set[str] | None, skip_unknown: bool) -> set[str]:
    if not skip_unknown or known_tags is None:
        return tags
    return {tag for tag in tags if tag in known_tags}


def main() -> int:
    args = parse_args()
    client = PolkeClient(base_url=args.polke_url)

    if not client.health_check():
        print("POLKE health check failed.", file=sys.stderr)
        print("Start POLKE: bash scripts/grammar/polke/start.sh", file=sys.stderr)
        return 1

    processed = 0
    tags_written = 0
    unknown_tags: set[str] = set()
    offset = 0

    with db_connect() as conn:
        known_tags: set[str] | None = None
        if args.skip_unknown:
            known_tags = load_known_tags(conn, args.language)
            if not known_tags:
                print(
                    "grammar_constructs is empty. Run load_egp_tags.py first.",
                    file=sys.stderr,
                )
                return 1
            print(f"Loaded {len(known_tags)} known grammar tags from DB")

        while True:
            if args.limit is not None and processed >= args.limit:
                break

            fetch_limit = args.batch_size
            if args.limit is not None:
                fetch_limit = min(fetch_limit, args.limit - processed)

            use_offset = args.reprocess or args.dry_run
            sentences = fetch_sentences(
                conn,
                language=args.language,
                batch_size=fetch_limit,
                offset=offset if use_offset else 0,
                reprocess=args.reprocess or args.dry_run,
            )
            if not sentences:
                break

            batch_rows: list[tuple[int, str, float]] = []
            reprocess_ids: list[int] = []

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
                tags = filter_tags(raw_tags, known_tags, args.skip_unknown)
                if known_tags is not None:
                    unknown_tags.update(raw_tags - tags)

                if args.dry_run:
                    print(f"sentence_id={sentence.id} tags={sorted(tags)}")
                else:
                    if args.reprocess:
                        reprocess_ids.append(sentence.id)
                    for tag in sorted(tags):
                        batch_rows.append((sentence.id, tag, 1.0))

                processed += 1

            if not args.dry_run:
                if args.reprocess and reprocess_ids:
                    delete_tags(conn, reprocess_ids)
                tags_written += insert_tags_batch(conn, batch_rows)
                conn.commit()

            print(f"Batch done: processed={processed}, tags_written={tags_written}")

            if use_offset:
                offset += len(sentences)
            elif len(sentences) < fetch_limit:
                break

    if unknown_tags:
        print(f"Skipped {len(unknown_tags)} unknown tags (not in grammar_constructs)", file=sys.stderr)

    print(f"Done. Sentences processed: {processed}, tags written: {tags_written}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

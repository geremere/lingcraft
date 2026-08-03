#!/usr/bin/env python3
"""Tag sentences from a JSONL file (no database)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from grammar.polke.client import PolkeClient, PolkeError, construct_tag


def main() -> int:
    parser = argparse.ArgumentParser(description="Tag JSONL corpus via POLKE")
    parser.add_argument("input", type=Path, help="JSONL with {id, text} per line")
    parser.add_argument("-o", "--output", type=Path, help="Output JSONL (default: stdout)")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--polke-url", default=None)
    args = parser.parse_args()

    client = PolkeClient(base_url=args.polke_url)
    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout

    processed = 0
    try:
        with args.input.open(encoding="utf-8") as handle:
            for line in handle:
                if args.limit is not None and processed >= args.limit:
                    break
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                text = row.get("text", "")
                try:
                    annotations = client.annotate(text)
                except PolkeError as exc:
                    print(f"id={row.get('id')}: {exc}", file=sys.stderr)
                    continue

                tags = sorted({construct_tag(ann.construct_id) for ann in annotations})
                out.write(
                    json.dumps(
                        {"id": row.get("id"), "text": text, "tags": tags},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                processed += 1
                if processed % 100 == 0:
                    print(f"Tagged {processed} sentences", file=sys.stderr)
    finally:
        if args.output:
            out.close()

    print(f"Done. Tagged {processed} sentences.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

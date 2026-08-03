#!/usr/bin/env python3
"""Tag a single sentence via POLKE (stdout JSON)."""

from __future__ import annotations

import argparse
import json
import sys

from grammar.polke.client import PolkeClient, PolkeError, construct_tag


def main() -> int:
    parser = argparse.ArgumentParser(description="Tag one sentence with POLKE")
    parser.add_argument("text", nargs="?", help="Sentence text")
    parser.add_argument("--polke-url", default=None)
    args = parser.parse_args()

    text = args.text or sys.stdin.read().strip()
    if not text:
        print("No text provided.", file=sys.stderr)
        return 1

    client = PolkeClient(base_url=args.polke_url)
    try:
        annotations = client.annotate(text)
    except PolkeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = {
        "sentence": text,
        "tags": [
            {
                "tag": construct_tag(ann.construct_id),
                "construct_id": ann.construct_id,
                "begin": ann.begin,
                "end": ann.end,
            }
            for ann in annotations
        ],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Suggest EAQUALS grammar topic → EGP construct mappings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

from grammar.egp_registry import load_constructs, load_polke_supported_ids
from grammar.polke.client import PolkeClient, PolkeError, construct_tag

CURRICULUM_DIR = Path(__file__).resolve().parent
INVENTORY = CURRICULUM_DIR / "eaquals_core_inventory.json"
OUT = CURRICULUM_DIR / "eaquals_egp_mapping.yaml"

# EAQUALS title/section keywords → (super_category, sub_category substring)
RULES: list[tuple[str, str, str]] = [
    (r"present simple", "PRESENT", "present simple"),
    (r"present continuous", "PRESENT", "present continuous"),
    (r"past simple", "PAST", "past simple"),
    (r"past continuous", "PAST", "past continuous"),
    (r"present perfect", "PRESENT", "present perfect"),
    (r"going to", "FUTURE", "future"),
    (r"future time|future continuous|future perfect", "FUTURE", "future"),
    (r"can|could", "MODALITY", "can"),
    (r"might|may", "MODALITY", "may"),
    (r"must|have to|should|ought", "MODALITY", ""),
    (r"there is", "VERBS", "there is"),
    (r"imperative", "CLAUSES", "imperatives"),
    (r"conditional", "CLAUSES", "conditional"),
    (r"passive", "PASSIVES", "passives"),
    (r"relative clause", "CLAUSES", "relative"),
    (r"reported speech", "REPORTED SPEECH", "reported"),
    (r"phrasal", "VERBS", "phrasal"),
    (r"article", "DETERMINERS", "articles"),
    (r"determiner", "DETERMINERS", ""),
    (r"possessive", "DETERMINERS", "possessives"),
    (r"pronoun", "PRONOUNS", ""),
    (r"preposition", "PREPOSITIONS", "prepositions"),
    (r"comparative|superlative", "ADJECTIVES", "comparative"),
    (r"adverb", "ADVERBS", ""),
    (r"adjective", "ADJECTIVES", ""),
    (r"question", "QUESTIONS", ""),
    (r"gerund|infinitive|i'd like|verb \+ -ing", "VERBS", "patterns"),
    (r"to be|have got", "VERBS", ""),
    (r"connecting words|linker", "CONJUNCTIONS", ""),
    (r"countable|uncountable|noun", "NOUNS", ""),
    (r"intensifier", "ADVERBS", ""),
    (r"used to", "MODALITY", "used to"),
    (r"wish", "CLAUSES", "conditional"),
    (r"inversion", "FOCUS", ""),
    (r"narrative", "PAST", ""),
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def match_rule(title: str, section: str | None) -> tuple[str, str] | None:
    haystack = normalize(f"{title} {section or ''}")
    for pattern, super_cat, sub_hint in RULES:
        if re.search(pattern, haystack):
            return super_cat, sub_hint
    return None


def score_construct(topic_title: str, construct: dict) -> float:
    title = normalize(topic_title)
    blob = normalize(f"{construct['guideword']} {construct['can_do']} {construct['sub_category']}")
    score = 0.0
    if construct["sub_category"] and normalize(construct["sub_category"]) in title:
        score += 0.5
    for token in re.findall(r"[a-z']+", title):
        if len(token) > 3 and token in blob:
            score += 0.15
    return min(score, 1.0)


def polke_tags_for_examples(
    examples: list[str],
    client: PolkeClient,
) -> dict[str, int]:
    """Return tag → hit count from POLKE annotations on example sentences."""
    counts: dict[str, int] = {}
    for sentence in examples:
        try:
            annotations = client.annotate(sentence)
        except PolkeError:
            continue
        for ann in annotations:
            tag = construct_tag(ann.construct_id)
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def merge_refs(rule_refs: list[dict], polke_counts: dict[str, int], constructs_by_tag: dict[str, dict]) -> list[dict]:
    by_tag = {ref["ref"]: dict(ref) for ref in rule_refs}
    for tag, hits in polke_counts.items():
        if tag in by_tag:
            by_tag[tag]["match"] = "polke+rule"
            by_tag[tag]["confidence"] = min(0.95, by_tag[tag]["confidence"] + 0.1)
            by_tag[tag]["polke_hits"] = hits
        else:
            construct = constructs_by_tag.get(tag)
            if construct is None:
                continue
            by_tag[tag] = {
                "ref": tag,
                "egp_id": construct["egp_id"],
                "match": "polke",
                "confidence": min(0.75, 0.5 + 0.05 * hits),
                "polke_hits": hits,
            }
    merged = sorted(by_tag.values(), key=lambda row: (-row["confidence"], row["ref"]))
    return merged[:20]


def suggest_for_topic(topic: dict, constructs: list[dict]) -> list[dict]:
    levels = set(topic["levels"])
    rule = match_rule(topic["title"], topic.get("section"))
    candidates: list[tuple[float, dict, str]] = []

    for construct in constructs:
        if construct["level"] not in levels:
            continue
        match_type = "level"
        conf = 0.3

        if rule:
            super_cat, sub_hint = rule
            if construct["super_category"] != super_cat:
                continue
            match_type = "super_category"
            conf = 0.6
            if sub_hint and sub_hint in normalize(construct["sub_category"]):
                match_type = "sub_category"
                conf = 0.85

        text_score = score_construct(topic["title"], construct)
        if text_score > 0.3:
            conf = max(conf, text_score)
            match_type = "guideword"

        if rule or text_score > 0.3:
            candidates.append((conf, construct, match_type))

    candidates.sort(key=lambda x: (-x[0], x[1]["egp_id"]))
    seen: set[str] = set()
    refs: list[dict] = []
    for conf, construct, match_type in candidates:
        tag = construct["tag"]
        if tag in seen:
            continue
        seen.add(tag)
        refs.append({"ref": tag, "egp_id": construct["egp_id"], "match": match_type, "confidence": round(conf, 2)})
        if len(refs) >= 20:
            break
    return refs


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest EAQUALS → EGP mappings")
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--report", action="store_true", help="Print summary to stdout")
    parser.add_argument(
        "--polke-validate",
        action="store_true",
        help="Annotate grammar examples via POLKE and merge tags (requires running POLKE)",
    )
    parser.add_argument("--polke-url", default=None, help="POLKE base URL")
    parser.add_argument(
        "--polke-supported-only",
        action="store_true",
        help="Keep only EGP refs that POLKE can tag (registry/polke_supported.json)",
    )
    args = parser.parse_args()

    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    constructs = load_constructs()
    constructs_by_tag = {item["tag"]: item for item in constructs}
    polke_supported_ids = load_polke_supported_ids()
    grammar_topics = inventory["domains"]["grammar"]

    polke_client: PolkeClient | None = None
    if args.polke_validate:
        polke_client = PolkeClient(base_url=args.polke_url)
        if not polke_client.health_check():
            raise SystemExit("POLKE health check failed. Start: bash scripts/grammar/polke/start.sh")

    mappings = []
    empty = 0
    wide = 0
    total_polke_supported = 0
    total_polke_unsupported = 0
    for topic in grammar_topics:
        refs = suggest_for_topic(topic, constructs)
        if polke_client and topic.get("examples"):
            polke_counts = polke_tags_for_examples(topic["examples"], polke_client)
            refs = merge_refs(refs, polke_counts, constructs_by_tag)
        polke_supported_refs = sum(1 for ref in refs if ref["egp_id"] in polke_supported_ids)
        polke_unsupported_refs = len(refs) - polke_supported_refs
        total_polke_supported += polke_supported_refs
        total_polke_unsupported += polke_unsupported_refs
        if args.polke_supported_only:
            refs = [ref for ref in refs if ref["egp_id"] in polke_supported_ids]
        if not refs:
            empty += 1
        if len(refs) > 15:
            wide += 1
        mappings.append(
            {
                "eaquals_id": topic["id"],
                "title": topic["title"],
                "section": topic.get("section"),
                "levels": topic["levels"],
                "egp_refs": refs,
                "polke_supported_refs": polke_supported_refs,
                "polke_unsupported_refs": polke_unsupported_refs,
                "status": "suggested" if refs else "empty",
            }
        )

    payload = {
        "meta": {
            "source_inventory": str(INVENTORY.name),
            "egp_construct_count": len(constructs),
            "polke_supported_count": len(polke_supported_ids),
            "grammar_topic_count": len(grammar_topics),
            "mapped_count": sum(1 for m in mappings if m["egp_refs"]),
            "empty_count": empty,
            "wide_count": wide,
            "polke_validated": bool(args.polke_validate),
            "polke_supported_only": bool(args.polke_supported_only),
            "polke_supported_refs": total_polke_supported,
            "polke_unsupported_refs": total_polke_unsupported,
        },
        "mappings": mappings,
    }
    args.output.write_text(yaml.dump(payload, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    print(f"Wrote {args.output} ({len(mappings)} topics, {empty} empty, {wide} wide)")

    if args.report:
        for row in mappings[:10]:
            refs = ", ".join(r["ref"] for r in row["egp_refs"][:5])
            print(f"  {row['eaquals_id']}: {row['title'][:40]:40s} → {refs}")


if __name__ == "__main__":
    main()

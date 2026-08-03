#!/usr/bin/env python3
"""Import English Grammar Profile (EGP) Excel into registry JSON and optional package scaffold."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
REGISTRY_DIR = SCRIPT_DIR / "registry"
RULES_DIR = SCRIPT_DIR / "rules" / "eng"
DOCS_DIR = SCRIPT_DIR.parents[1] / "docs" / "grammar"
CATEGORY_MAP_PATH = REGISTRY_DIR / "category_map.yaml"

DEFAULT_XLSX_URL = "https://raw.githubusercontent.com/ninja33/EGP/master/asset/egpo.xlsx"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import EGP Excel → registry JSON")
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=Path("/tmp/egpo.xlsx"),
        help="Path to egpo.xlsx",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help=f"Download egpo.xlsx to --xlsx from {DEFAULT_XLSX_URL}",
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Create rules/eng/{level}/{category}/{slug}/ README + metadata.yaml",
    )
    parser.add_argument(
        "--overview",
        action="store_true",
        help="Write docs/grammar/egp-overview.md",
    )
    return parser.parse_args()


def slugify(*parts: str) -> str:
    text = "-".join(p for p in parts if p).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:80] or "construct"


def detectability(guideword: str) -> str:
    upper = guideword.upper()
    if upper.startswith("USE"):
        return "use"
    if upper.startswith("FORM"):
        return "form"
    return "hybrid"


def read_xlsx_rows(path: Path) -> list[dict]:
    zf = zipfile.ZipFile(path)
    strings = [
        "".join(si.itertext())
        for si in ET.fromstring(zf.read("xl/sharedStrings.xml")).findall(".//{*}si")
    ]
    sheet = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.findall(".//{*}row")[1:]:
        vals: list[str] = []
        for cell in row.findall("{*}c"):
            value = cell.find("{*}v")
            if value is None:
                vals.append("")
            elif cell.get("t") == "s":
                vals.append(strings[int(value.text)])
            else:
                vals.append(value.text or "")
        if len(vals) >= 8 and vals[0].isdigit():
            examples = [ex.strip() for ex in vals[7].split("\n\n") if ex.strip()]
            rows.append(
                {
                    "id": int(vals[0]),
                    "super_category": vals[1].strip(),
                    "sub_category": vals[2].strip(),
                    "level": vals[3].strip(),
                    "lexical_range": vals[4].strip(),
                    "guideword": vals[5].strip(),
                    "can_do": vals[6].strip(),
                    "examples": examples,
                }
            )
    return rows


def load_category_map() -> dict[str, str]:
    with CATEGORY_MAP_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def build_entry(row: dict, category_map: dict[str, str]) -> dict:
    category = category_map.get(row["super_category"], slugify(row["super_category"]))
    level = row["level"].lower() or "unknown"
    slug = slugify(
        f"egp-{row['id']}",
        row["sub_category"],
        row["guideword"].split(":")[-1] if ":" in row["guideword"] else row["guideword"],
        level,
    )
    detect = detectability(row["guideword"])
    return {
        "id": row["id"],
        "slug": slug,
        "egp_id": row["id"],
        "tag": f"egp-{row['id']}",
        "level": row["level"],
        "super_category": row["super_category"],
        "sub_category": row["sub_category"],
        "category_folder": category,
        "level_folder": level,
        "guideword": row["guideword"],
        "can_do": row["can_do"],
        "examples": row["examples"][:5],
        "detectability": detect,
        "detection": "polke" if detect == "form" else "llm",
        "polke_construct_id": row["id"],
    }


def write_registry(entries: list[dict]) -> None:
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    by_id = {entry["id"]: entry for entry in entries}
    with (REGISTRY_DIR / "egp_en.json").open("w", encoding="utf-8") as handle:
        json.dump({"constructs": entries, "by_id": by_id}, handle, indent=2, ensure_ascii=False)

    # polke_mapping.json indexes ALL EGP constructs — not POLKE Ruta coverage.
    # Actual taggable IDs: registry/polke_supported.json (from audit_polke_coverage.py).
    polke_mapping = {
        str(entry["id"]): {
            "egp_id": entry["id"],
            "tag": entry["tag"],
            "slug": entry["slug"],
            "level": entry["level"],
            "detectability": entry["detectability"],
        }
        for entry in entries
    }
    with (REGISTRY_DIR / "polke_mapping.json").open("w", encoding="utf-8") as handle:
        json.dump(polke_mapping, handle, indent=2, ensure_ascii=False)


def scaffold_packages(entries: list[dict]) -> int:
    created = 0
    for entry in entries:
        pkg_dir = (
            RULES_DIR
            / entry["level_folder"]
            / entry["category_folder"]
            / entry["slug"]
        )
        pkg_dir.mkdir(parents=True, exist_ok=True)
        readme = pkg_dir / "README.md"
        metadata = pkg_dir / "metadata.yaml"

        if not readme.exists():
            example = entry["examples"][0] if entry["examples"] else ""
            readme.write_text(
                f"# {entry['guideword']}\n\n"
                f"**EGP #{entry['id']}** · **{entry['level']}** · `{entry['tag']}`\n\n"
                f"## Can-do\n\n{entry['can_do']}\n\n"
                f"## Example\n\n{example}\n",
                encoding="utf-8",
            )
            created += 1

        if not metadata.exists():
            yaml.safe_dump(
                {
                    "egp_id": entry["id"],
                    "tag": entry["tag"],
                    "slug": entry["slug"],
                    "level": entry["level"],
                    "super_category": entry["super_category"],
                    "sub_category": entry["sub_category"],
                    "detection": entry["detection"],
                    "detectability": entry["detectability"],
                    "polke_construct_id": entry["polke_construct_id"],
                },
                metadata.open("w", encoding="utf-8"),
                sort_keys=False,
            )
    return created


def write_overview(entries: list[dict]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    levels = Counter(entry["level"] for entry in entries if entry["level"])
    supers = Counter(entry["super_category"] for entry in entries)
    detect = Counter(entry["detectability"] for entry in entries)

    lines = [
        "# English Grammar Profile (EGP) Overview",
        "",
        "Auto-generated from `egpo.xlsx` via `scripts/grammar/import_egp.py`.",
        "",
        "## Summary",
        "",
        f"- **Total constructs:** {len(entries)}",
        "",
        "### By CEFR level",
        "",
        "| Level | Count |",
        "|-------|-------|",
    ]
    for level in ("A1", "A2", "B1", "B2", "C1", "C2"):
        lines.append(f"| {level} | {levels.get(level, 0)} |")

    lines.extend(
        [
            "",
            "### By detectability",
            "",
            "| Type | Count | Notes |",
            "|------|-------|-------|",
            f"| form | {detect.get('form', 0)} | POLKE rule-based |",
            f"| use | {detect.get('use', 0)} | LLM validation later |",
            f"| hybrid | {detect.get('hybrid', 0)} | Mixed |",
            "",
            "### SuperCategories",
            "",
            "| Category | Count |",
            "|----------|-------|",
        ]
    )
    for super_cat, count in sorted(supers.items()):
        lines.append(f"| {super_cat} | {count} |")

    lines.extend(["", "## Sample constructs", ""])
    samples_by_super: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        if len(samples_by_super[entry["super_category"]]) < 2:
            samples_by_super[entry["super_category"]].append(entry)

    for super_cat in sorted(samples_by_super):
        lines.append(f"### {super_cat}")
        lines.append("")
        for entry in samples_by_super[super_cat]:
            example = entry["examples"][0] if entry["examples"] else "—"
            lines.append(f"- **{entry['tag']}** ({entry['level']}) — {entry['guideword']}")
            lines.append(f"  - *{entry['can_do'][:120]}...*")
            lines.append(f"  - Example: *{example[:100]}*")
        lines.append("")

    (DOCS_DIR / "egp-overview.md").write_text("\n".join(lines), encoding="utf-8")


def download_xlsx(dest: Path) -> None:
    import httpx

    dest.parent.mkdir(parents=True, exist_ok=True)
    response = httpx.get(DEFAULT_XLSX_URL, follow_redirects=True, timeout=60)
    response.raise_for_status()
    dest.write_bytes(response.content)


def main() -> int:
    args = parse_args()
    if args.download or not args.xlsx.exists():
        print(f"Downloading {DEFAULT_XLSX_URL} → {args.xlsx}")
        download_xlsx(args.xlsx)

    category_map = load_category_map()
    rows = read_xlsx_rows(args.xlsx)
    entries = [build_entry(row, category_map) for row in rows]
    write_registry(entries)
    print(f"Wrote {len(entries)} constructs to {REGISTRY_DIR / 'egp_en.json'}")

    if args.scaffold:
        created = scaffold_packages(entries)
        print(f"Scaffolded/updated packages under {RULES_DIR} ({created} new README files)")

    if args.overview:
        write_overview(entries)
        print(f"Wrote {DOCS_DIR / 'egp-overview.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

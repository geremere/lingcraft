# Grammar blocks (FSRS curriculum)

Grammar is **not** stored as EGP constructs in the database. The DB holds teachable **grammar blocks** only; external EGP references live in block files on disk.

## Layout

```
blocks/{lang}/{level}/{slug}/
  block.yaml       — FSRS block (title, category, sort_order)
  egp_links.yaml   — external Cambridge EGP refs (not in DB)
  examples.json    — curated sentences for the example bank
```

Example: `blocks/en/a1/a1-modality-can/`

## Load into DB

```bash
pip install -r scripts/requirements.txt
bash backend/scripts/setup_dev_env.sh

PYTHONPATH=scripts python3 scripts/grammar/load_blocks.py --dry-run
PYTHONPATH=scripts python3 scripts/grammar/load_blocks.py
```

## Categories

Folder names (`verbs-tenses`, `modals`, …) are defined in `blocks/_meta/category_map.yaml`.

## FSRS model

One `grammar_blocks` row = one FSRS card. User progress will link via `review_items` (planned).

# Grammar tagging (POLKE + EGP registry)

Offline pipeline: read sentences from PostgreSQL, annotate with POLKE, write tags to JSON/CSV.

EGP constructs live in `registry/egp_en.json` only — not in the database.

## Setup

```bash
pip install -r scripts/requirements.txt

# POLKE (Docker)
bash scripts/grammar/polke/setup.sh
bash scripts/grammar/polke/start.sh   # http://localhost/extractor

# EGP registry (if missing)
PYTHONPATH=scripts python3 scripts/grammar/import_egp.py --download
```

## Tag sentences

```bash
# Single sentence
PYTHONPATH=scripts python3 scripts/grammar/tag_sentence.py "I can swim."

# Batch from DB → JSON (all EGP tags)
PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py \
  --limit 100 \
  --skip-unknown \
  --output tags.json

# Only tags POLKE can actually detect (~658)
PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py \
  --limit 100 \
  --skip-unknown \
  --polke-supported-only \
  --output tags.json

# CSV
PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py -o tags.csv --limit 50
```

## Registry files

| Path | Purpose |
|------|---------|
| `registry/egp_en.json` | Full EGP construct registry (~1239) |
| `registry/polke_mapping.json` | Same constructs indexed by ID — **not** POLKE coverage |
| `registry/polke_supported.json` | EGP IDs with actual POLKE Ruta rules (~658) |

Each construct in `egp_en.json` has a `detection` field (`polke` or `llm`) set from guideword detectability at import time. That is a *planned* detection method, not proof POLKE can tag it. Ground-truth coverage is `polke_supported.json` (regenerate with `audit_polke_coverage.py`).

## Files

| Path | Purpose |
|------|---------|
| `polke/` | Docker provider + `PolkeClient` |
| `audit_polke_coverage.py` | Regenerate `polke_supported.json` from vendor POLKE |
| `import_egp.py` | Excel → JSON |
| `tag_sentences.py` | DB → POLKE → output file |

Curriculum (EAQUALS) and EGP mapping: see [`../curriculum/README.md`](../curriculum/README.md).

# EAQUALS curriculum + EGP mapping

Curriculum data from [EAQUALS Core Curriculum Appendix D](https://www.eaquals.org/wp-content/uploads/EAQUALS_British_Council_Core_Curriculum_April2011.pdf), with grammar examples from Appendix E. EGP constructs stay in `scripts/grammar/registry/egp_en.json` — not in PostgreSQL.

## Files

| File | Purpose |
|------|---------|
| `eaquals_core_inventory.json` | Appendix D topics (grammar + level shells for functions/lexis/topics) |
| `build_eaquals_inventory.py` | Regenerate inventory JSON from embedded source data |
| `eaquals_egp_mapping.yaml` | Grammar topic → EGP construct suggestions |
| `suggest_egp_mapping.py` | Rule-based mapping + optional POLKE validation on examples |
| `export_anki_csv.py` | Anki deck export |

## Build inventory

```bash
python3 scripts/curriculum/build_eaquals_inventory.py
```

## Suggest EGP mappings

Rule-based (level filter, keyword → EGP sub_category, guideword scan):

```bash
PYTHONPATH=scripts python3 scripts/curriculum/suggest_egp_mapping.py --report
```

Only refs POLKE can tag (see `registry/polke_supported.json`):

```bash
PYTHONPATH=scripts python3 scripts/curriculum/suggest_egp_mapping.py --polke-supported-only --report
```

With POLKE validation on grammar examples (start POLKE first):

```bash
bash scripts/grammar/polke/start.sh
PYTHONPATH=scripts python3 scripts/curriculum/suggest_egp_mapping.py --polke-validate --report
```

Output YAML includes per-topic `polke_supported_refs` / `polke_unsupported_refs` counts. `detection: polke` in `egp_en.json` is import-time intent, not coverage — use `polke_supported.json` for ground truth.

Review `eaquals_egp_mapping.yaml`: topics with `status: empty` or more than ~15 refs need manual curation. Target: **3–15 EGP constructs per grammar topic**.

## Export Anki deck

```bash
PYTHONPATH=scripts python3 scripts/curriculum/export_anki_csv.py
# optional: --domain grammar --domain functions
```

Output: `eaquals_anki.csv` (Front / Back / Tags).

## Tag corpus sentences (POLKE)

See [`../grammar/README.md`](../grammar/README.md). Tags are written to JSON/CSV, not the database.

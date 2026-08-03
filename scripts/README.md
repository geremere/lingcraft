# Scripts

Python utilities for offline data pipelines.

## Grammar tagging (POLKE)

Read sentences from PostgreSQL, annotate with local POLKE, write EGP tags to JSON/CSV.

```bash
pip install -r scripts/requirements.txt
bash scripts/grammar/polke/setup.sh
bash scripts/grammar/polke/start.sh

PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py \
  --limit 100 --skip-unknown --output tags.json
```

See [`grammar/README.md`](grammar/README.md).

## EAQUALS curriculum

Appendix D curriculum inventory, grammar → EGP mapping, and Anki export.

```bash
python3 scripts/curriculum/build_eaquals_inventory.py
PYTHONPATH=scripts python3 scripts/curriculum/suggest_egp_mapping.py --report
PYTHONPATH=scripts python3 scripts/curriculum/export_anki_csv.py
```

See [`curriculum/README.md`](curriculum/README.md).

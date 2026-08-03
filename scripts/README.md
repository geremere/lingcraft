# Scripts

Python utilities for offline data pipelines.

## Grammar tagging (EGP + POLKE)

Two-step pipeline:

```bash
pip install -r scripts/requirements.txt

# 0. Apply DB schema (once)
bash backend/scripts/setup_dev_env.sh

# 1. Load EGP construct registry into grammar_constructs
PYTHONPATH=scripts python3 scripts/grammar/load_egp_tags.py

# 2. Start local POLKE
bash scripts/grammar/polke/setup.sh   # first time only
bash scripts/grammar/polke/start.sh   # requires Docker Desktop

# 3. Tag sentences from DB (batch)
PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py --dry-run --limit 10
PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py --skip-unknown --batch-size 100

# Stop POLKE
bash scripts/grammar/polke/stop.sh
```

See [`grammar/polke/README.md`](grammar/polke/README.md) for POLKE setup.

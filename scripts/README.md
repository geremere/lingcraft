# Scripts

Python utilities for offline data pipelines.

## Grammar blocks

Grammar curriculum lives on disk under `scripts/grammar/blocks/` and is loaded into `grammar_blocks` (no EGP in the database).

```bash
pip install -r scripts/requirements.txt
bash backend/scripts/setup_dev_env.sh

PYTHONPATH=scripts python3 scripts/grammar/load_blocks.py --dry-run
PYTHONPATH=scripts python3 scripts/grammar/load_blocks.py
```

See [`grammar/README.md`](grammar/README.md).

# POLKE — local EGP grammar tagger

POLKE annotates English sentences with [English Grammar Profile (EGP)](https://www.englishprofile.org/english-grammar-profile) constructs. Lingraft uses it **offline only** — never on the Go server.

Source: [github.com/chxiaobin/polke](https://github.com/chxiaobin/polke) (Java + UIMA Ruta + Docker).

## Local setup (recommended)

**Requirements:** Docker Desktop, Git, Java 17+, Maven (for first build).

```bash
# 1. Clone POLKE into vendor/ (one-time)
bash scripts/grammar/polke/setup.sh

# 2. Build and start (first run: several minutes)
bash scripts/grammar/polke/start.sh
# API: http://localhost/extractor

# 3. Test
export POLKE_URL=http://localhost
PYTHONPATH=scripts python3 scripts/grammar/tag_sentence.py "Do you like coffee?"

# 4. Stop when done
bash scripts/grammar/polke/stop.sh
```

Default `POLKE_URL` in our client is `http://localhost` — no env needed if POLKE runs locally.

## Tag sentences in PostgreSQL

```bash
pip install -r scripts/requirements.txt

PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py --dry-run --limit 10
PYTHONPATH=scripts python3 scripts/grammar/tag_sentences.py --limit 1000
```

### CLI options (`tag_sentences.py`)

| Flag | Description |
|------|-------------|
| `--language en` | Filter by `languages.code` |
| `--limit N` | Max sentences |
| `--batch-size 100` | Fetch/commit batch |
| `--dry-run` | Print tags, no DB writes |
| `--reprocess` | Re-tag sentences that already have tags |
| `--polke-url URL` | Override `POLKE_URL` env |

## Output format

POLKE returns EGP `constructID` values. We store them as `egp-{constructID}` (e.g. `egp-1035`).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Cannot connect to POLKE` | Run `bash scripts/grammar/polke/start.sh`, wait for build to finish |
| Docker not running | Start Docker Desktop |
| Port 80 in use | Stop conflicting service or check POLKE `serve.sh` / Jetty config |
| Slow first start | Normal — Maven build + Docker image on first `./serve.sh` |

## References

- [POLKE developer guide](https://polke.kibi.group/developer_guide.html)
- [POLKE user guide](https://polke.kibi.group/user_guide.html)
- [EGP Excel mirror](https://github.com/ninja33/EGP)

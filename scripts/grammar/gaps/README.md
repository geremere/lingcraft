# Grammar gap layer (Phase 2+)

EGP constructs that POLKE does not cover need separate tagging:

| Gap | Count (approx) | Approach |
|-----|----------------|----------|
| USE constructs | ~301 | LLM yes/no validation on can-do statement |
| EGP without POLKE rule | ~581 | Custom rules or wait for POLKE updates |
| A0 survival topics | 10 | Manual `rules/eng/a0/` packages |

## Pipeline order

```
1. tag_sentences.py     → POLKE form-based tags (egp-{id})
2. tag_gaps.py (future) → LLM/custom for USE + A0
```

## A0 manual topics (placeholder)

Add under `rules/eng/a0/` when curriculum is defined:

- greetings
- basic introductions
- numbers 1-20
- etc.

Each package: `README.md` + optional `rule.py` with `detection: custom`.

# Database Schema

Source of truth: [`backend/migrations/000001_init_schema.up.sql`](../backend/migrations/000001_init_schema.up.sql)

Single migration while pre-production — edit `000001` instead of adding new migrations.

## Overview

```mermaid
erDiagram
    languages ||--o{ lemmas : has
    languages ||--o{ sentences : has
    languages ||--o{ grammar_constructs : has
    languages ||--o{ sense_descriptions : has

    lemmas ||--o{ senses : has
    lemmas ||--o{ lemma_audio : has
    lemmas ||--o{ sentence_tokens : optional

    senses ||--o{ sense_descriptions : has
    senses ||--o{ sense_tags : has
    senses ||--o{ sense_translations : source
    senses ||--o{ sense_translations : target
    senses ||--o{ sense_sentence_links : has

    sentences ||--o{ sentence_tokens : has
    sentences ||--o{ sentence_tags : has
    sentences ||--o{ sentence_audio : has
    sentences ||--o{ sentence_translations : source
    sentences ||--o{ sentence_translations : target
    sentences ||--o{ sense_sentence_links : has

    image_files ||--o{ senses : optional
    audio_files ||--o{ lemma_audio : has
    audio_files ||--o{ sentence_audio : has
```

**16 tables** + trigger `trg_senses_updated_at` on `senses`.

## Core

### `languages`

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| code | TEXT UNIQUE | `en`, `ru`, `es` |
| name | TEXT | |

### `lemmas`

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| language_id | FK → languages | CASCADE |
| lemma | TEXT | |
| pos | TEXT | |
| frequency_rank | INTEGER | CHECK > 0 |
| frequency_count | INTEGER | CHECK ≥ 0 |
| ipa | TEXT | |
| source, source_ref | TEXT | |

Indexes: `language_id`, `lemma`, `(language_id, frequency_rank)`.

### `senses`

Main learnable unit for vocabulary (FSRS target per sense).

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| lemma_id | FK → lemmas | CASCADE |
| sense_index | INTEGER | UNIQUE(lemma_id, sense_index) |
| cefr_level | TEXT | A1–C2 or NULL |
| image_id | FK → image_files | SET NULL |
| created_at, updated_at | TIMESTAMPTZ | auto-update on UPDATE |

### `grammar_constructs`

EGP grammar tag registry (loaded via `scripts/grammar/load_egp_tags.py`).

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| language_id | FK → languages | CASCADE |
| egp_id | INTEGER | UNIQUE per language |
| tag | TEXT | e.g. `egp-865` |
| slug | TEXT | human-readable id |
| level | TEXT | A1–C2 |
| super_category, sub_category | TEXT | PRESENT, QUESTIONS, … |
| guideword, can_do | TEXT | from EGP |
| detectability | TEXT | `form` \| `use` \| `hybrid` |
| detection | TEXT | `polke` \| `llm` \| `custom` |
| examples_json | JSONB | learner examples |
| created_at | TIMESTAMPTZ | |

## Descriptions and tags

### `sense_descriptions`

Per-sense definitions in multiple languages.

| Column | Type |
|--------|------|
| sense_id | FK → senses |
| language_id | FK → languages |
| definition | TEXT |
| short_definition | TEXT |

UNIQUE(sense_id, language_id).

### `sense_tags`

Domain/vocabulary tags on senses (Kaikki etc.). Free-text `tag`.

UNIQUE(sense_id, tag).

### `sense_translations`

Links equivalent senses across languages.

| Column | Type |
|--------|------|
| source_sense_id, target_sense_id | FK → senses |
| relation_type | `exact` \| `close` \| `broader` \| `narrower` |
| confidence | NUMERIC(4,3) 0–1 |

PK(source_sense_id, target_sense_id).

## Sentences

### `sentences`

| Column | Type | Notes |
|--------|------|-------|
| id | BIGSERIAL PK | |
| language_id | FK → languages | |
| text | TEXT | |
| source, source_ref | TEXT | |
| level_id | TEXT | CEFR band (unconstrained) |

### `sentence_tokens`

NLP tokenization output (spaCy etc.).

| Column | Type |
|--------|------|
| sentence_id | FK → sentences |
| position | INTEGER |
| surface, lemma, pos, tag | TEXT |
| lemma_id | FK → lemmas (optional) |

UNIQUE(sentence_id, position).

### `sentence_tags`

Grammar tags on sentences (POLKE → EGP).

| Column | Type | Notes |
|--------|------|-------|
| sentence_id | FK → sentences | |
| tag | TEXT | `egp-{id}`, matches `grammar_constructs.tag` |
| confidence | NUMERIC(4,3) | 0–1; POLKE rule-based = 1.0 |

### `sentence_translations`

Parallel sentences across languages. PK(source_sentence_id, target_sentence_id).

### `sense_sentence_links`

Word-sense disambiguation: which sense appears in which sentence.

| Column | Type | Notes |
|--------|------|-------|
| sense_id | FK → senses | |
| sentence_id | FK → sentences | |
| score | NUMERIC(4,3) | 0–1 |
| approved | BOOLEAN | default false |
| is_primary | BOOLEAN | default false |

UNIQUE(sense_id, sentence_id).

## Media

### `image_files`

`url`, `provider`, `metadata_json`, `source`, `source_ref`.

### `audio_files`

Same as images + optional `quality_score` (0–1).

### `lemma_audio` / `sentence_audio`

Junction tables: `(lemma_id|sentence_id, audio_id)` + `is_primary`.

## Data flows

### Vocabulary

```
languages → lemmas → senses → sense_descriptions
                      ↓
              sense_sentence_links ← sentences
```

### Grammar

```
grammar_constructs (registry)     sentence_tags (runtime)
         tag = egp-{id}    ←──────────────┘
                              POLKE batch job
```

Sense does **not** link to grammar directly. Path:

```
sense → sense_sentence_links → sentence → sentence_tags
```

## Not in schema yet

From [`docs/design`](design) — planned for quiz/FSRS layer:

- `grammar_blocks` (teachable curriculum ~115 topics)
- `review_items` (FSRS cards)
- `exercises`, `exercise_distractors`
- users, progress tables

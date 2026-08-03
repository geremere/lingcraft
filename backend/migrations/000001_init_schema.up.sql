BEGIN;

CREATE TABLE languages (
    id BIGSERIAL PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL
);

CREATE TABLE image_files (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    provider TEXT,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT,
    source_ref TEXT
);

CREATE TABLE lemmas (
    id BIGSERIAL PRIMARY KEY,
    language_id BIGINT NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    lemma TEXT NOT NULL,
    pos TEXT,
    frequency_rank INTEGER,
    frequency_count INTEGER,
    ipa TEXT,
    source TEXT,
    source_ref TEXT,
    CHECK (frequency_rank IS NULL OR frequency_rank > 0),
    CHECK (frequency_count IS NULL OR frequency_count >= 0)
);

CREATE INDEX idx_lemmas_language_id ON lemmas(language_id);
CREATE INDEX idx_lemmas_lemma ON lemmas(lemma);
CREATE INDEX idx_lemmas_frequency_rank ON lemmas(language_id, frequency_rank);

CREATE TABLE audio_files (
    id BIGSERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    provider TEXT,
    quality_score NUMERIC(4,3),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    source TEXT,
    source_ref TEXT,
    CHECK (quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1))
);

CREATE TABLE sentences (
    id BIGSERIAL PRIMARY KEY,
    language_id BIGINT NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    source TEXT,
    source_ref TEXT,
    level_id TEXT
);

CREATE INDEX idx_sentences_language_id ON sentences(language_id);

CREATE TABLE senses (
    id BIGSERIAL PRIMARY KEY,
    lemma_id BIGINT NOT NULL REFERENCES lemmas(id) ON DELETE CASCADE,
    sense_index INTEGER NOT NULL,
    cefr_level TEXT,
    image_id BIGINT REFERENCES image_files(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (lemma_id, sense_index),
    CHECK (cefr_level IS NULL OR cefr_level IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2'))
);

CREATE INDEX idx_senses_lemma_id ON senses(lemma_id);
CREATE INDEX idx_senses_cefr_level ON senses(cefr_level);

CREATE TABLE sense_descriptions (
    id BIGSERIAL PRIMARY KEY,
    sense_id BIGINT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    language_id BIGINT NOT NULL REFERENCES languages(id) ON DELETE CASCADE,
    definition TEXT NOT NULL,
    short_definition TEXT,
    UNIQUE (sense_id, language_id)
);

CREATE INDEX idx_sense_descriptions_language_id ON sense_descriptions(language_id);

CREATE TABLE sense_tags (
    id BIGSERIAL PRIMARY KEY,
    sense_id BIGINT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    UNIQUE (sense_id, tag)
);

CREATE INDEX idx_sense_tags_tag ON sense_tags(tag);

CREATE TABLE sense_translations (
    source_sense_id BIGINT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    target_sense_id BIGINT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    confidence NUMERIC(4,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source_sense_id, target_sense_id),
    CHECK (source_sense_id <> target_sense_id),
    CHECK (relation_type IN ('exact', 'close', 'broader', 'narrower')),
    CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX idx_sense_translations_target_sense_id ON sense_translations(target_sense_id);

CREATE TABLE lemma_audio (
    lemma_id BIGINT NOT NULL REFERENCES lemmas(id) ON DELETE CASCADE,
    audio_id BIGINT NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (lemma_id, audio_id)
);

CREATE INDEX idx_lemma_audio_audio_id ON lemma_audio(audio_id);

CREATE TABLE sentence_audio (
    sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    audio_id BIGINT NOT NULL REFERENCES audio_files(id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (sentence_id, audio_id)
);

CREATE INDEX idx_sentence_audio_audio_id ON sentence_audio(audio_id);

CREATE TABLE sentence_translations (
    source_sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    target_sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    confidence NUMERIC(4,3),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (source_sentence_id, target_sentence_id),
    CHECK (source_sentence_id <> target_sentence_id),
    CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX idx_sentence_translations_target_sentence_id ON sentence_translations(target_sentence_id);

CREATE TABLE sentence_tokens (
    id BIGSERIAL PRIMARY KEY,
    sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    surface TEXT NOT NULL,
    lemma TEXT,
    pos TEXT,
    tag TEXT,
    lemma_id BIGINT REFERENCES lemmas(id) ON DELETE SET NULL,
    UNIQUE (sentence_id, position)
);

CREATE INDEX idx_sentence_tokens_sentence_id ON sentence_tokens(sentence_id);
CREATE INDEX idx_sentence_tokens_lemma_id ON sentence_tokens(lemma_id);

CREATE TABLE sense_sentence_links (
    id BIGSERIAL PRIMARY KEY,
    sense_id BIGINT NOT NULL REFERENCES senses(id) ON DELETE CASCADE,
    sentence_id BIGINT NOT NULL REFERENCES sentences(id) ON DELETE CASCADE,
    score NUMERIC(4,3),
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (sense_id, sentence_id),
    CHECK (score IS NULL OR (score >= 0 AND score <= 1))
);

CREATE INDEX idx_sense_sentence_links_sense_id ON sense_sentence_links(sense_id);
CREATE INDEX idx_sense_sentence_links_sentence_id ON sense_sentence_links(sentence_id);
CREATE INDEX idx_sense_sentence_links_approved ON sense_sentence_links(approved);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_senses_updated_at
BEFORE UPDATE ON senses
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

COMMIT;

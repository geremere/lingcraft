BEGIN;

DROP TRIGGER IF EXISTS trg_senses_updated_at ON senses;
DROP FUNCTION IF EXISTS set_updated_at();

DROP TABLE IF EXISTS sense_sentence_links;
DROP TABLE IF EXISTS sentence_tokens;
DROP TABLE IF EXISTS sentence_translations;
DROP TABLE IF EXISTS sentence_audio;
DROP TABLE IF EXISTS lemma_audio;
DROP TABLE IF EXISTS sense_translations;
DROP TABLE IF EXISTS sense_tags;
DROP TABLE IF EXISTS sense_descriptions;
DROP TABLE IF EXISTS senses;
DROP TABLE IF EXISTS sentences;
DROP TABLE IF EXISTS audio_files;
DROP TABLE IF EXISTS lemmas;
DROP TABLE IF EXISTS image_files;
DROP TABLE IF EXISTS languages;

COMMIT;

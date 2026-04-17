-- ============================================================
-- Totem Inteligente Inclusivo (Sprint 4) - SQLite Schema
-- Estende Sprint 3 com: chatbot, visão computacional, voz
-- ============================================================

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS interactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id         TEXT    NOT NULL DEFAULT 'simulator-01',
    source            TEXT    NOT NULL DEFAULT 'simulated'
                      CHECK (source IN ('simulated', 'esp32', 'esp32-cam', 'manual', 'test', 'chatbot', 'voice')),
    session_id        TEXT    NULL,
    event_timestamp   TEXT    NOT NULL,
    presence          INTEGER NOT NULL CHECK (presence IN (0,1)),
    touch             INTEGER NOT NULL CHECK (touch IN (0,1)),
    voice_detected    INTEGER NOT NULL CHECK (voice_detected IN (0,1)),
    duration_s        INTEGER NOT NULL CHECK (duration_s >= 0 AND duration_s <= 3600),
    location          TEXT    NULL,
    interaction_zone  TEXT    NULL,
    accessibility_mode TEXT   NULL,
    content_category  TEXT    NULL,
    ui_language       TEXT    NOT NULL DEFAULT 'pt-BR',
    is_valid          INTEGER NOT NULL DEFAULT 1 CHECK (is_valid IN (0,1)),
    validation_notes  TEXT    NULL,
    ingested_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_interactions_device_timestamp
ON interactions (device_id, event_timestamp);

CREATE INDEX IF NOT EXISTS ix_interactions_timestamp ON interactions (event_timestamp);
CREATE INDEX IF NOT EXISTS ix_interactions_source ON interactions (source);
CREATE INDEX IF NOT EXISTS ix_interactions_presence ON interactions (presence);

CREATE TABLE IF NOT EXISTS predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id  INTEGER NOT NULL,
    pred_label      TEXT    NOT NULL,
    pred_proba      REAL    NULL CHECK (pred_proba IS NULL OR (pred_proba >= 0.0 AND pred_proba <= 1.0)),
    model_name      TEXT    NOT NULL DEFAULT 'RandomForestClassifier',
    model_version   TEXT    NOT NULL DEFAULT 'rf_v1',
    trained_at      TEXT    NULL,
    predicted_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    notes           TEXT    NULL,
    FOREIGN KEY (interaction_id) REFERENCES interactions(id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_predictions_interaction_model ON predictions (interaction_id, model_version);
CREATE INDEX IF NOT EXISTS ix_predictions_predicted_at ON predictions (predicted_at);
CREATE INDEX IF NOT EXISTS ix_predictions_label ON predictions (pred_label);

-- SPRINT 4: sessoes de chat
CREATE TABLE IF NOT EXISTS chat_sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL UNIQUE,
    device_id       TEXT    NOT NULL DEFAULT 'totem-01',
    started_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    ended_at        TEXT    NULL,
    total_messages  INTEGER NOT NULL DEFAULT 0,
    language        TEXT    NOT NULL DEFAULT 'pt-BR',
    accessibility_mode TEXT NULL
);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_started ON chat_sessions (started_at);

-- SPRINT 4: mensagens do chat
CREATE TABLE IF NOT EXISTS chat_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NOT NULL,
    role            TEXT    NOT NULL CHECK (role IN ('user', 'assistant')),
    content         TEXT    NOT NULL,
    intent          TEXT    NULL,
    confidence      REAL    NULL,
    input_mode      TEXT    NOT NULL DEFAULT 'text' CHECK (input_mode IN ('text', 'voice', 'touch')),
    created_at      TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session ON chat_messages (session_id);
CREATE INDEX IF NOT EXISTS ix_chat_messages_created ON chat_messages (created_at);
CREATE INDEX IF NOT EXISTS ix_chat_messages_intent ON chat_messages (intent);

-- SPRINT 4: eventos de visao computacional
CREATE TABLE IF NOT EXISTS vision_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id       TEXT    NOT NULL DEFAULT 'totem-01',
    session_id      TEXT    NULL,
    detected_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    frame_id        TEXT    NULL,
    person_detected INTEGER NOT NULL DEFAULT 0 CHECK (person_detected IN (0,1)),
    person_count    INTEGER NOT NULL DEFAULT 0,
    age_group       TEXT    NULL,
    emotion         TEXT    NULL,
    attention_score REAL    NULL,
    zone            TEXT    NULL,
    source          TEXT    NOT NULL DEFAULT 'simulated' CHECK (source IN ('camera', 'simulated', 'dataset')),
    raw_labels      TEXT    NULL,
    confidence      REAL    NULL
);

CREATE INDEX IF NOT EXISTS ix_vision_detected_at ON vision_events (detected_at);
CREATE INDEX IF NOT EXISTS ix_vision_person_detected ON vision_events (person_detected);

-- SPRINT 4: eventos de voz
CREATE TABLE IF NOT EXISTS voice_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT    NULL,
    device_id       TEXT    NOT NULL DEFAULT 'totem-01',
    recorded_at     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    transcript      TEXT    NULL,
    language        TEXT    NOT NULL DEFAULT 'pt-BR',
    confidence      REAL    NULL,
    duration_ms     INTEGER NULL,
    source          TEXT    NOT NULL DEFAULT 'simulated' CHECK (source IN ('microphone', 'simulated', 'file')),
    processed       INTEGER NOT NULL DEFAULT 0 CHECK (processed IN (0,1)),
    chat_message_id INTEGER NULL,
    FOREIGN KEY (chat_message_id) REFERENCES chat_messages(id)
);

CREATE INDEX IF NOT EXISTS ix_voice_recorded_at ON voice_events (recorded_at);

-- View de features (Sprint 3 + 4)
CREATE VIEW IF NOT EXISTS v_features AS
SELECT
    i.id AS interaction_id,
    i.device_id, i.source, i.session_id, i.event_timestamp,
    CAST(strftime('%H', substr(i.event_timestamp, 1, 19)) AS INTEGER) AS hour,
    CAST(strftime('%w', substr(i.event_timestamp, 1, 19)) AS INTEGER) AS weekday,
    CASE
        WHEN CAST(strftime('%H', substr(i.event_timestamp, 1, 19)) AS INTEGER) BETWEEN 7 AND 10 THEN 1
        WHEN CAST(strftime('%H', substr(i.event_timestamp, 1, 19)) AS INTEGER) BETWEEN 17 AND 20 THEN 1
        ELSE 0
    END AS is_peak_hour,
    i.presence, i.touch, i.voice_detected, i.duration_s,
    CASE
        WHEN i.duration_s <= 5 THEN 'quick'
        WHEN i.duration_s BETWEEN 6 AND 20 THEN 'normal'
        ELSE 'engaged'
    END AS duration_class
FROM interactions i WHERE i.is_valid = 1;

CREATE TRIGGER IF NOT EXISTS trg_interactions_validate_presence_duration
AFTER INSERT ON interactions FOR EACH ROW
WHEN NEW.presence = 0 AND NEW.duration_s > 5
BEGIN
    UPDATE interactions
    SET is_valid = 0,
        validation_notes = COALESCE(validation_notes, '') || 'presence=0 com duration_s alto; '
    WHERE id = NEW.id;
END;

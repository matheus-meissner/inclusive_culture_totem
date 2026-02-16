-- ============================================================
-- Totem Inteligente Inclusivo (Sprint 3) - SQLite Schema
-- Sensores (simulados/reais) -> Banco -> ML -> Dashboard/Report
-- ============================================================

PRAGMA foreign_keys = ON;

-- ----------------------------
-- Tabela principal: interações
-- ----------------------------
CREATE TABLE IF NOT EXISTS interactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Identificação e origem do evento
    device_id         TEXT    NOT NULL DEFAULT 'simulator-01',
    source            TEXT    NOT NULL DEFAULT 'simulated'
                      CHECK (source IN ('simulated', 'esp32', 'esp32-cam', 'manual', 'test')),
    session_id        TEXT    NULL, -- agrupa uma "visita" ao totem (opcional)

    -- Momento do evento (momento do sensor)
    event_timestamp   TEXT    NOT NULL,  -- ISO-8601 UTC recomendado: 2026-02-16T13:45:12.123Z

    -- Sinais (sensores/inputs)
    presence          INTEGER NOT NULL CHECK (presence IN (0,1)),
    touch             INTEGER NOT NULL CHECK (touch IN (0,1)),
    voice_detected    INTEGER NOT NULL CHECK (voice_detected IN (0,1)),

    -- Medidas
    duration_s        INTEGER NOT NULL CHECK (duration_s >= 0 AND duration_s <= 3600),

    -- Campos “de negócio” (opcional, mas deixa realista)
    location          TEXT    NULL,   -- ex.: "Biblioteca - Piso 1"
    interaction_zone  TEXT    NULL,   -- ex.: "Tela Principal", "Acessibilidade"
    accessibility_mode TEXT   NULL,   -- ex.: "alto_contraste", "libras", "leitor_tela"
    content_category  TEXT    NULL,   -- ex.: "cultura", "informacoes", "agenda"
    ui_language       TEXT    NOT NULL DEFAULT 'pt-BR',

    -- Qualidade/Integridade
    is_valid          INTEGER NOT NULL DEFAULT 1 CHECK (is_valid IN (0,1)),
    validation_notes  TEXT    NULL,

    -- Auditoria (momento em que o sistema gravou no banco)
    ingested_at       TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

-- Evita duplicidade simples (mesmo device + timestamp)
-- (em dados reais você poderia ter colisões, mas pra Sprint ajuda muito)
CREATE UNIQUE INDEX IF NOT EXISTS ux_interactions_device_timestamp
ON interactions (device_id, event_timestamp);

CREATE INDEX IF NOT EXISTS ix_interactions_timestamp
ON interactions (event_timestamp);

CREATE INDEX IF NOT EXISTS ix_interactions_source
ON interactions (source);

CREATE INDEX IF NOT EXISTS ix_interactions_presence
ON interactions (presence);

-- ----------------------------------------
-- Saída do ML: previsões por interação
-- ----------------------------------------
CREATE TABLE IF NOT EXISTS predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    interaction_id  INTEGER NOT NULL,

    -- Resultado do modelo
    pred_label      TEXT    NOT NULL,       -- ex.: quick / normal / engaged
    pred_proba      REAL    NULL
                    CHECK (pred_proba IS NULL OR (pred_proba >= 0.0 AND pred_proba <= 1.0)),

    -- Metadados do modelo (reprodutibilidade)
    model_name      TEXT    NOT NULL DEFAULT 'RandomForestClassifier',
    model_version   TEXT    NOT NULL DEFAULT 'rf_v1',
    trained_at      TEXT    NULL,           -- ISO: quando o modelo foi treinado
    predicted_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),

    -- Auditoria extra
    notes           TEXT    NULL,

    FOREIGN KEY (interaction_id)
      REFERENCES interactions(id)
      ON DELETE CASCADE
);

-- Uma interação deve ter no máximo 1 previsão por (model_version)
CREATE UNIQUE INDEX IF NOT EXISTS ux_predictions_interaction_model
ON predictions (interaction_id, model_version);

CREATE INDEX IF NOT EXISTS ix_predictions_predicted_at
ON predictions (predicted_at);

CREATE INDEX IF NOT EXISTS ix_predictions_label
ON predictions (pred_label);

-- -------------------------------------------------
-- View de features: facilita ETL/ML sem duplicar
-- -------------------------------------------------
CREATE VIEW IF NOT EXISTS v_features AS
SELECT
    i.id AS interaction_id,
    i.device_id,
    i.source,
    i.session_id,
    i.event_timestamp,
    CAST(strftime('%H', substr(i.event_timestamp, 1, 19)) AS INTEGER) AS hour,
    CAST(strftime('%w', substr(i.event_timestamp, 1, 19)) AS INTEGER) AS weekday,
    CASE
        WHEN CAST(strftime('%H', substr(i.event_timestamp, 1, 19)) AS INTEGER) BETWEEN 7 AND 10 THEN 1
        WHEN CAST(strftime('%H', substr(i.event_timestamp, 1, 19)) AS INTEGER) BETWEEN 17 AND 20 THEN 1
        ELSE 0
    END AS is_peak_hour,

    i.presence,
    i.touch,
    i.voice_detected,
    i.duration_s,

    CASE
        WHEN i.duration_s <= 5 THEN 'quick'
        WHEN i.duration_s BETWEEN 6 AND 20 THEN 'normal'
        ELSE 'engaged'
    END AS duration_class
FROM interactions i
WHERE i.is_valid = 1;

-- -------------------------------------------------
-- Trigger simples: se presença=0, duration tende a ser 0
-- (não bloqueia, mas marca inválido se incoerente)
-- -------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_interactions_validate_presence_duration
AFTER INSERT ON interactions
FOR EACH ROW
WHEN NEW.presence = 0 AND NEW.duration_s > 5
BEGIN
    UPDATE interactions
    SET is_valid = 0,
        validation_notes = COALESCE(validation_notes, '') || 'presence=0 com duration_s alto; '
    WHERE id = NEW.id;
END;

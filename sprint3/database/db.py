from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ============================================================
# Paths robustos (não quebram se rodar de qualquer pasta)
# ============================================================
DB_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = DB_DIR / "totem.db"
DEFAULT_SCHEMA_PATH = DB_DIR / "schema.sql"


@dataclass(frozen=True)
class Interaction:
    id: int
    device_id: str
    source: str
    session_id: Optional[str]
    event_timestamp: str
    presence: int
    touch: int
    voice_detected: int
    duration_s: int
    ingested_at: str
    is_valid: int
    validation_notes: Optional[str]


def get_conn(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Abre conexão SQLite com pragmas recomendados para projeto local.
    """
    path = Path(db_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row

    # Pragmas úteis
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")      # melhor para leitura/escrita concorrente (Streamlit)
    conn.execute("PRAGMA synchronous = NORMAL;")    # bom trade-off local
    conn.execute("PRAGMA temp_store = MEMORY;")
    return conn


def init_db(conn: sqlite3.Connection, schema_path: str | Path = DEFAULT_SCHEMA_PATH) -> None:
    """
    Inicializa/atualiza o schema executando schema.sql.
    Idempotente (pode chamar várias vezes).
    """
    schema_file = Path(schema_path).resolve()
    if not schema_file.exists():
        raise FileNotFoundError(f"schema.sql não encontrado em: {schema_file}")

    sql = schema_file.read_text(encoding="utf-8")
    conn.executescript(sql)
    conn.commit()


# ============================================================
# Inserts
# ============================================================

def insert_interaction(conn: sqlite3.Connection, payload: Dict[str, Any]) -> int:
    """
    Insere uma interação já validada/normalizada.
    Retorna o id gerado.

    Payload esperado (mínimo):
      - event_timestamp (str)
      - presence (0/1)
      - touch (0/1)
      - voice_detected (0/1)
      - duration_s (int >=0)
    O resto é opcional.
    """
    # Normalizações leves (defensivo, mas sem "mágica")
    device_id = str(payload.get("device_id") or "simulator-01")
    source = str(payload.get("source") or "simulated")
    session_id = payload.get("session_id")
    event_timestamp = str(payload["event_timestamp"])

    presence = int(payload.get("presence", 0))
    touch = int(payload.get("touch", 0))
    voice_detected = int(payload.get("voice_detected", 0))
    duration_s = int(payload.get("duration_s", 0))

    location = payload.get("location")
    interaction_zone = payload.get("interaction_zone")
    accessibility_mode = payload.get("accessibility_mode")
    content_category = payload.get("content_category")
    ui_language = str(payload.get("ui_language") or "pt-BR")

    # Integridade básica (mantém o banco "realista")
    is_valid = 1
    validation_notes_parts: List[str] = []

    if presence not in (0, 1):
        is_valid = 0
        validation_notes_parts.append("presence fora de {0,1}")

    if touch not in (0, 1):
        is_valid = 0
        validation_notes_parts.append("touch fora de {0,1}")

    if voice_detected not in (0, 1):
        is_valid = 0
        validation_notes_parts.append("voice_detected fora de {0,1}")

    if duration_s < 0:
        is_valid = 0
        validation_notes_parts.append("duration_s negativo")

    if duration_s > 3600:
        is_valid = 0
        validation_notes_parts.append("duration_s muito alto (>3600)")

    validation_notes = None
    if validation_notes_parts:
        validation_notes = "; ".join(validation_notes_parts) + "; "

    sql = """
    INSERT INTO interactions (
        device_id, source, session_id, event_timestamp,
        presence, touch, voice_detected, duration_s,
        location, interaction_zone, accessibility_mode, content_category,
        ui_language,
        is_valid, validation_notes
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    cur = conn.execute(
        sql,
        (
            device_id, source, session_id, event_timestamp,
            presence, touch, voice_detected, duration_s,
            location, interaction_zone, accessibility_mode, content_category,
            ui_language,
            is_valid, validation_notes,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def insert_prediction(
    conn: sqlite3.Connection,
    interaction_id: int,
    label: str,
    proba: Optional[float],
    model_version: str,
    model_name: str = "RandomForestClassifier",
    trained_at: Optional[str] = None,
    notes: Optional[str] = None,
) -> int:
    """
    Insere previsão para uma interação (por versão do modelo).
    """
    sql = """
    INSERT INTO predictions (
        interaction_id, pred_label, pred_proba,
        model_name, model_version, trained_at, notes
    )
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """
    cur = conn.execute(
        sql,
        (interaction_id, str(label), proba, model_name, str(model_version), trained_at, notes),
    )
    conn.commit()
    return int(cur.lastrowid)


# ============================================================
# Fetch / Queries
# ============================================================

def fetch_interactions(conn: sqlite3.Connection, limit: int = 200) -> List[Interaction]:
    """
    Retorna as últimas interações (mais recentes primeiro).
    """
    sql = """
    SELECT
        id, device_id, source, session_id, event_timestamp,
        presence, touch, voice_detected, duration_s,
        ingested_at, is_valid, validation_notes
    FROM interactions
    ORDER BY event_timestamp DESC
    LIMIT ?;
    """
    rows = conn.execute(sql, (int(limit),)).fetchall()
    return [
        Interaction(
            id=int(r["id"]),
            device_id=str(r["device_id"]),
            source=str(r["source"]),
            session_id=r["session_id"],
            event_timestamp=str(r["event_timestamp"]),
            presence=int(r["presence"]),
            touch=int(r["touch"]),
            voice_detected=int(r["voice_detected"]),
            duration_s=int(r["duration_s"]),
            ingested_at=str(r["ingested_at"]),
            is_valid=int(r["is_valid"]),
            validation_notes=r["validation_notes"],
        )
        for r in rows
    ]


def fetch_unpredicted(
    conn: sqlite3.Connection,
    model_version: str = "rf_v1",
    limit: int = 500,
    only_valid: bool = True,
) -> List[sqlite3.Row]:
    """
    Busca interações que ainda NÃO possuem previsão para a versão do modelo.
    Retorna rows (dict-like) para facilitar no ML.
    """
    where_valid = "AND i.is_valid = 1" if only_valid else ""
    sql = f"""
    SELECT
        i.id,
        i.device_id,
        i.source,
        i.session_id,
        i.event_timestamp,
        i.presence,
        i.touch,
        i.voice_detected,
        i.duration_s
    FROM interactions i
    LEFT JOIN predictions p
      ON p.interaction_id = i.id
     AND p.model_version = ?
    WHERE p.id IS NULL
    {where_valid}
    ORDER BY i.event_timestamp ASC
    LIMIT ?;
    """
    return conn.execute(sql, (str(model_version), int(limit))).fetchall()


def fetch_predictions_latest(
    conn: sqlite3.Connection,
    limit: int = 200,
    model_version: str = "rf_v1",
) -> List[sqlite3.Row]:
    """
    Retorna previsões mais recentes com dados da interação (JOIN).
    Útil para dashboard.
    """
    sql = """
    SELECT
        p.id AS prediction_id,
        p.pred_label,
        p.pred_proba,
        p.model_version,
        p.predicted_at,
        i.id AS interaction_id,
        i.event_timestamp,
        i.device_id,
        i.source,
        i.presence,
        i.touch,
        i.voice_detected,
        i.duration_s
    FROM predictions p
    JOIN interactions i ON i.id = p.interaction_id
    WHERE p.model_version = ?
    ORDER BY p.predicted_at DESC
    LIMIT ?;
    """
    return conn.execute(sql, (str(model_version), int(limit))).fetchall()


def fetch_kpis(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    KPIs simples (ótimo para dashboard e report).
    """
    sql = """
    SELECT
        COUNT(*) AS total_events,
        SUM(CASE WHEN presence = 1 THEN 1 ELSE 0 END) AS total_presence,
        ROUND(AVG(duration_s), 2) AS avg_duration,
        SUM(CASE WHEN touch = 1 THEN 1 ELSE 0 END) AS total_touch,
        SUM(CASE WHEN voice_detected = 1 THEN 1 ELSE 0 END) AS total_voice,
        SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) AS total_valid
    FROM interactions;
    """
    r = conn.execute(sql).fetchone()
    return dict(r) if r else {}


# ============================================================
# Utils
# ============================================================

def execute_many(conn: sqlite3.Connection, sql: str, params_seq: Iterable[Tuple[Any, ...]]) -> int:
    """
    Executa executemany e retorna número de linhas afetadas (aproximado).
    """
    cur = conn.executemany(sql, params_seq)
    conn.commit()
    return cur.rowcount


def close_conn(conn: sqlite3.Connection) -> None:
    try:
        conn.close()
    except Exception:
        pass

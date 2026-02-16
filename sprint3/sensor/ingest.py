from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pathlib import Path

# Import do seu módulo de banco (Sprint 3)
from database.db import get_conn, init_db, insert_interaction


@dataclass(frozen=True)
class IngestResult:
    inserted_id: int
    normalized_event: Dict[str, Any]


def _to_iso_utc(ts: Any) -> str:
    """
    Converte timestamp para ISO-8601 UTC com 'Z'.
    Aceita:
      - str (já ISO ou "YYYY-mm-dd HH:MM:SS")
      - datetime
      - None (gera agora)
    """
    if ts is None or str(ts).strip() == "":
        dt = datetime.now(timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    if isinstance(ts, datetime):
        dt = ts.astimezone(timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # string
    s = str(ts).strip()

    # Se vier no formato "2026-02-16T13:00:00Z", mantém.
    if s.endswith("Z") and "T" in s:
        return s

    # Se vier ISO sem Z, tenta parse básico
    # Ex.: "2026-02-16T13:00:00" ou "2026-02-16 13:00:00"
    try:
        if "T" in s:
            dt = datetime.fromisoformat(s)
        else:
            dt = datetime.fromisoformat(s.replace(" ", "T"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except Exception:
        # fallback: agora
        dt = datetime.now(timezone.utc)
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _to_01(v: Any) -> int:
    """
    Normaliza para 0/1 aceitando:
    - 0/1, True/False, "0"/"1", "true"/"false", "yes"/"no"
    """
    if v is None:
        return 0
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, (int, float)):
        return 1 if int(v) != 0 else 0

    s = str(v).strip().lower()
    if s in ("1", "true", "t", "yes", "y", "sim"):
        return 1
    if s in ("0", "false", "f", "no", "n", "nao", "não"):
        return 0

    # default conservador
    return 0


def validate_event(e: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida e normaliza o evento do sensor/simulador para o contrato do banco.

    Contrato mínimo (Sprint 3):
      - event_timestamp (ISO UTC)
      - presence, touch, voice_detected (0/1)
      - duration_s (int >= 0)
      - device_id (str)
      - source (str)

    Observação:
      - Aceita também 'timestamp' no lugar de 'event_timestamp'
      - Aceita 'duration' no lugar de 'duration_s'
    """
    if not isinstance(e, dict):
        raise ValueError("Evento inválido: esperado dict.")

    # Timestamp (aceita timestamp ou event_timestamp)
    raw_ts = e.get("event_timestamp", e.get("timestamp"))
    event_timestamp = _to_iso_utc(raw_ts)

    # Flags
    presence = _to_01(e.get("presence"))
    touch = _to_01(e.get("touch"))
    voice_detected = _to_01(e.get("voice_detected"))

    # Duração (aceita duration ou duration_s)
    raw_duration = e.get("duration_s", e.get("duration", 0))
    try:
        duration_s = int(raw_duration)
    except Exception:
        duration_s = 0

    if duration_s < 0:
        duration_s = 0
    if duration_s > 3600:
        duration_s = 3600

    # Regras de coerência (deixa “real”)
    # Se não há presença, não faz sentido ter touch/voz/duração alta
    if presence == 0:
        touch = 0
        voice_detected = 0
        if duration_s > 5:
            duration_s = 0

    device_id = str(e.get("device_id") or "simulator-01")
    source = str(e.get("source") or "simulated")

    # Campos opcionais (ajudam a parecer real e pontuam no dashboard/report)
    normalized: Dict[str, Any] = {
        "event_timestamp": event_timestamp,
        "presence": presence,
        "touch": touch,
        "voice_detected": voice_detected,
        "duration_s": duration_s,
        "device_id": device_id,
        "source": source,

        # opcionais (se existirem no evento, passam; senão, None)
        "session_id": e.get("session_id"),
        "location": e.get("location"),
        "interaction_zone": e.get("interaction_zone"),
        "accessibility_mode": e.get("accessibility_mode"),
        "content_category": e.get("content_category"),
        "ui_language": e.get("ui_language") or "pt-BR",
    }

    return normalized


def ingest_event(event: Dict[str, Any], db_path: Optional[str] = None, verbose: bool = True) -> IngestResult:
    """
    Valida e insere o evento no banco.
    Retorna IngestResult com inserted_id + evento normalizado.
    """
    normalized = validate_event(event)

    # Conexão com DB
    if db_path:
        conn = get_conn(db_path)
    else:
        conn = get_conn()

    try:
        init_db(conn)
        inserted_id = insert_interaction(conn, normalized)
        if verbose:
            print(f"Inserted interaction id={inserted_id} | device={normalized['device_id']} source={normalized['source']} ts={normalized['event_timestamp']}")
        return IngestResult(inserted_id=inserted_id, normalized_event=normalized)
    finally:
        conn.close()

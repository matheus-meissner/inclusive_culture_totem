"""
vision/detector.py — Módulo de Visão Computacional (Sprint 4)
100% local. Usa OpenCV + simulação inteligente quando câmera não disponível.
Classifica presença, faixa etária, emoção e zona de atenção.
"""
from __future__ import annotations

import json
import random
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================
# Paths
# ============================================================
VISION_DIR = Path(__file__).resolve().parent
SPRINT4_DIR = VISION_DIR.parent
DB_PATH = SPRINT4_DIR / "database" / "totem.db"

# ============================================================
# Modelo de resultado de detecção
# ============================================================

@dataclass
class DetectionResult:
    frame_id: str
    person_detected: bool
    person_count: int
    age_group: Optional[str]       # crianca, jovem, adulto, idoso
    emotion: Optional[str]         # neutro, feliz, curioso, confuso
    attention_score: float         # 0.0 a 1.0
    zone: Optional[str]            # zona onde a pessoa está
    confidence: float
    source: str                    # camera, simulated, dataset
    raw_labels: Dict[str, Any]
    detected_at: str


# ============================================================
# Simulador inteligente de visão
# ============================================================

AGE_GROUPS = ["crianca", "jovem", "adulto", "idoso"]
AGE_WEIGHTS = [0.10, 0.35, 0.40, 0.15]

EMOTIONS = ["neutro", "feliz", "curioso", "confuso"]
EMOTION_WEIGHTS = [0.40, 0.25, 0.25, 0.10]

ZONES = [
    "Tela Principal",
    "Painel de Acessibilidade",
    "Busca de Conteúdo",
    "Agenda/Eventos",
    "Mapa do Espaço",
]

# Padrão temporal: mais pessoas de manhã e tarde
HOURLY_PRESENCE_WEIGHTS = {
    0: 0.02, 1: 0.01, 2: 0.01, 3: 0.01, 4: 0.01, 5: 0.02,
    6: 0.05, 7: 0.15, 8: 0.35, 9: 0.55, 10: 0.70, 11: 0.80,
    12: 0.65, 13: 0.75, 14: 0.80, 15: 0.78, 16: 0.72, 17: 0.65,
    18: 0.50, 19: 0.40, 20: 0.30, 21: 0.20, 22: 0.10, 23: 0.05,
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def simulate_frame(
    dt: Optional[datetime] = None,
    force_person: Optional[bool] = None,
) -> DetectionResult:
    """
    Simula detecção de um frame de câmera.
    Se force_person=True, garante detecção. Se False, garante ausência.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    hour = dt.hour
    presence_prob = HOURLY_PRESENCE_WEIGHTS.get(hour, 0.3)

    if force_person is True:
        person_detected = True
    elif force_person is False:
        person_detected = False
    else:
        person_detected = random.random() < presence_prob

    frame_id = str(uuid.uuid4())[:8]

    if not person_detected:
        return DetectionResult(
            frame_id=frame_id,
            person_detected=False,
            person_count=0,
            age_group=None,
            emotion=None,
            attention_score=0.0,
            zone=None,
            confidence=round(random.uniform(0.80, 0.99), 3),
            source="simulated",
            raw_labels={"objects": [], "person_prob": round(1 - presence_prob, 3)},
            detected_at=dt.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        )

    # Pessoa detectada
    person_count = random.choices([1, 2, 3], weights=[0.70, 0.22, 0.08], k=1)[0]
    age_group = random.choices(AGE_GROUPS, weights=AGE_WEIGHTS, k=1)[0]
    emotion = random.choices(EMOTIONS, weights=EMOTION_WEIGHTS, k=1)[0]
    zone = random.choice(ZONES)

    # Score de atenção: curioso e feliz têm mais atenção
    base_attention = {"neutro": 0.5, "feliz": 0.7, "curioso": 0.85, "confuso": 0.4}
    attention_score = round(
        min(1.0, base_attention.get(emotion, 0.5) + random.gauss(0, 0.1)), 3
    )

    confidence = round(random.uniform(0.75, 0.98), 3)

    raw_labels = {
        "objects": [{"label": "person", "prob": confidence}],
        "age_group_probs": {ag: round(random.random(), 3) for ag in AGE_GROUPS},
        "emotion_probs": {em: round(random.random(), 3) for em in EMOTIONS},
        "person_count_estimate": person_count,
    }
    # Normaliza probs
    raw_labels["age_group_probs"][age_group] = max(raw_labels["age_group_probs"].values()) + 0.1
    raw_labels["emotion_probs"][emotion] = max(raw_labels["emotion_probs"].values()) + 0.1

    return DetectionResult(
        frame_id=frame_id,
        person_detected=True,
        person_count=person_count,
        age_group=age_group,
        emotion=emotion,
        attention_score=attention_score,
        zone=zone,
        confidence=confidence,
        source="simulated",
        raw_labels=raw_labels,
        detected_at=dt.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    )


# ============================================================
# Tentativa de uso de câmera real (OpenCV)
# ============================================================

def try_capture_from_camera(camera_index: int = 0) -> Optional[DetectionResult]:
    """
    Tenta capturar frame real via OpenCV.
    Faz detecção de presença via Haar Cascade (face detection).
    Retorna None se câmera não disponível.
    """
    try:
        import cv2  # type: ignore
    except ImportError:
        return None

    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return None

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return None

        # Haar Cascade para detecção de rostos
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        person_count = len(faces)
        person_detected = person_count > 0

        frame_id = str(uuid.uuid4())[:8]

        return DetectionResult(
            frame_id=frame_id,
            person_detected=person_detected,
            person_count=person_count,
            age_group="adulto" if person_detected else None,  # sem modelo de idade real
            emotion="neutro" if person_detected else None,
            attention_score=0.8 if person_detected else 0.0,
            zone="Tela Principal",
            confidence=0.85 if person_detected else 0.95,
            source="camera",
            raw_labels={"faces_detected": person_count, "method": "haar_cascade"},
            detected_at=_iso_now(),
        )

    except Exception:
        return None


# ============================================================
# Persistência
# ============================================================

def _get_conn() -> sqlite3.Connection:
    from database.db import get_conn, init_db
    conn = get_conn(DB_PATH)
    init_db(conn)
    return conn


def save_vision_event(result: DetectionResult, device_id: str = "totem-01", session_id: Optional[str] = None) -> int:
    """Salva evento de visão no banco. Retorna id."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO vision_events
            (device_id, session_id, detected_at, frame_id, person_detected, person_count,
             age_group, emotion, attention_score, zone, source, raw_labels, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device_id,
                session_id,
                result.detected_at,
                result.frame_id,
                int(result.person_detected),
                result.person_count,
                result.age_group,
                result.emotion,
                result.attention_score,
                result.zone,
                result.source,
                json.dumps(result.raw_labels),
                result.confidence,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


# ============================================================
# Geração em bulk para análise (Sprint 4)
# ============================================================

def simulate_bulk(
    n: int = 500,
    days: int = 7,
    device_id: str = "totem-01",
    verbose: bool = False,
) -> int:
    """
    Gera N eventos simulados de visão espalhados nos últimos X dias.
    Retorna quantidade inserida.
    """
    now = datetime.now(timezone.utc)
    inserted = 0

    for i in range(n):
        delta = random.randint(0, days * 24 * 3600)
        dt = now - timedelta(seconds=delta)
        result = simulate_frame(dt=dt)
        save_vision_event(result, device_id=device_id)
        inserted += 1

        if verbose and (i + 1) % 100 == 0:
            print(f"Vision events inserted: {i + 1}/{n}")

    return inserted


# ============================================================
# API de detecção (câmera real ou simulada)
# ============================================================

def detect(
    use_camera: bool = False,
    camera_index: int = 0,
    device_id: str = "totem-01",
    session_id: Optional[str] = None,
    save: bool = True,
) -> DetectionResult:
    """
    Detecta presença. Tenta câmera real se use_camera=True, senão simula.
    Salva no banco se save=True.
    """
    result = None

    if use_camera:
        result = try_capture_from_camera(camera_index)

    if result is None:
        result = simulate_frame()

    if save:
        save_vision_event(result, device_id=device_id, session_id=session_id)

    return result


# ============================================================
# Análise de padrões
# ============================================================

def get_vision_analytics() -> Dict[str, Any]:
    """Retorna métricas agregadas dos eventos de visão."""
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM vision_events").fetchone()[0]
        with_person = conn.execute("SELECT COUNT(*) FROM vision_events WHERE person_detected = 1").fetchone()[0]

        age_dist = dict(conn.execute(
            "SELECT age_group, COUNT(*) FROM vision_events WHERE age_group IS NOT NULL GROUP BY age_group"
        ).fetchall())

        emotion_dist = dict(conn.execute(
            "SELECT emotion, COUNT(*) FROM vision_events WHERE emotion IS NOT NULL GROUP BY emotion"
        ).fetchall())

        zone_dist = dict(conn.execute(
            "SELECT zone, COUNT(*) FROM vision_events WHERE zone IS NOT NULL GROUP BY zone ORDER BY COUNT(*) DESC"
        ).fetchall())

        avg_attention = conn.execute(
            "SELECT ROUND(AVG(attention_score), 3) FROM vision_events WHERE person_detected = 1"
        ).fetchone()[0] or 0.0

        return {
            "total_frames": total,
            "frames_with_person": with_person,
            "presence_rate": round(with_person / total * 100, 1) if total > 0 else 0.0,
            "age_distribution": age_dist,
            "emotion_distribution": emotion_dist,
            "zone_distribution": zone_dist,
            "avg_attention_score": avg_attention,
        }
    finally:
        conn.close()

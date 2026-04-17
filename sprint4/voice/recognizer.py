"""
voice/recognizer.py — Módulo de Voz (Sprint 4)
100% local. Suporte real via SpeechRecognition (offline com Vosk ou online com Google).
Fallback inteligente com simulação quando microfone não disponível.
"""
from __future__ import annotations

import random
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ============================================================
# Paths
# ============================================================
VOICE_DIR = Path(__file__).resolve().parent
SPRINT4_DIR = VOICE_DIR.parent
DB_PATH = SPRINT4_DIR / "database" / "totem.db"

# ============================================================
# Modelo de resultado de transcrição
# ============================================================

@dataclass
class TranscriptResult:
    transcript: str
    confidence: float
    language: str
    duration_ms: int
    source: str  # microphone, simulated, file
    success: bool
    error: Optional[str] = None


# ============================================================
# Frases simuladas realistas para o contexto do tótem
# ============================================================

SIMULATED_PHRASES = [
    # Saudações
    ("oi", "pt-BR"),
    ("olá, tudo bem?", "pt-BR"),
    ("bom dia", "pt-BR"),
    ("boa tarde", "pt-BR"),
    # Exposições
    ("quais são as exposições disponíveis?", "pt-BR"),
    ("o que tem para ver aqui?", "pt-BR"),
    ("me fala sobre as obras de arte", "pt-BR"),
    ("tem alguma exposição de fotografia?", "pt-BR"),
    # Eventos
    ("quais eventos acontecem essa semana?", "pt-BR"),
    ("tem algum show hoje?", "pt-BR"),
    ("quando é o próximo concerto?", "pt-BR"),
    ("quero saber da programação cultural", "pt-BR"),
    # Horários
    ("qual o horário de funcionamento?", "pt-BR"),
    ("o museu fecha que horas?", "pt-BR"),
    ("a biblioteca está aberta?", "pt-BR"),
    # Localização
    ("onde fica o banheiro?", "pt-BR"),
    ("tem restaurante aqui?", "pt-BR"),
    ("qual a senha do wifi?", "pt-BR"),
    ("tem estacionamento?", "pt-BR"),
    # Acessibilidade
    ("vocês têm recursos para deficientes visuais?", "pt-BR"),
    ("tem intérprete de libras?", "pt-BR"),
    ("preciso de cadeira de rodas", "pt-BR"),
    # Ingressos
    ("quanto custa a entrada?", "pt-BR"),
    ("a entrada é gratuita?", "pt-BR"),
    # Despedidas
    ("obrigado pela ajuda", "pt-BR"),
    ("tchau, muito obrigado", "pt-BR"),
]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# ============================================================
# Reconhecimento real via SpeechRecognition
# ============================================================

def try_recognize_from_microphone(
    language: str = "pt-BR",
    timeout: int = 5,
    phrase_time_limit: int = 10,
) -> Optional[TranscriptResult]:
    """
    Tenta reconhecer fala via microfone usando SpeechRecognition + Whisper local.
    Retorna None se não disponível.
    """
    try:
        import speech_recognition as sr  # type: ignore
    except ImportError:
        return None

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            duration_ms = int(len(audio.frame_data) / (audio.sample_rate * audio.sample_width) * 1000)
    except Exception as e:
        return TranscriptResult(
            transcript="",
            confidence=0.0,
            language=language,
            duration_ms=0,
            source="microphone",
            success=False,
            error=f"Microfone indisponível: {e}",
        )

    # Tenta Whisper local (offline)
    try:
        transcript = r.recognize_whisper(audio, language=language.split("-")[0])
        return TranscriptResult(
            transcript=transcript.strip(),
            confidence=0.90,
            language=language,
            duration_ms=duration_ms,
            source="microphone",
            success=True,
        )
    except Exception:
        pass

    # Tenta Google (online fallback)
    try:
        transcript = r.recognize_google(audio, language=language)
        return TranscriptResult(
            transcript=transcript.strip(),
            confidence=0.85,
            language=language,
            duration_ms=duration_ms,
            source="microphone",
            success=True,
        )
    except sr.UnknownValueError:
        return TranscriptResult(
            transcript="",
            confidence=0.0,
            language=language,
            duration_ms=duration_ms,
            source="microphone",
            success=False,
            error="Fala não reconhecida",
        )
    except sr.RequestError as e:
        return TranscriptResult(
            transcript="",
            confidence=0.0,
            language=language,
            duration_ms=duration_ms,
            source="microphone",
            success=False,
            error=f"Erro no serviço de reconhecimento: {e}",
        )


# ============================================================
# Simulação inteligente
# ============================================================

def simulate_voice_input(language: str = "pt-BR") -> TranscriptResult:
    """Simula entrada de voz com frase aleatória do contexto do tótem."""
    phrase, lang = random.choice(SIMULATED_PHRASES)
    duration_ms = random.randint(800, 4000)
    confidence = round(random.uniform(0.75, 0.98), 3)

    return TranscriptResult(
        transcript=phrase,
        confidence=confidence,
        language=lang,
        duration_ms=duration_ms,
        source="simulated",
        success=True,
    )


# ============================================================
# Persistência
# ============================================================

def _get_conn() -> sqlite3.Connection:
    from database.db import get_conn, init_db
    conn = get_conn(DB_PATH)
    init_db(conn)
    return conn


def save_voice_event(
    result: TranscriptResult,
    session_id: Optional[str] = None,
    device_id: str = "totem-01",
    chat_message_id: Optional[int] = None,
) -> int:
    """Salva evento de voz no banco."""
    conn = _get_conn()
    try:
        cur = conn.execute(
            """
            INSERT INTO voice_events
            (session_id, device_id, recorded_at, transcript, language,
             confidence, duration_ms, source, processed, chat_message_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                device_id,
                _iso_now(),
                result.transcript if result.success else None,
                result.language,
                result.confidence if result.success else None,
                result.duration_ms,
                result.source,
                1 if result.success else 0,
                chat_message_id,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def simulate_bulk_voice(n: int = 200, device_id: str = "totem-01") -> int:
    """Gera N eventos de voz simulados para análise."""
    inserted = 0
    for _ in range(n):
        result = simulate_voice_input()
        save_voice_event(result, device_id=device_id)
        inserted += 1
    return inserted


# ============================================================
# API principal
# ============================================================

def recognize(
    use_microphone: bool = False,
    language: str = "pt-BR",
    session_id: Optional[str] = None,
    device_id: str = "totem-01",
    save: bool = True,
    chat_message_id: Optional[int] = None,
) -> TranscriptResult:
    """
    Reconhece fala: tenta microfone real, senão simula.
    Salva no banco se save=True.
    """
    result = None

    if use_microphone:
        result = try_recognize_from_microphone(language=language)

    if result is None:
        result = simulate_voice_input(language=language)

    if save:
        save_voice_event(
            result,
            session_id=session_id,
            device_id=device_id,
            chat_message_id=chat_message_id,
        )

    return result


# ============================================================
# Análise de padrões de voz
# ============================================================

def get_voice_analytics() -> Dict[str, Any]:
    """Retorna métricas agregadas dos eventos de voz."""
    conn = _get_conn()
    try:
        total = conn.execute("SELECT COUNT(*) FROM voice_events").fetchone()[0]
        processed = conn.execute("SELECT COUNT(*) FROM voice_events WHERE processed = 1").fetchone()[0]
        avg_conf = conn.execute(
            "SELECT ROUND(AVG(confidence), 3) FROM voice_events WHERE processed = 1"
        ).fetchone()[0] or 0.0
        avg_dur = conn.execute(
            "SELECT ROUND(AVG(duration_ms), 0) FROM voice_events WHERE processed = 1"
        ).fetchone()[0] or 0

        # Distribuição por idioma
        lang_dist = dict(conn.execute(
            "SELECT language, COUNT(*) FROM voice_events GROUP BY language"
        ).fetchall())

        # Top transcripts (para análise de tópicos)
        sample = conn.execute(
            "SELECT transcript FROM voice_events WHERE transcript IS NOT NULL ORDER BY RANDOM() LIMIT 10"
        ).fetchall()
        sample_transcripts = [r[0] for r in sample]

        return {
            "total_events": total,
            "processed": processed,
            "success_rate": round(processed / total * 100, 1) if total > 0 else 0.0,
            "avg_confidence": avg_conf,
            "avg_duration_ms": avg_dur,
            "language_distribution": lang_dist,
            "sample_transcripts": sample_transcripts,
        }
    finally:
        conn.close()

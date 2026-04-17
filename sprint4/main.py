"""
main.py — Orquestrador Sprint 4 (Totem Inteligente Inclusivo)
Pipeline: sensor → DB → ML → visão → voz → chatbot → dashboard → report
"""
from __future__ import annotations

import argparse
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from database.db import get_conn, init_db
from sensor.ingest import ingest_event
from sensor.simulate_sensor import generate_interaction

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "database" / "totem.db"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def log(msg: str) -> None:
    print(f"[{iso_now()}] {msg}")


@dataclass
class RunConfig:
    seconds: int = 60
    interval_s: float = 1.0
    device_id: str = "simulator-01"


# ============================================================
# Comandos
# ============================================================

def cmd_init_db() -> None:
    log("INIT-DB: criando/validando schema Sprint 4 (com chat, visão e voz)...")
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
    finally:
        conn.close()
    log(f"INIT-DB: OK ✅ ({DB_PATH})")


def cmd_ingest(cfg: RunConfig) -> None:
    log(f"INGEST: iniciando ingestão por {cfg.seconds}s device={cfg.device_id}")
    cmd_init_db()

    start = time.time()
    inserted = 0
    session_id = str(uuid.uuid4())

    while (time.time() - start) < cfg.seconds:
        if inserted % 15 == 0 and inserted > 0:
            session_id = str(uuid.uuid4())

        e = generate_interaction(device_id=cfg.device_id, session_id=session_id)
        ingest_event(e, verbose=False)
        inserted += 1

        if inserted % 25 == 0:
            log(f"INGEST: inserted={inserted}")

        time.sleep(max(0.0, cfg.interval_s))

    log(f"INGEST: finalizado ✅ total_inserted={inserted}")


def cmd_bulk_ingest(n: int = 3000, devices: int = 5, days: int = 7) -> None:
    log(f"BULK-INGEST: gerando {n} interações (devices={devices}, days={days})...")
    cmd_init_db()
    from sensor.simulate_sensor import run_bulk
    run_bulk(n=n, devices=devices, days=days, balance=True)
    log("BULK-INGEST: concluído ✅")


def cmd_train() -> None:
    log("TRAIN: treinando modelo ML...")
    import ml.train as ml_train
    ml_train.main()
    log("TRAIN: concluído ✅")


def cmd_predict(limit: int = 6000) -> None:
    log(f"PREDICT: inferência (limit={limit})...")
    import ml.predict as ml_predict
    ml_predict.main(limit=limit, model_version_override=None)
    log("PREDICT: concluído ✅")


def cmd_vision_bulk(n: int = 500, days: int = 7) -> None:
    log(f"VISION: gerando {n} eventos de visão computacional simulados (days={days})...")
    cmd_init_db()
    from vision.detector import simulate_bulk
    inserted = simulate_bulk(n=n, days=days, verbose=True)
    log(f"VISION: {inserted} eventos inseridos ✅")


def cmd_voice_bulk(n: int = 200) -> None:
    log(f"VOICE: gerando {n} eventos de voz simulados...")
    cmd_init_db()
    from voice.recognizer import simulate_bulk_voice
    inserted = simulate_bulk_voice(n=n)
    log(f"VOICE: {inserted} eventos inseridos ✅")


def cmd_chat_demo() -> None:
    """Demonstração interativa do chatbot no terminal."""
    log("CHAT-DEMO: iniciando chatbot interativo (digite 'sair' para encerrar)...")
    cmd_init_db()

    from chatbot.engine import chat, create_session, end_session

    session_id = create_session(device_id="totem-demo")
    print("\n" + "=" * 60)
    print("  TÓTEM CULTURAL — Assistente Virtual")
    print("  (Sprint 4 | 100% Local)")
    print("=" * 60)
    print("  Digite sua mensagem ou 'sair' para encerrar.\n")

    while True:
        try:
            user_input = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if normalize_input(user_input) in ("sair", "exit", "quit"):
            print("\nTotem: Até logo! Obrigado pela visita. 👋\n")
            break

        response = chat(user_message=user_input, session_id=session_id, input_mode="text")
        print(f"\nTotem: {response.bot_response}")
        print(f"       [intent: {response.intent} | confiança: {response.confidence:.0%}]\n")

    end_session(session_id)
    log("CHAT-DEMO: sessão encerrada ✅")


def normalize_input(text: str) -> str:
    import unicodedata
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text


def cmd_report() -> None:
    log("REPORT: gerando relatório analítico Sprint 4...")
    import reports.generate_report as rep
    rep.main()
    log("REPORT: concluído ✅")


def cmd_simulate_chat_sessions(n_sessions: int = 20) -> None:
    """Gera N sessões de chat simuladas para popular o banco."""
    log(f"SIMULATE-CHAT: gerando {n_sessions} sessões de chat simuladas...")
    cmd_init_db()

    from chatbot.engine import chat, create_session, end_session
    import random

    SAMPLE_INPUTS = [
        "oi",
        "quais exposições têm hoje?",
        "qual o horário de funcionamento?",
        "tem acessibilidade para cadeirante?",
        "onde fica o banheiro?",
        "qual a senha do wifi?",
        "quero saber sobre os eventos",
        "a entrada é gratuita?",
        "tem restaurante aqui?",
        "quero ver obras de arte",
        "quando fecha?",
        "tem intérprete de libras?",
        "qual o horário da biblioteca?",
        "obrigado",
        "tchau",
    ]

    for i in range(n_sessions):
        session_id = create_session(device_id=f"simulator-{(i % 5) + 1:02d}")
        n_msgs = random.randint(2, 6)
        for _ in range(n_msgs):
            msg = random.choice(SAMPLE_INPUTS)
            chat(user_message=msg, session_id=session_id, input_mode=random.choice(["text", "touch", "voice"]))
        end_session(session_id)

        if (i + 1) % 5 == 0:
            log(f"SIMULATE-CHAT: {i + 1}/{n_sessions} sessões criadas")

    log(f"SIMULATE-CHAT: {n_sessions} sessões simuladas ✅")


def cmd_all(cfg: RunConfig) -> None:
    """Pipeline completo Sprint 4."""
    log("ALL: iniciando pipeline completo Sprint 4 🚀")
    cmd_init_db()
    cmd_bulk_ingest(n=3000, devices=5, days=7)
    cmd_train()
    cmd_predict(limit=6000)
    cmd_vision_bulk(n=500, days=7)
    cmd_voice_bulk(n=200)
    cmd_simulate_chat_sessions(n_sessions=30)
    cmd_report()
    log("ALL: pipeline completo finalizado ✅")
    log("  ➜  Para o dashboard: streamlit run dashboard/app.py")
    log("  ➜  Para o chatbot:   python main.py chat-demo")


# ============================================================
# CLI
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sprint4/main.py",
        description="Orquestração Sprint 4 — Tótem Inteligente Inclusivo (sensor+ML+visão+voz+chat)",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Cria/valida o schema do banco (Sprint 4)")

    p_bulk = sub.add_parser("bulk-ingest", help="Gera N interações rapidamente")
    p_bulk.add_argument("--n", type=int, default=3000)
    p_bulk.add_argument("--devices", type=int, default=5)
    p_bulk.add_argument("--days", type=int, default=7)

    p_ing = sub.add_parser("ingest", help="Ingestão contínua por X segundos")
    p_ing.add_argument("--seconds", type=int, default=60)
    p_ing.add_argument("--interval", type=float, default=1.0)
    p_ing.add_argument("--device", type=str, default="simulator-01")

    sub.add_parser("train", help="Treina modelo ML")

    p_pred = sub.add_parser("predict", help="Gera previsões ML")
    p_pred.add_argument("--limit", type=int, default=6000)

    p_vis = sub.add_parser("vision-bulk", help="Gera eventos simulados de visão")
    p_vis.add_argument("--n", type=int, default=500)
    p_vis.add_argument("--days", type=int, default=7)

    p_voi = sub.add_parser("voice-bulk", help="Gera eventos simulados de voz")
    p_voi.add_argument("--n", type=int, default=200)

    p_chat_sim = sub.add_parser("simulate-chat", help="Simula sessões de chatbot")
    p_chat_sim.add_argument("--sessions", type=int, default=20)

    sub.add_parser("chat-demo", help="Chatbot interativo no terminal")
    sub.add_parser("report", help="Gera relatório analítico Sprint 4")

    p_all = sub.add_parser("all", help="Pipeline completo Sprint 4")
    p_all.add_argument("--seconds", type=int, default=60)
    p_all.add_argument("--interval", type=float, default=1.0)
    p_all.add_argument("--device", type=str, default="simulator-01")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        cmd_init_db()
    elif args.command == "bulk-ingest":
        cmd_bulk_ingest(n=args.n, devices=args.devices, days=args.days)
    elif args.command == "ingest":
        cfg = RunConfig(seconds=args.seconds, interval_s=args.interval, device_id=args.device)
        cmd_ingest(cfg)
    elif args.command == "train":
        cmd_train()
    elif args.command == "predict":
        cmd_predict(limit=args.limit)
    elif args.command == "vision-bulk":
        cmd_vision_bulk(n=args.n, days=args.days)
    elif args.command == "voice-bulk":
        cmd_voice_bulk(n=args.n)
    elif args.command == "simulate-chat":
        cmd_simulate_chat_sessions(n_sessions=args.sessions)
    elif args.command == "chat-demo":
        cmd_chat_demo()
    elif args.command == "report":
        cmd_report()
    elif args.command == "all":
        cfg = RunConfig(seconds=args.seconds, interval_s=args.interval, device_id=args.device)
        cmd_all(cfg)


if __name__ == "__main__":
    main()

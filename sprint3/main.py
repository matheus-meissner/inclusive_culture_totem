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


# ============================================================
# Paths
# ============================================================
ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "database" / "totem.db"


# ============================================================
# Util
# ============================================================
def iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def log(msg: str) -> None:
    print(f"[{iso_now_utc()}] {msg}")


@dataclass
class RunConfig:
    seconds: int = 60
    interval_s: float = 1.0
    device_id: str = "simulator-01"


# ============================================================
# Commands
# ============================================================
def cmd_init_db() -> None:
    log("INIT-DB: criando/validando schema do SQLite...")
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
    finally:
        conn.close()
    log(f"INIT-DB: OK ✅ ({DB_PATH})")


def cmd_ingest(cfg: RunConfig) -> None:
    """
    Ingestão por tempo: gera eventos e insere no banco via ingest_event.
    """
    log(f"INGEST: iniciando ingestão por {cfg.seconds}s (interval={cfg.interval_s}s) device={cfg.device_id}")

    # garante DB pronto
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

    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        count = conn.execute("SELECT count(*) FROM interactions").fetchone()[0]
    finally:
        conn.close()
    log(f"INGEST: interactions count={count}")


def cmd_train() -> None:
    """
    Executa o treino (gera artifacts).
    Imports locais para evitar inicialização antecipada de backends gráficos.
    """
    log("TRAIN: iniciando treino ML (gera artifacts)...")
    import ml.train as ml_train
    ml_train.main()
    log("TRAIN: concluído ✅ (ver ml/artifacts/)")


def cmd_predict(limit: int = 6000) -> None:
    """
    Executa inferência e grava em predictions.
    """
    log(f"PREDICT: iniciando inferência (limit={limit})...")
    import ml.predict as ml_predict
    ml_predict.main(limit=limit, model_version_override=None)
    log("PREDICT: concluído ✅ (predictions gravadas)")

    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        n_pred = conn.execute("SELECT count(*) FROM predictions").fetchone()[0]
    finally:
        conn.close()
    log(f"PREDICT: predictions count={n_pred}")


def cmd_report() -> None:
    """
    Gera reports/report.md.
    """
    log("REPORT: gerando reports/report.md ...")
    import reports.generate_report as rep_gen
    rep_gen.main()
    log("REPORT: concluído ✅ (reports/report.md atualizado)")


def cmd_all(cfg: RunConfig) -> None:
    """
    Pipeline completo:
      init-db -> ingest -> train -> predict -> report
    """
    log("ALL: iniciando pipeline completo (Sprint 3) 🚀")
    cmd_init_db()
    cmd_ingest(cfg)
    cmd_train()
    cmd_predict(limit=6000)
    cmd_report()
    log("ALL: pipeline completo finalizado ✅")


# ============================================================
# CLI
# ============================================================
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sprint3/main.py",
        description="Orquestração do pipeline Sprint 3 (sensor -> DB -> ML -> dashboard/report).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Cria/valida o schema do banco SQLite")

    p_ing = sub.add_parser("ingest", help="Roda ingestão por X segundos (gera e insere eventos)")
    p_ing.add_argument("--seconds", type=int, default=60, help="Duração da ingestão em segundos")
    p_ing.add_argument("--interval", type=float, default=1.0, help="Intervalo entre eventos (segundos)")
    p_ing.add_argument("--device", type=str, default="simulator-01", help="device_id do simulador")

    sub.add_parser("train", help="Treina o modelo e gera artifacts")

    p_pred = sub.add_parser("predict", help="Roda inferência e grava em predictions")
    p_pred.add_argument("--limit", type=int, default=6000, help="Máximo de registros para prever")

    sub.add_parser("report", help="Gera reports/report.md com KPIs + métricas + insights")

    p_all = sub.add_parser("all", help="Roda pipeline completo em sequência")
    p_all.add_argument("--seconds", type=int, default=60, help="Duração da ingestão em segundos")
    p_all.add_argument("--interval", type=float, default=1.0, help="Intervalo entre eventos (segundos)")
    p_all.add_argument("--device", type=str, default="simulator-01", help="device_id do simulador")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init-db":
        cmd_init_db()
        return

    if args.command == "ingest":
        cfg = RunConfig(seconds=args.seconds, interval_s=args.interval, device_id=args.device)
        cmd_ingest(cfg)
        return

    if args.command == "train":
        cmd_train()
        return

    if args.command == "predict":
        cmd_predict(limit=args.limit)
        return

    if args.command == "report":
        cmd_report()
        return

    if args.command == "all":
        cfg = RunConfig(seconds=args.seconds, interval_s=args.interval, device_id=args.device)
        cmd_all(cfg)
        return


if __name__ == "__main__":
    main()

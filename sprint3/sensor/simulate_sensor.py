from __future__ import annotations

import argparse
import random
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from sensor.ingest import ingest_event


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def generate_interaction(
    device_id: str,
    session_id: str,
    dt: Optional[datetime] = None,
    force_class: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gera evento com cara de real. Se force_class for passado (quick/normal/engaged),
    força uma duração compatível com o target do ML para balancear dataset.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    presence = random.choices([0, 1], weights=[0.20, 0.80], k=1)[0]

    # Se queremos forçar classe, garantimos presence=1 (faz sentido)
    if force_class is not None:
        presence = 1

    if presence == 0:
        touch = 0
        voice_detected = 0
        duration_s = random.choice([0, 0, 1, 2])
    else:
        touch = random.choices([0, 1], weights=[0.35, 0.65], k=1)[0]
        voice_detected = random.choices([0, 1], weights=[0.75, 0.25], k=1)[0]

        if force_class == "quick":
            duration_s = random.randint(1, 5)
        elif force_class == "normal":
            duration_s = random.randint(6, 20)
        elif force_class == "engaged":
            duration_s = random.randint(21, 70)
        else:
            bucket = random.choices(["short", "medium", "long"], weights=[0.60, 0.30, 0.10], k=1)[0]
            if bucket == "short":
                duration_s = random.randint(1, 6)
            elif bucket == "medium":
                duration_s = random.randint(7, 20)
            else:
                duration_s = random.randint(21, 60)

    # Campos opcionais (variação real)
    location = random.choice(["Biblioteca - Piso 1", "Centro Cultural - Entrada", "Museu - Hall", "Biblioteca - Recepção"])
    interaction_zone = random.choice(["Tela Principal", "Acessibilidade", "Busca de Conteúdo", "Agenda/Evento"])
    accessibility_mode = random.choices(
        ["nenhum", "alto_contraste", "libras", "leitor_tela"],
        weights=[0.70, 0.12, 0.10, 0.08],
        k=1
    )[0]
    if accessibility_mode == "nenhum":
        accessibility_mode = None

    content_category = random.choice(["cultura", "informacoes", "agenda", "acervo", "servicos"])
    ui_language = random.choice(["pt-BR", "pt-BR", "pt-BR", "en-US"])  # maioria PT, alguns EN

    return {
        "event_timestamp": _iso_utc(dt),
        "presence": presence,
        "touch": touch,
        "voice_detected": voice_detected,
        "duration_s": duration_s,
        "device_id": device_id,
        "source": "simulated",
        "session_id": session_id,
        "location": location,
        "interaction_zone": interaction_zone,
        "accessibility_mode": accessibility_mode,
        "content_category": content_category,
        "ui_language": ui_language,
    }


def run_live(interval_s: float = 5.0) -> None:
    print("Iniciando simulador (LIVE)... Ctrl+C para parar.")
    device_id = "simulator-01"
    session_id = str(uuid.uuid4())

    try:
        while True:
            if random.random() < 0.08:
                session_id = str(uuid.uuid4())
            e = generate_interaction(device_id=device_id, session_id=session_id)
            ingest_event(e, verbose=True)
            time.sleep(interval_s)
    except KeyboardInterrupt:
        print("\nLIVE finalizado.")


def run_bulk(
    n: int,
    devices: int = 1,
    days: int = 1,
    balance: bool = True,
) -> None:
    """
    Gera N eventos MUITO rápido, com variação temporal.
    - devices: quantos devices diferentes simular
    - days: espalha timestamps nos últimos X dias
    - balance: força distribuição mais equilibrada das classes (quick/normal/engaged)
    """
    print(f"Gerando BULK: n={n} devices={devices} days={days} balance={balance}")

    device_ids = [f"simulator-{i:02d}" for i in range(1, devices + 1)]
    now = datetime.now(timezone.utc)

    # Distribuição controlada para reduzir warnings e melhorar relatório
    class_cycle = ["quick", "normal", "engaged"] if balance else [None]

    for i in range(n):
        device_id = random.choice(device_ids)
        session_id = str(uuid.uuid4())

        # timestamp aleatório dentro da janela de dias (e espalhado por horas)
        delta_seconds = random.randint(0, days * 24 * 60 * 60)
        dt = now - timedelta(seconds=delta_seconds)

        # offset incremental pra nunca repetir no mesmo device
        dt = dt + timedelta(microseconds=i)


        # força classe de forma cíclica para equilibrar
        force_class = class_cycle[i % len(class_cycle)] if balance else None

        e = generate_interaction(device_id=device_id, session_id=session_id, dt=dt, force_class=force_class)
        ingest_event(e, verbose=False)

        # log a cada 200
        if (i + 1) % 200 == 0:
            print(f"Inserted {i + 1}/{n}...")

    print("BULK concluído ✅")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bulk", type=int, default=0, help="Se >0, gera N eventos rapidamente")
    parser.add_argument("--devices", type=int, default=1, help="Qtd de devices simulados no bulk")
    parser.add_argument("--days", type=int, default=1, help="Espalha timestamps nos últimos X dias")
    parser.add_argument("--no-balance", action="store_true", help="Desativa balanceamento de classes")
    parser.add_argument("--interval", type=float, default=5.0, help="Intervalo (LIVE) em segundos")
    args = parser.parse_args()

    if args.bulk and args.bulk > 0:
        run_bulk(
            n=args.bulk,
            devices=max(1, args.devices),
            days=max(1, args.days),
            balance=not args.no_balance,
        )
    else:
        run_live(interval_s=max(0.1, args.interval))


if __name__ == "__main__":
    main()

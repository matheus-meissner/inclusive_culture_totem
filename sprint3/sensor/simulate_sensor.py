from __future__ import annotations

import random
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from .ingest import ingest_event


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def generate_interaction(device_id: str, session_id: str) -> Dict[str, Any]:
    """
    Gera um evento SIMULADO com cara de real.

    Regras de realismo:
    - presence=0 => touch=0, voice=0 e duration baixo/zero
    - presence=1 => touch e voice probabilísticos, duration variando
    - adiciona campos de negócio opcionais (zona, categoria, acessibilidade) para parecer "mundo real"
    """
    presence = random.choices([0, 1], weights=[0.25, 0.75], k=1)[0]

    if presence == 0:
        touch = 0
        voice_detected = 0
        duration_s = random.choice([0, 0, 1, 2])  # normalmente 0
    else:
        # Touch mais comum do que voz
        touch = random.choices([0, 1], weights=[0.35, 0.65], k=1)[0]
        voice_detected = random.choices([0, 1], weights=[0.75, 0.25], k=1)[0]

        # Duração com distribuição mais real: muitos curtos, alguns médios, poucos longos
        bucket = random.choices(["short", "medium", "long"], weights=[0.60, 0.30, 0.10], k=1)[0]
        if bucket == "short":
            duration_s = random.randint(1, 6)
        elif bucket == "medium":
            duration_s = random.randint(7, 20)
        else:
            duration_s = random.randint(21, 60)

    # Campos opcionais para parecer aplicação real (ajudam muito no dashboard/report)
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
    ui_language = "pt-BR"

    event = {
        # contrato do banco (Sprint 3)
        "event_timestamp": _iso_utc_now(),
        "presence": presence,
        "touch": touch,
        "voice_detected": voice_detected,
        "duration_s": duration_s,
        "device_id": device_id,
        "source": "simulated",

        # opcional, mas “profissional”
        "session_id": session_id,
        "location": location,
        "interaction_zone": interaction_zone,
        "accessibility_mode": accessibility_mode,
        "content_category": content_category,
        "ui_language": ui_language,
    }

    return event


def main() -> None:
    print("Iniciando simulador de sensor do Totem Flexmedia (Sprint 3)...")

    # device/session realistas
    device_id = "simulator-01"

    # sessão “simula” uma visita ao totem; muda a cada X eventos para ficar real
    session_id = str(uuid.uuid4())

    try:
        while True:
            # troca de sessão ocasionalmente (simula novo usuário)
            if random.random() < 0.08:
                session_id = str(uuid.uuid4())

            event = generate_interaction(device_id=device_id, session_id=session_id)

            # IMPORTANTE: grava via ingest (validação + insert + logs)
            ingest_event(event, verbose=True)

            # A cada 5s (como sua Sprint 2, bom para vídeo)
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nSimulação finalizada pelo usuário.")


if __name__ == "__main__":
    main()

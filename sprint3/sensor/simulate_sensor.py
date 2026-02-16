import random
import time
import sqlite3
from datetime import datetime


DB_PATH = "../database/totem.db"


def create_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            presence INTEGER NOT NULL,
            touch INTEGER NOT NULL,
            voice_detected INTEGER NOT NULL,
            duration INTEGER NOT NULL
        );
        """
    )
    conn.commit()


def generate_interaction():
    """
    Gera um registro de interação simulada.

    Regra:
    - presence = 0  → touch = 0, voice_detected = 0, duration = 0
    - presence = 1  → touch/voice aleatórios e duração entre 1 e 20s
    """
    presence = random.choice([0, 1])

    if presence == 0:
        touch = 0
        voice_detected = 0
        duration = 0
    else:
        touch = random.choice([0, 1])
        voice_detected = random.choice([0, 1])
        duration = random.randint(1, 20)

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "presence": presence,
        "touch": touch,
        "voice_detected": voice_detected,
        "duration": duration,
    }


def insert_interaction(conn, interaction):
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO interactions (timestamp, presence, touch, voice_detected, duration)
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            interaction["timestamp"],
            interaction["presence"],
            interaction["touch"],
            interaction["voice_detected"],
            interaction["duration"],
        ),
    )
    conn.commit()


def main():
    print("Iniciando simulador de sensor do Totem Flexmedia...")
    print(f"Banco de dados: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    try:
        while True:
            interaction = generate_interaction()
            insert_interaction(conn, interaction)
            print("Interação registrada:", interaction)

            # Espera 5 segundos entre registros (bom para o vídeo)
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nSimulação finalizada pelo usuário.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

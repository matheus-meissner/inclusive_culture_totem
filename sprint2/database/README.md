# 🗄️ Banco de Dados – Sprint 2

Esta pasta contém o arquivo `totem.db`, utilizado para armazenar as interações do Totem Flexmedia.

- O banco é criado automaticamente pelo script `sensor_simulation/simulate_sensor.py`.
- A tabela principal é:

```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    presence INTEGER NOT NULL,
    touch INTEGER NOT NULL,
    voice_detected INTEGER NOT NULL,
    duration INTEGER NOT NULL
);

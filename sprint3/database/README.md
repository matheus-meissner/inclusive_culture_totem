# 🗄️ Banco de Dados — Sprint 2  
_Repositório: `sprint2/database/`_

Esta pasta contém o banco de dados **`totem.db`**, utilizado para armazenar todas as interações simuladas do Totem Flexmedia ao longo da Sprint 2.

O banco é criado **automaticamente** pelo script:
```
sprint2/sensor_simulation/simulate_sensor.py
```


Sempre que o simulador é executado, novos registros são inseridos diretamente na tabela principal `interactions`.

---

## 📌 Estrutura da Tabela `interactions`

A tabela utilizada na Sprint 2 foi projetada para representar com fidelidade os dados coletados pelos sensores simulados (presença, toque, voz e duração).

```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    presence INTEGER NOT NULL,
    touch INTEGER NOT NULL,
    voice_detected INTEGER NOT NULL,
    duration INTEGER NOT NULL
);
```

---

# 📘 Campos e seu propósito
```
Campo	Tipo	Descrição
id	INTEGER	Identificador único do registro (autoincremento).
timestamp	TEXT	Data e hora da interação registrada.
presence	INTEGER	1 se há alguém diante do totem, 0 caso contrário.
touch	INTEGER	1 se houve toque no display, 0 caso contrário.
voice_detected	INTEGER	1 se um comando de voz foi detectado.
duration	INTEGER	Tempo de permanência em segundos.
```

---

# 🧪 Como o banco é alimentado?

A cada 5 segundos, o simulador gera um novo evento contendo:

- presença detectada ou não
- toque ou ausência de toque
- comando de voz ou não
- duração estimada
- timestamp do evento

E insere no banco SQLite automaticamente.

---

# 📝 Como inspecionar o banco?

Você pode visualizar os dados com qualquer ferramenta SQLite, por exemplo:

🔸 Via terminal
```
sqlite3 totem.db
SELECT * FROM interactions LIMIT 10;
```

🔸 Via Python
```
import sqlite3
import pandas as pd

conn = sqlite3.connect("totem.db")
df = pd.read_sql_query("SELECT * FROM interactions", conn)
df.head()
```

---

# 🖼️ Prints utilizados na documentação (PDF)

Os prints que comprovam o funcionamento do banco estão na pasta:
```
sprint2/docs/prints/
```

---

# ✔️ Conclusão

O banco atende 100% dos requisitos da Sprint 2:

✔ Banco SQL simples
✔ Estrutura coerente com sensores reais
✔ Persistência contínua dos eventos
✔ Integração total com a análise (notebook)
✔ Integração com o dashboard (Streamlit)

Este é o núcleo do pipeline de dados da sprint e base para as próximas entregas.

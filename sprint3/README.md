# 🧠 Sprint 2 — Totem Inteligente Inclusivo  
**Integração Sensores → SQL → Análise → Machine Learning → Dashboard**

Esta sprint marca o momento em que o Totem Inteligente Inclusivo passa a funcionar de ponta a ponta:  
simulação dos sensores, armazenamento estruturado em SQL, análises estatísticas, um modelo simples de Machine Learning e um dashboard totalmente interativo para visualizar insights em tempo quase real.

Repositório geral: https://github.com/matheus-meissner/inclusive_culture_totem  
Vídeo da Sprint 2: https://youtu.be/KuR6zuKEfyU

---

# 📌 1. Objetivo da Sprint 2

O foco desta sprint foi **transformar o planejamento técnico da Sprint 1 em uma cadeia operacional real**, validando todo o fluxo:

1. **Gerar dados simulados dos sensores** (presença, toque, voz, duração).  
2. **Persistir esses dados em um banco SQLite** para consultas e auditoria.  
3. **Processar e analisar métricas de uso** utilizando Python.  
4. **Criar um modelo supervisionado simples** usando o dataset gerado.  
5. **Exibir KPIs e gráficos em um dashboard Streamlit**, consumindo diretamente o SQLite.

O resultado é um sistema funcional e conectado – exatamente como um totem real faria no mundo físico.

---

# 🏗️ 2. Estrutura da Pasta `sprint2/`
```
sprint2/
│
├── sensor_simulation/
│   └── simulate_sensor.py
│
├── database/
│   ├── README.md
│   └── totem.db
│
├── analysis/
│   ├── analysis.ipynb
│   └── dashboard/
│       └── app.py
│
├── docs/
│   └── prints/
│       ├── fluxo_sprint2.png
│       ├── simulador_rodando.png
│       ├── celula1_imports_conexao.png
│       ├── celula2_conversao_limpeza.png
│       ├── celula3_feature_engineering.png
│       ├── celula4_ativacoes_dia.png
│       ├── celula4_distribuicao_tipos.png
│       ├── celula5_classification_report.png
│       ├── streamlit_ativacoes_hora.png
│       ├── streamlit_tabela_dados_bruta.png
│       └── (demais prints da sprint)
│
└── README.md   ← este arquivo
```

---

# 🟦 3. Módulo 1 — Simulador de Sensores  
📁 `sensor_simulation/simulate_sensor.py`

Um totem real utiliza **ESP32 + sensor de presença (PIR) + microfone + toque**.  
Nesta sprint, isso foi replicado por meio de um simulador Python que:

- gera dados a cada **5 segundos**  
- simula presença  
- simula toque  
- simula detecção de voz  
- calcula a duração da interação  
- grava diretamente no banco SQL  

Os dados gerados seguem o esquema:
```
| Campo           | Tipo | Descrição |
|----------------|------|-----------|
| `timestamp`     | str  | Momento da interação |
| `presence`      | int  | 1 = usuário presente |
| `touch`         | int  | 1 = toque detectado |
| `voice_detected`| int  | 1 = interação por voz |
| `duration`      | int  | segundos de permanência |
```
Este módulo inicia o fluxo do ecossistema do totem.

---

# 🟫 4. Módulo 2 — Armazenamento SQL  
📁 `database/totem.db`

A Sprint 2 exige explicitamente um **banco SQL simples**, portanto foi utilizada a solução ideal para uso local: **SQLite**.

A tabela criada:
```
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    presence INTEGER,
    touch INTEGER,
    voice_detected INTEGER,
    duration INTEGER
);
```

## Por que SQLite?

- não requer servidor
- leve e simples de demonstrar
- atende exatamente o requisito da sprint
- pode ser lido diretamente pelo dashboard

---

# 🟩 5. Módulo 3 — Análise dos Dados

📁 `analysis/analysis.ipynb`

## O notebook realiza:

✔ Pré-processamento

- leitura do SQLite
- conversão do timestamp
- remoção de duplicações
- limpeza e validação das entradas

✔ Feature Engineering

- criação da variável houve_interacao
- classificação automática da interação em:
- rapida
- media
- longa
- sem_interacao

✔ Análises estatísticas

- ativações por dia
- ativações por hora
- presença × toque × voz
- evolução temporal

✔ Visualizações (matplotlib)

- número de ativações
- distribuição dos tipos de interação
- timeline de uso
- Essas análises servem de base para o dashboard (Módulo 5).

---

# 🟧 6. Módulo 4 — Machine Learning Supervisionado

✔ Requisito obrigatório da Sprint 2 atendido

O notebook treina um modelo RandomForestClassifier para classificar se uma interação é:

- rápida
- não rápida
- Features usadas:
- presence
- touch
- voice_detected
- duration

Métricas exibidas:

- accuracy
- precision
- recall
- f1-score
- matriz de confusão

O objetivo não é desenvolver um modelo avançado, mas sim demonstrar domínio do pipeline de dados + ML.

--- 

# 🟦 7. Módulo 5 — Dashboard em Streamlit

📁 `analysis/dashboard/app.py`

O painel consome diretamente o banco SQLite e exibe:

✔ KPIs Principais

- total de registros
- ativações (presence = 1)
- duração média
- total de interações com permanência

✔ Gráficos

- ativações ao longo do tempo
- distribuição dos tipos de interação
- ativações por dia
- ativações por hora

✔ Recursos adicionais

- atualização em tempo real
- tabela de dados bruta (últimos 300 registros)

Este dashboard representa exatamente o que a Flexmedia espera:
visualização interativa de métricas geradas a partir dos sensores.

---

# 🎬 8. Demonstração em Vídeo

📌 A sprint exige um vídeo com até 5 minutos contendo:

- execução do simulador
- visualização do banco sendo atualizado
- análises do notebook
- modelo ML funcionando
- dashboard rodando

O vídeo está publicado e atende totalmente aos critérios:
▶️ https://youtu.be/KuR6zuKEfyU

---

# 🏁 9. Conclusão da Sprint 2

A Sprint 2 foi implementada de forma integral, entregando:

✔ pipeline completo
✔ conexão sensores → SQL
✔ análise estatística
✔ modelo supervisionado funcional
✔ dashboard interativo
✔ documentação técnica
✔ vídeo demonstrativo

Isso cria as bases sólidas para as próximas etapas da solução, onde módulos mais inteligentes serão adicionados.

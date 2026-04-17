# 🏛️ Sprint 4 — Tótem Inteligente Inclusivo

**Projeto:** Challenge Flexmedia — FIAP  
**Aluno:** Matheus Meissner | RM567080  
**Sprint:** 4 (Entrega Final)  
**Repositório:** https://github.com/matheus-meissner/inclusive_culture_totem

---

## 🎯 Objetivo da Sprint 4

Evoluir o protótipo do Tótem Inteligente, incorporando:

- **Chatbot com NLP local** — assistente virtual que interpreta perguntas dos visitantes e responde de forma contextualizada, 100% offline
- **Visão Computacional** — detecção de presença, faixa etária, emoção e zona de atenção (câmera real via OpenCV ou simulação inteligente)
- **Reconhecimento de Voz** — transcrição de comandos falados (microfone real via SpeechRecognition ou simulação)
- **Dashboard completo** — 5 abas interativas integrando todos os módulos
- **Relatório analítico final** — gerado automaticamente com métricas de todos os módulos

---

## 🚀 Execução Rápida (Pipeline Completo)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Rodar pipeline completo (dados + ML + visão + voz + chat + relatório)
cd sprint4/
python main.py all

# 3. Abrir dashboard
streamlit run dashboard/app.py
```

O comando `all` executa automaticamente:
1. `init-db` — cria/valida schema com 6 tabelas
2. `bulk-ingest` — gera 3.000 interações simuladas (5 devices, 7 dias)
3. `train` — treina RandomForest + baseline + sanity check
4. `predict` — classifica todas as interações
5. `vision-bulk` — gera 500 eventos de visão computacional
6. `voice-bulk` — gera 200 eventos de reconhecimento de voz
7. `simulate-chat` — simula 30 sessões de chatbot
8. `report` — gera `reports/report.md`

---

## 🏗️ Estrutura do Projeto

```
sprint4/
│
├── main.py                     # Orquestrador CLI — pipeline completo
│
├── database/
│   ├── schema.sql              # 6 tabelas + views + triggers + índices
│   ├── db.py                   # Conexão SQLite, queries, inserts
│   └── totem.db                # Banco gerado após execução
│
├── sensor/
│   ├── simulate_sensor.py      # Gerador de eventos com variação temporal realista
│   └── ingest.py               # Validação, normalização e ingestão no banco
│
├── ml/
│   ├── train.py                # Treinamento: DummyClassifier (baseline) + RandomForest (FULL + sanity check)
│   ├── predict.py              # Inferência com gravação no banco
│   └── artifacts/
│       ├── model.pkl           # Modelo treinado
│       ├── metrics.json        # Métricas de avaliação
│       ├── confusion_matrix.png
│       └── confusion_matrix_no_duration.png
│
├── chatbot/
│   └── engine.py               # NLP local: detecção de intenção + geração de resposta + persistência
│
├── vision/
│   └── detector.py             # Visão computacional: OpenCV (câmera real) ou simulação inteligente
│
├── voice/
│   └── recognizer.py           # Voz: SpeechRecognition (microfone real) ou simulação contextual
│
├── dashboard/
│   └── app.py                  # Streamlit — 5 abas: Visão Geral, ML, Chatbot, Visão, Voz
│
├── reports/
│   ├── generate_report.py      # Gerador automático de relatório Markdown
│   └── report.md               # Relatório gerado (atualizado a cada execução)
│
├── requirements.txt            # Dependências Python
└── README_Sprint4.md           # Este arquivo
```

---

## 📦 Banco de Dados — Esquema Sprint 4

O banco SQLite evoluiu de 2 para **6 tabelas**:

| Tabela | Descrição |
|---|---|
| `interactions` | Eventos de sensor (presença, toque, voz, duração) |
| `predictions` | Previsões do modelo ML por interação |
| `chat_sessions` | Sessões do chatbot (device, idioma, acessibilidade) |
| `chat_messages` | Mensagens trocadas (usuário e assistente, com intenção detectada) |
| `vision_events` | Frames analisados (pessoa, faixa etária, emoção, atenção, zona) |
| `voice_events` | Eventos de voz (transcrição, confiança, duração, idioma) |

---

## 🤖 Módulo: Chatbot (NLP Local)

**Arquivo:** `chatbot/engine.py`

**Como funciona:**
1. A mensagem do visitante é normalizada (lowercase, sem acentos)
2. Detecção de intenção por contagem ponderada de keywords
3. Sub-intenção detectada para localização e horários (ex.: banheiro, biblioteca)
4. Resposta gerada a partir de base de conhecimento contextualizada
5. Sessão e mensagens persistidas no SQLite

**Intenções suportadas:**
`saudacao` | `horario` | `exposicao` | `evento` | `acessibilidade` | `localizacao` | `ingresso` | `acervo` | `despedida` | `ajuda`

**Demo interativo no terminal:**
```bash
python main.py chat-demo
```

---

## 👁️ Módulo: Visão Computacional

**Arquivo:** `vision/detector.py`

**Modo câmera real (quando disponível):**
- Captura frame via OpenCV
- Detecção de rostos via Haar Cascade
- Gravação no banco com metadados

**Modo simulado (padrão):**
- Simula detecção com padrões temporais realistas (mais pessoas de manhã e à tarde)
- Classifica faixa etária, emoção, zona e score de atenção
- Grava no banco `vision_events`

```bash
# Gerar 500 eventos simulados de visão
python main.py vision-bulk --n 500 --days 7
```

---

## 🎙️ Módulo: Reconhecimento de Voz

**Arquivo:** `voice/recognizer.py`

**Modo microfone real (quando disponível):**
- Usa `SpeechRecognition` com Whisper local (offline) ou Google (fallback online)
- Transcrição gravada no banco `voice_events`

**Modo simulado (padrão):**
- Seleciona frases realistas do contexto cultural (horários, exposições, acessibilidade...)
- Simula confiança e duração da transcrição

```bash
# Gerar 200 eventos de voz simulados
python main.py voice-bulk --n 200
```

---

## 📊 Dashboard — 5 Abas

**Arquivo:** `dashboard/app.py`  
**Executar:** `streamlit run dashboard/app.py`

| Aba | Conteúdo |
|---|---|
| 📊 Visão Geral | KPIs de sensores, eventos por hora/dia, categorias, acessibilidade |
| 🤖 Machine Learning | Métricas do modelo, sanity check, matriz de confusão, previsões |
| 💬 Chatbot | Interface de chat ao vivo + analytics de intenções e modos de entrada |
| 👁️ Visão Computacional | KPIs de detecção, distribuição por emoção/faixa etária/zona, demo ao vivo |
| 🎙️ Voz | KPIs de transcrição, distribuição, demo de simulação integrada com chatbot |

---

## 🔬 Machine Learning — Detalhes

**Problema:** Classificar nível de engajamento do visitante

**Target:**
- `quick` — duração ≤ 5s
- `normal` — duração 6–20s
- `engaged` — duração ≥ 21s

**Modelos treinados:**
1. `DummyClassifier` (baseline most_frequent) — referência
2. `RandomForestClassifier` FULL — modelo principal (com `duration_s`)
3. `RandomForestClassifier` NO duration — sanity check (sem a feature mais correlacionada)

**Métricas geradas:** acurácia, F1-macro, classification report, matriz de confusão

---

## ⚙️ Comandos CLI Disponíveis

```bash
python main.py init-db                          # Inicializa banco
python main.py bulk-ingest --n 3000 --days 7   # Gera interações em volume
python main.py ingest --seconds 60              # Ingestão contínua por tempo
python main.py train                            # Treina modelo ML
python main.py predict --limit 6000             # Gera previsões
python main.py vision-bulk --n 500              # Eventos de visão computacional
python main.py voice-bulk --n 200               # Eventos de voz
python main.py simulate-chat --sessions 30      # Simula sessões de chat
python main.py chat-demo                        # Chatbot interativo no terminal
python main.py report                           # Gera relatório analítico
python main.py all                              # Pipeline completo
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| SQLite | Banco de dados local (6 tabelas) |
| pandas | Manipulação e análise de dados |
| scikit-learn | Modelo ML (RandomForest, DummyClassifier, métricas) |
| Streamlit | Dashboard interativo |
| matplotlib | Geração de gráficos (matriz de confusão) |
| OpenCV *(opcional)* | Captura de câmera e detecção de rostos |
| SpeechRecognition *(opcional)* | Reconhecimento de voz via microfone |
| Whisper *(opcional)* | Transcrição offline de fala |

---

## ✅ Requisitos Atendidos (Sprint 4)

| Requisito | Status |
|---|---|
| Interface de interação com o usuário | ✅ Dashboard Streamlit + chatbot ao vivo |
| Entradas via texto, botões e voz | ✅ Chat por texto, botões rápidos, simulação de voz |
| Modelos de IA treinados com métricas | ✅ RandomForest + baseline + sanity check |
| Reconhecimento visual / presença | ✅ `vision/detector.py` (OpenCV ou simulado) |
| Armazenamento estruturado | ✅ SQLite com 6 tabelas |
| Fluxo completo de dados | ✅ Captura → Banco → ML → Análise → Visualização |
| Métricas de engajamento | ✅ KPIs, distribuições, padrões temporais |
| Chatbot com respostas automáticas | ✅ NLP local com 10 intenções |
| Conversão de voz em texto | ✅ `voice/recognizer.py` |
| Relatório analítico | ✅ `reports/report.md` gerado automaticamente |

---

## 🎬 Vídeo de Apresentação

> Link: *(inserir link do YouTube não listado após gravação)*

---

*Sprint 4 — Challenge Flexmedia | FIAP 2026*

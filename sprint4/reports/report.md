# Relatório Analítico Final — Tótem Inteligente Inclusivo (Sprint 4)

**Gerado em (UTC):** 2026-04-17T20:29:39Z
**Banco de dados:** `C:\Users\mathe\Desktop\sprint4_totem_inteligente_1\sprint4\database\totem.db`

---

## 1. Resumo Executivo

Sprint 4 do Tótem Inteligente Inclusivo. A solução integra coleta de dados via sensores,
Machine Learning supervisionado, visão computacional, reconhecimento de voz e chatbot interativo
— tudo rodando **100% localmente**, sem dependência de APIs externas.

**Pipeline:**
Sensores → SQLite → ML (RandomForest) → Visão Computacional → Voz → Chatbot → Dashboard → Relatório

**Período:** 2026-04-08 a 2026-04-17

---

## 2. KPIs Operacionais (Sensores)

| Indicador | Valor |
|---|---:|
| Eventos totais | 6,000 |
| Eventos válidos | 6,000 |
| Taxa de validade | 100.0% |
| Ativações com presença | 6,000 |
| Taxa de presença | 100.0% |
| Duração média (s) | 20.7 |
| % com touch | 64.6% |
| % com voz detectada | 25.4% |

### Horários de pico (presença)

| Hora (0–23) | Qtde |
|---|---:|
| 18 | 279 |
| 4 | 275 |
| 20 | 275 |
| 2 | 262 |
| 22 | 262 |
| 16 | 261 |
| 14 | 260 |
| 13 | 259 |

### Categorias de conteúdo mais acessadas

| Categoria | Qtde |
|---|---:|
| acervo | 1208 |
| informacoes | 1201 |
| cultura | 1198 |
| servicos | 1197 |
| agenda | 1196 |

---

## 3. Machine Learning

**Modelo:** RandomForestClassifier | **Versão:** rf_v2
**Treinado em:** 2026-04-17T20:29:30Z | **Linhas:** 6000
**Target:** `quick` (≤5s), `normal` (6–20s), `engaged` (≥21s)

| Indicador | Valor |
|---|---:|
| Baseline Accuracy | 0.3333 |
| Baseline F1-macro | 0.1667 |
| RF Accuracy (FULL) | 1.0000 |
| RF F1-macro (FULL) | 1.0000 |
| RF Accuracy (sem duration_s) | 0.3083 |

### Distribuição de previsões

| Classe prevista | Qtde |
|---|---:|
| quick | 2000 |
| engaged | 2000 |
| normal | 2000 |

---

## 4. Chatbot — Assistente Virtual (NLP Local)

| Indicador | Valor |
|---|---:|
| Sessões iniciadas | 63 |
| Total de mensagens | 496 |
| Média mensagens/sessão | 7.9 |
| Mensagens do usuário | 248 |

### Intenções detectadas

| Intenção | Qtde |
|---|---:|
| horario | 60 |
| localizacao | 38 |
| despedida | 35 |
| exposicao | 30 |
| acessibilidade | 30 |
| ingresso | 20 |
| saudacao | 18 |
| evento | 17 |

### Modos de entrada

| Modo | Qtde |
|---|---:|
| touch | 89 |
| text | 87 |
| voice | 72 |

---

## 5. Visão Computacional

| Indicador | Valor |
|---|---:|
| Frames analisados | 1,035 |
| Com pessoa detectada | 356 |
| Taxa de presença detectada | 34.4% |
| Score médio de atenção | 0.625 |

### Faixa etária detectada

| Faixa etária | Qtde |
|---|---:|
| jovem | 135 |
| adulto | 133 |
| idoso | 46 |
| crianca | 42 |

### Emoção detectada

| Emoção | Qtde |
|---|---:|
| neutro | 137 |
| curioso | 92 |
| feliz | 87 |
| confuso | 40 |

### Zonas de interação

| Zona | Qtde |
|---|---:|
| Mapa do Espaço | 80 |
| Painel de Acessibilidade | 75 |
| Tela Principal | 72 |
| Agenda/Eventos | 70 |
| Busca de Conteúdo | 59 |

---

## 6. Reconhecimento de Voz

| Indicador | Valor |
|---|---:|
| Eventos registrados | 404 |
| Transcrições bem-sucedidas | 404 |
| Taxa de sucesso | 100.0% |
| Confiança média | 86% |

---

## 7. Insights e Padrões de Comportamento

- **Horário de pico:** 18h com 279 ativações.
- **Conteúdo mais acessado:** `acervo` (1208 vezes).
- **Intenção de chat dominante:** `horario` (60 ocorrências).
- **Faixa etária predominante:** `jovem` (135 detecções).
- **Emoção predominante:** `neutro` (137 detecções).
- **Classe de engajamento dominante:** `quick`.

**Interpretações:**
- Visitantes `engaged` indicam alto interesse — momentos ideais para conteúdo aprofundado.
- Emoção `curioso` correlaciona com maior atenção, validando conteúdo interativo.
- Modo `touch` dominante indica que interface física é preferida ao teclado.
- Picos por hora orientam manutenção e alocação de equipe.

---

## 8. Arquitetura Técnica

```
sprint4/
├── main.py                 # Orquestrador CLI
├── database/schema.sql     # 6 tabelas: interactions, predictions, chat_sessions,
│                           #            chat_messages, vision_events, voice_events
├── sensor/                 # Simulador + ingestão
├── ml/                     # RandomForest + baseline + sanity check + artifacts
├── chatbot/engine.py       # NLP local: intenção + resposta + persistência
├── vision/detector.py      # Detecção presença/emoção (OpenCV ou simulado)
├── voice/recognizer.py     # Speech-to-text (SpeechRecognition ou simulado)
├── dashboard/app.py        # Streamlit 5 abas
└── reports/                # Relatório automático Markdown
```

---

## 9. Integridade e Segurança

- Validação na ingestão (0/1, timestamps, duration)
- UNIQUE constraints por device/timestamp
- Rastreabilidade: device_id, session_id, source, event_timestamp
- Trigger: presença=0 com duração alta → inválido

---

## 10. Limitações e Próximos Passos

- Dados simulados; pipeline equivalente ao cenário real com hardware.
- Chatbot pode evoluir para LLM local (Ollama + LLaMA) sem alterar a arquitetura.
- Visão pode ser expandida com YOLO para detecção mais precisa.
- Voz pode usar Vosk para reconhecimento offline completo.

---

**Fim do relatório — Sprint 4.**

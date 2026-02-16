# Relatório Automático — Totem Inteligente Inclusivo (Sprint 3)

**Gerado em (UTC):** 2026-02-16T15:31:51Z  
**Banco:** `C:\Users\mathe\Desktop\matheus_meissner\dev\inclusive_culture_totem\sprint3\database\totem.db`  

---

## 1) Resumo Executivo (Pipeline Integrado)

Este relatório comprova a execução ponta a ponta do sistema:

**Sensores (simulados/reais) → SQLite → Treino ML → Inferência (predictions) → Dashboards/Insights**

Período coberto pelos dados: **2026-02-16 13:00:00 UTC → 2026-02-16 13:00:00 UTC**  
Devices observados: **simulator-01, simulator-02, simulator-03, simulator-04, simulator-05**  
Fontes (`source`): **simulated**

---

## 2) KPIs de Uso do Totem

| Indicador | Valor |
|---|---:|
| Eventos totais | 5543 |
| Eventos válidos | 5543 |
| Eventos inválidos | 0 |
| Taxa de validade | 100.0% |
| Ativações (presença=1) | 5445 |
| Taxa de presença | 98.2% |
| Duração média (s) | 19.4 |
| % com toque (touch=1) | 64.1% |
| % com voz (voice_detected=1) | 24.8% |

---

## 3) Padrões Temporais (Horários/Dias de Pico)

### 3.1 Horas com mais ativações (presença=1)
| Hora (0–23) | Qtde |
|---|---:|
| 13.0 | 1 |

### 3.2 Dias com mais ativações (presença=1)
| Dia | Qtde |
|---|---:|
| 2026-02-16 | 1 |

---

## 4) Machine Learning (Classificação) — Métricas e Qualidade

**Problema:** classificar nível de engajamento por evento com base em sinais de interação.  
**Target:** `quick` (≤5s), `normal` (6–20s), `engaged` (≥21s).

**Modelo:** RandomForestClassifier  
**Versão:** rf_v2  
**Treinado em:** 2026-02-16T15:31:51Z  
**Linhas usadas no treino:** 5543

### 4.1 Métricas (Baseline vs Modelo)
| Indicador | Valor |
|---|---:|
| Baseline Accuracy (most_frequent) | 0.3553 |
| Baseline F1-macro | 0.1748 |
| RF Accuracy | - |
| RF F1-macro | - |

> Observação: recomenda-se sempre comparar com baseline para evidenciar ganho real do modelo.

---

## 5) Previsões em Produção (Gravadas no Banco)

### 5.1 Distribuição de classes previstas
| Classe | Qtde |
|---|---:|
| quick | 1967 |
| normal | 1857 |
| engaged | 1719 |

### 5.2 Confiança média (probabilidade) por classe
| Classe | Confiança (%) |
|---|---:|
| engaged | 96 |
| quick | 95 |
| normal | 85 |

### 5.3 Últimas previsões (amostra)
| predicted_at | interaction_id | pred_label | pred_proba | duration_s | presence | touch | voice_detected | device_id | source |
|---|---|---|---|---|---|---|---|---|---|
| 2026-02-16 15:31:51 UTC | 5543 | normal | 0.8911 | 10 | 1 | 0 | 0 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5542 | normal | 0.8956 | 18 | 1 | 1 | 0 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5541 | quick | 0.9252 | 3 | 1 | 1 | 1 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5540 | quick | 0.9401 | 1 | 1 | 0 | 1 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5539 | quick | 0.9404 | 2 | 1 | 1 | 0 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5538 | quick | 0.9252 | 4 | 1 | 1 | 1 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5537 | quick | 0.9765 | 1 | 0 | 0 | 0 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5536 | quick | 0.9371 | 5 | 1 | 1 | 0 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5535 | quick | 0.9765 | 0 | 0 | 0 | 0 | simulator-01 | simulated |
| 2026-02-16 15:31:51 UTC | 5534 | quick | 0.9765 | 2 | 0 | 0 | 0 | simulator-01 | simulated |

---

## 6) Insights (para decisão / impacto)

- **Uso**: 5543 eventos registrados (100.0% válidos) no período analisado.
- **Presença detectada**: 5445 ocorrências (98.2% dos eventos).
- **Interação média**: 19.4s por evento; toque em 64.1% e voz em 24.8%.
- **Classe prevista dominante**: `quick` (1967 previsões).
- **Horário de pico** (presença): **13h** com **1** ativações.

**Interpretação prática:**  
- Previsões `engaged` sugerem **maior interesse** (tempo alto), útil para priorizar conteúdos e ajustar acessibilidade.  
- Picos por hora/dia indicam **melhor janela de atendimento** e planejamento de equipe/infraestrutura.

---

## 7) Integridade e Segurança (conceitual e aplicável)

- **Validação de entrada** na ingestão (normalização 0/1, duration>=0, timestamp ISO).
- **Restrições no banco** (chaves + UNIQUE para evitar duplicidade por device/timestamp).
- **Rastreabilidade** por `device_id`, `source`, `session_id` e timestamps (`event_timestamp`, `ingested_at`).

---

## 8) Limitações e Próximos Passos

- Os dados são **simulados** (ou parcialmente simulados), portanto padrões refletem a lógica do simulador; ainda assim, o pipeline e as validações são equivalentes ao cenário real.
- A métrica pode oscilar caso haja **desbalanceamento** entre classes (ex.: poucos `engaged`). Recomendação: manter volume 3k+ e/ou balancear no simulador.
- O modelo atual é supervisionado e simples (baseline vs RandomForest); melhorias possíveis incluem tuning de hiperparâmetros, validação cruzada e explicabilidade (feature importance).

---

**Fim do relatório.**

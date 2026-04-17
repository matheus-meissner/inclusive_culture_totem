"""
reports/generate_report.py — Relatório Analítico Sprint 4
Inclui: KPIs sensor, ML, chatbot, visão computacional, voz.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

REPORTS_DIR = Path(__file__).resolve().parent
SPRINT4_DIR = REPORTS_DIR.parent
sys.path.insert(0, str(SPRINT4_DIR))

from database.db import get_conn, init_db

DB_PATH = SPRINT4_DIR / "database" / "totem.db"
ARTIFACTS_DIR = SPRINT4_DIR / "ml" / "artifacts"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
REPORT_PATH = REPORTS_DIR / "report.md"


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def md_table(rows: List[tuple]) -> str:
    lines = ["| Indicador | Valor |", "|---|---:|"]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def md_series(s: pd.Series, col: str, top_n: int = 8) -> str:
    if s is None or s.empty:
        return "_(sem dados)_"
    lines = [f"| {col} | Qtde |", "|---|---:|"]
    for idx, val in s.head(top_n).items():
        lines.append(f"| {idx} | {int(val)} |")
    return "\n".join(lines)


def load_all() -> Dict[str, Any]:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)

        def safe_query(sql):
            try:
                return pd.read_sql_query(sql, conn)
            except Exception:
                return pd.DataFrame()

        return {
            "interactions": safe_query("SELECT * FROM interactions"),
            "predictions": safe_query("SELECT * FROM predictions"),
            "chat_sessions": safe_query("SELECT * FROM chat_sessions"),
            "chat_messages": safe_query("SELECT * FROM chat_messages"),
            "vision": safe_query("SELECT * FROM vision_events"),
            "voice": safe_query("SELECT * FROM voice_events"),
            "metrics": read_json(METRICS_PATH),
        }
    finally:
        conn.close()


def build_report(data: Dict[str, Any]) -> str:
    now = iso_now()
    idf = data["interactions"]
    pdf = data["predictions"]
    csdf = data["chat_sessions"]
    cmdf = data["chat_messages"]
    vdf = data["vision"]
    vodf = data["voice"]
    metrics = data["metrics"] or {}

    # Interactions
    if idf.empty:
        total_i = valid_i = presence_i = 0
        avg_dur = touch_rate = voice_rate = 0.0
        date_range = "-"
        peak_hours = pd.Series(dtype=int)
        content_dist = pd.Series(dtype=int)
    else:
        total_i = len(idf)
        valid_i = int(idf["is_valid"].sum()) if "is_valid" in idf.columns else total_i
        presence_i = int(idf["presence"].sum())
        avg_dur = float(idf["duration_s"].mean())
        touch_rate = float(idf["touch"].mean() * 100)
        voice_rate = float(idf["voice_detected"].mean() * 100)
        idf["ts"] = pd.to_datetime(idf["event_timestamp"], errors="coerce", utc=True)
        date_range = f"{idf['ts'].min().strftime('%Y-%m-%d')} a {idf['ts'].max().strftime('%Y-%m-%d')}"
        idf["hour"] = idf["ts"].dt.hour
        peak_hours = idf.groupby("hour")["presence"].sum().sort_values(ascending=False)
        content_dist = idf["content_category"].value_counts() if "content_category" in idf.columns else pd.Series(dtype=int)

    # ML
    baseline_acc = metrics.get("baseline_accuracy")
    baseline_f1 = metrics.get("baseline_f1_macro")
    rf_acc = metrics.get("rf_full_accuracy")
    rf_f1 = metrics.get("rf_full_f1_macro")
    rf_nd_acc = metrics.get("rf_no_duration_accuracy")
    pred_dist = pdf["pred_label"].value_counts() if not pdf.empty and "pred_label" in pdf.columns else pd.Series(dtype=int)

    # Chatbot
    total_sessions = len(csdf)
    total_messages = len(cmdf)
    avg_msgs = float(csdf["total_messages"].mean()) if not csdf.empty and "total_messages" in csdf.columns else 0.0
    user_msgs = cmdf[cmdf["role"] == "user"] if not cmdf.empty else pd.DataFrame()
    intent_dist = user_msgs["intent"].value_counts() if not user_msgs.empty and "intent" in user_msgs.columns else pd.Series(dtype=int)
    input_mode_dist = user_msgs["input_mode"].value_counts() if not user_msgs.empty and "input_mode" in user_msgs.columns else pd.Series(dtype=int)

    # Vision
    total_frames = len(vdf)
    frames_with_person = int(vdf["person_detected"].sum()) if not vdf.empty else 0
    presence_rate_v = frames_with_person / total_frames * 100 if total_frames > 0 else 0.0
    avg_attention = float(vdf[vdf["person_detected"] == 1]["attention_score"].mean()) if not vdf.empty else 0.0
    age_dist = vdf["age_group"].dropna().value_counts() if not vdf.empty else pd.Series(dtype=int)
    emotion_dist = vdf["emotion"].dropna().value_counts() if not vdf.empty else pd.Series(dtype=int)
    zone_dist = vdf["zone"].dropna().value_counts() if not vdf.empty else pd.Series(dtype=int)

    # Voice
    total_voice = len(vodf)
    processed_voice = int(vodf["processed"].sum()) if not vodf.empty else 0
    success_rate_v = processed_voice / total_voice * 100 if total_voice > 0 else 0.0
    avg_conf_voice = float(vodf[vodf["processed"] == 1]["confidence"].mean()) if not vodf.empty else 0.0

    # Insights dinâmicos
    insights_lines = []
    if not peak_hours.empty:
        insights_lines.append(f"- **Horário de pico:** {int(peak_hours.index[0])}h com {int(peak_hours.iloc[0])} ativações.")
    if not content_dist.empty:
        insights_lines.append(f"- **Conteúdo mais acessado:** `{content_dist.index[0]}` ({int(content_dist.iloc[0])} vezes).")
    if not intent_dist.empty:
        insights_lines.append(f"- **Intenção de chat dominante:** `{intent_dist.index[0]}` ({int(intent_dist.iloc[0])} ocorrências).")
    if not age_dist.empty:
        insights_lines.append(f"- **Faixa etária predominante:** `{age_dist.index[0]}` ({int(age_dist.iloc[0])} detecções).")
    if not emotion_dist.empty:
        insights_lines.append(f"- **Emoção predominante:** `{emotion_dist.index[0]}` ({int(emotion_dist.iloc[0])} detecções).")
    if not pred_dist.empty:
        insights_lines.append(f"- **Classe de engajamento dominante:** `{pred_dist.index[0]}`.")
    insights_text = "\n".join(insights_lines) if insights_lines else "_(sem dados suficientes para insights)_"

    return f"""# Relatório Analítico Final — Tótem Inteligente Inclusivo (Sprint 4)

**Gerado em (UTC):** {now}
**Banco de dados:** `{DB_PATH}`

---

## 1. Resumo Executivo

Sprint 4 do Tótem Inteligente Inclusivo. A solução integra coleta de dados via sensores,
Machine Learning supervisionado, visão computacional, reconhecimento de voz e chatbot interativo
— tudo rodando **100% localmente**, sem dependência de APIs externas.

**Pipeline:**
Sensores → SQLite → ML (RandomForest) → Visão Computacional → Voz → Chatbot → Dashboard → Relatório

**Período:** {date_range}

---

## 2. KPIs Operacionais (Sensores)

{md_table([
    ("Eventos totais", f"{total_i:,}"),
    ("Eventos válidos", f"{valid_i:,}"),
    ("Taxa de validade", f"{valid_i/total_i*100:.1f}%" if total_i > 0 else "0%"),
    ("Ativações com presença", f"{presence_i:,}"),
    ("Taxa de presença", f"{presence_i/total_i*100:.1f}%" if total_i > 0 else "0%"),
    ("Duração média (s)", f"{avg_dur:.1f}"),
    ("% com touch", f"{touch_rate:.1f}%"),
    ("% com voz detectada", f"{voice_rate:.1f}%"),
])}

### Horários de pico (presença)

{md_series(peak_hours, "Hora (0–23)")}

### Categorias de conteúdo mais acessadas

{md_series(content_dist, "Categoria")}

---

## 3. Machine Learning

**Modelo:** {metrics.get("model_name", "RandomForestClassifier")} | **Versão:** {metrics.get("model_version", "-")}
**Treinado em:** {metrics.get("trained_at", "-")} | **Linhas:** {metrics.get("rows_used", "-")}
**Target:** `quick` (≤5s), `normal` (6–20s), `engaged` (≥21s)

{md_table([
    ("Baseline Accuracy", f"{baseline_acc:.4f}" if baseline_acc is not None else "-"),
    ("Baseline F1-macro", f"{baseline_f1:.4f}" if baseline_f1 is not None else "-"),
    ("RF Accuracy (FULL)", f"{rf_acc:.4f}" if rf_acc is not None else "-"),
    ("RF F1-macro (FULL)", f"{rf_f1:.4f}" if rf_f1 is not None else "-"),
    ("RF Accuracy (sem duration_s)", f"{rf_nd_acc:.4f}" if rf_nd_acc is not None else "-"),
])}

### Distribuição de previsões

{md_series(pred_dist, "Classe prevista")}

---

## 4. Chatbot — Assistente Virtual (NLP Local)

{md_table([
    ("Sessões iniciadas", total_sessions),
    ("Total de mensagens", total_messages),
    ("Média mensagens/sessão", f"{avg_msgs:.1f}"),
    ("Mensagens do usuário", len(user_msgs)),
])}

### Intenções detectadas

{md_series(intent_dist, "Intenção")}

### Modos de entrada

{md_series(input_mode_dist, "Modo")}

---

## 5. Visão Computacional

{md_table([
    ("Frames analisados", f"{total_frames:,}"),
    ("Com pessoa detectada", f"{frames_with_person:,}"),
    ("Taxa de presença detectada", f"{presence_rate_v:.1f}%"),
    ("Score médio de atenção", f"{avg_attention:.3f}"),
])}

### Faixa etária detectada

{md_series(age_dist, "Faixa etária")}

### Emoção detectada

{md_series(emotion_dist, "Emoção")}

### Zonas de interação

{md_series(zone_dist, "Zona")}

---

## 6. Reconhecimento de Voz

{md_table([
    ("Eventos registrados", f"{total_voice:,}"),
    ("Transcrições bem-sucedidas", f"{processed_voice:,}"),
    ("Taxa de sucesso", f"{success_rate_v:.1f}%"),
    ("Confiança média", f"{avg_conf_voice:.0%}"),
])}

---

## 7. Insights e Padrões de Comportamento

{insights_text}

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
"""


def main() -> None:
    print("== Sprint 4 | Report Generator ==")
    data = load_all()
    report = build_report(data)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Relatorio gerado: {REPORT_PATH}")
    for key, df in data.items():
        if hasattr(df, "__len__") and not isinstance(df, dict):
            print(f"  {key}: {len(df)} registros")
    print("OK")


if __name__ == "__main__":
    main()

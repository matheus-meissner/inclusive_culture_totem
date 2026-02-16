from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from database.db import get_conn, init_db


# ============================================================
# Paths robustos (Sprint 3)
# ============================================================
REPORTS_DIR = Path(__file__).resolve().parent
SPRINT3_DIR = REPORTS_DIR.parent

DB_PATH = SPRINT3_DIR / "database" / "totem.db"
ARTIFACTS_DIR = SPRINT3_DIR / "ml" / "artifacts"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
REPORT_MD_PATH = REPORTS_DIR / "report.md"


# ============================================================
# Helpers
# ============================================================
def iso_now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def md_table_from_series(series: pd.Series, col_name: str, top_n: int = 10) -> str:
    """
    Converte uma série (index->count) em tabela markdown.
    """
    if series is None or series.empty:
        return "_(sem dados)_"

    s = series.head(top_n)
    lines = []
    lines.append(f"| {col_name} | Qtde |")
    lines.append("|---|---:|")
    for idx, val in s.items():
        lines.append(f"| {idx} | {int(val)} |")
    return "\n".join(lines)


def md_key_value_table(rows: List[Tuple[str, Any]]) -> str:
    lines = ["| Indicador | Valor |", "|---|---:|"]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def pct(part: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return (part / total) * 100.0


def duration_class(d: int) -> str:
    if d <= 5:
        return "quick"
    if 6 <= d <= 20:
        return "normal"
    return "engaged"


# ============================================================
# Queries (puxando do banco)
# ============================================================

def load_interactions_df() -> pd.DataFrame:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        df = pd.read_sql_query(
            """
            SELECT
                id, device_id, source, session_id, event_timestamp,
                presence, touch, voice_detected, duration_s,
                location, interaction_zone, accessibility_mode,
                content_category, ui_language,
                is_valid, validation_notes, ingested_at
            FROM interactions
            """,
            conn
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", utc=True)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], errors="coerce", utc=True)
    df["date"] = df["event_timestamp"].dt.date
    df["hour"] = df["event_timestamp"].dt.hour

    # Classe por duração (alinhada ao target do ML)
    df["duration_class"] = df["duration_s"].fillna(0).astype(int).apply(duration_class)

    return df


def load_predictions_join_df(model_version: Optional[str] = None) -> pd.DataFrame:
    """
    JOIN predictions + interactions.
    Se model_version for None, pega a última versão que existe no DB.
    """
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)

        if model_version is None:
            row = conn.execute(
                "SELECT model_version FROM predictions ORDER BY predicted_at DESC LIMIT 1"
            ).fetchone()
            model_version = row[0] if row else None

        if not model_version:
            return pd.DataFrame()

        df = pd.read_sql_query(
            """
            SELECT
                p.id AS prediction_id,
                p.interaction_id,
                p.pred_label,
                p.pred_proba,
                p.model_name,
                p.model_version,
                p.trained_at,
                p.predicted_at,

                i.device_id,
                i.source,
                i.event_timestamp,
                i.presence,
                i.touch,
                i.voice_detected,
                i.duration_s,
                i.location,
                i.interaction_zone,
                i.content_category,
                i.accessibility_mode
            FROM predictions p
            JOIN interactions i ON i.id = p.interaction_id
            WHERE p.model_version = ?
            """,
            conn,
            params=(model_version,)
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", utc=True)
    df["predicted_at"] = pd.to_datetime(df["predicted_at"], errors="coerce", utc=True)
    df["date"] = df["event_timestamp"].dt.date
    df["hour"] = df["event_timestamp"].dt.hour

    return df


# ============================================================
# Report building
# ============================================================

@dataclass
class ReportContext:
    generated_at: str
    db_path: str
    interactions_count: int
    predictions_count: int
    model_version: Optional[str]
    metrics: Optional[Dict[str, Any]]


def compute_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "total_events": 0,
            "valid_events": 0,
            "invalid_events": 0,
            "valid_rate": 0.0,
            "presence_total": 0,
            "presence_rate": 0.0,
            "avg_duration_s": 0.0,
            "touch_rate": 0.0,
            "voice_rate": 0.0,
            "devices": [],
            "sources": [],
            "date_min": None,
            "date_max": None,
        }

    total = len(df)
    valid = int((df["is_valid"] == 1).sum()) if "is_valid" in df.columns else total
    invalid = total - valid
    presence_total = int(df["presence"].fillna(0).astype(int).sum())
    avg_duration = float(df["duration_s"].fillna(0).astype(int).mean())

    touch_rate = float(df["touch"].fillna(0).astype(int).mean())
    voice_rate = float(df["voice_detected"].fillna(0).astype(int).mean())

    devices = sorted([x for x in df["device_id"].dropna().unique().tolist()])
    sources = sorted([x for x in df["source"].dropna().unique().tolist()])

    date_min = df["event_timestamp"].min()
    date_max = df["event_timestamp"].max()

    return {
        "total_events": total,
        "valid_events": valid,
        "invalid_events": invalid,
        "valid_rate": pct(valid, total),
        "presence_total": presence_total,
        "presence_rate": pct(presence_total, total),
        "avg_duration_s": avg_duration,
        "touch_rate": touch_rate * 100.0,
        "voice_rate": voice_rate * 100.0,
        "devices": devices,
        "sources": sources,
        "date_min": date_min,
        "date_max": date_max,
    }


def compute_peaks(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Horários de pico e dias com mais presença.
    """
    if df.empty:
        return {"peak_hours": pd.Series(dtype=int), "peak_days": pd.Series(dtype=int)}

    # foco em presença (uso real do totem)
    dfp = df.copy()
    dfp["presence"] = dfp["presence"].fillna(0).astype(int)

    by_hour = dfp.groupby("hour")["presence"].sum().sort_values(ascending=False)
    by_day = dfp.groupby("date")["presence"].sum().sort_values(ascending=False)

    return {"peak_hours": by_hour, "peak_days": by_day}


def compute_pred_distribution(pred_df: pd.DataFrame) -> Dict[str, Any]:
    if pred_df.empty:
        return {
            "by_label": pd.Series(dtype=int),
            "avg_proba_by_label": pd.Series(dtype=float),
            "latest_rows": pd.DataFrame(),
        }

    by_label = pred_df["pred_label"].value_counts().sort_values(ascending=False)
    avg_proba_by_label = pred_df.groupby("pred_label")["pred_proba"].mean().sort_values(ascending=False)
    latest_rows = pred_df.sort_values("predicted_at", ascending=False).head(10)

    return {
        "by_label": by_label,
        "avg_proba_by_label": avg_proba_by_label,
        "latest_rows": latest_rows,
    }


def format_latest_predictions_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_(sem previsões)_"

    cols = ["predicted_at", "interaction_id", "pred_label", "pred_proba", "duration_s", "presence", "touch", "voice_detected", "device_id", "source"]
    df2 = df[cols].copy()

    # formata
    df2["predicted_at"] = df2["predicted_at"].dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    df2["pred_proba"] = df2["pred_proba"].astype(float).map(lambda x: f"{x:.4f}" if pd.notnull(x) else "-")

    # markdown table manual
    header = "| " + " | ".join(cols) + " |"
    sep = "|---" * len(cols) + "|"
    lines = [header, sep]
    for _, r in df2.iterrows():
        row = [str(r[c]) for c in cols]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_report_md(ctx: ReportContext, kpis: Dict[str, Any], peaks: Dict[str, Any], pred: Dict[str, Any]) -> str:
    date_min = kpis["date_min"]
    date_max = kpis["date_max"]

    date_range_str = "-"
    if pd.notnull(date_min) and pd.notnull(date_max):
        date_range_str = f"{date_min.strftime('%Y-%m-%d %H:%M:%S UTC')} → {date_max.strftime('%Y-%m-%d %H:%M:%S UTC')}"

    devices_str = ", ".join(kpis["devices"]) if kpis["devices"] else "-"
    sources_str = ", ".join(kpis["sources"]) if kpis["sources"] else "-"

    # Métricas do ML
    metrics = ctx.metrics or {}
    model_name = metrics.get("model_name", "RandomForestClassifier")
    model_version = metrics.get("model_version", ctx.model_version or "-")
    trained_at = metrics.get("trained_at", "-")
    rows_used = metrics.get("rows_used", "-")

    baseline_acc = metrics.get("baseline_accuracy", None)
    baseline_f1 = metrics.get("baseline_f1_macro", None)
    rf_acc = metrics.get("rf_accuracy", None)
    rf_f1 = metrics.get("rf_f1_macro", None)

    # Peaks
    peak_hours = peaks["peak_hours"]
    peak_days = peaks["peak_days"]

    # Distribuição de previsões
    by_label = pred["by_label"]
    avg_proba_by_label = pred["avg_proba_by_label"]
    latest_rows = pred["latest_rows"]

    # Insights simples (curtos e apresentáveis)
    insights = []
    insights.append(f"- **Uso**: {kpis['total_events']} eventos registrados ({kpis['valid_rate']:.1f}% válidos) no período analisado.")
    insights.append(f"- **Presença detectada**: {kpis['presence_total']} ocorrências ({kpis['presence_rate']:.1f}% dos eventos).")
    insights.append(f"- **Interação média**: {kpis['avg_duration_s']:.1f}s por evento; toque em {kpis['touch_rate']:.1f}% e voz em {kpis['voice_rate']:.1f}%.")

    if not by_label.empty:
        top_label = by_label.index[0]
        top_count = int(by_label.iloc[0])
        insights.append(f"- **Classe prevista dominante**: `{top_label}` ({top_count} previsões).")

    if not peak_hours.empty:
        insights.append(f"- **Horário de pico** (presença): **{int(peak_hours.index[0])}h** com **{int(peak_hours.iloc[0])}** ativações.")

    # Limitações (nota máxima: honestidade e plano de evolução)
    limitations = [
        "- Os dados são **simulados** (ou parcialmente simulados), portanto padrões refletem a lógica do simulador; ainda assim, o pipeline e as validações são equivalentes ao cenário real.",
        "- A métrica pode oscilar caso haja **desbalanceamento** entre classes (ex.: poucos `engaged`). Recomendação: manter volume 3k+ e/ou balancear no simulador.",
        "- O modelo atual é supervisionado e simples (baseline vs RandomForest); melhorias possíveis incluem tuning de hiperparâmetros, validação cruzada e explicabilidade (feature importance).",
    ]

    # Segurança / integridade (conceitual e aplicável)
    security_notes = [
        "- **Validação de entrada** na ingestão (normalização 0/1, duration>=0, timestamp ISO).",
        "- **Restrições no banco** (chaves + UNIQUE para evitar duplicidade por device/timestamp).",
        "- **Rastreabilidade** por `device_id`, `source`, `session_id` e timestamps (`event_timestamp`, `ingested_at`).",
    ]

    md = f"""# Relatório Automático — Totem Inteligente Inclusivo (Sprint 3)

**Gerado em (UTC):** {ctx.generated_at}  
**Banco:** `{ctx.db_path}`  

---

## 1) Resumo Executivo (Pipeline Integrado)

Este relatório comprova a execução ponta a ponta do sistema:

**Sensores (simulados/reais) → SQLite → Treino ML → Inferência (predictions) → Dashboards/Insights**

Período coberto pelos dados: **{date_range_str}**  
Devices observados: **{devices_str}**  
Fontes (`source`): **{sources_str}**

---

## 2) KPIs de Uso do Totem

{md_key_value_table([
    ("Eventos totais", kpis["total_events"]),
    ("Eventos válidos", kpis["valid_events"]),
    ("Eventos inválidos", kpis["invalid_events"]),
    ("Taxa de validade", f"{kpis['valid_rate']:.1f}%"),
    ("Ativações (presença=1)", kpis["presence_total"]),
    ("Taxa de presença", f"{kpis['presence_rate']:.1f}%"),
    ("Duração média (s)", f"{kpis['avg_duration_s']:.1f}"),
    ("% com toque (touch=1)", f"{kpis['touch_rate']:.1f}%"),
    ("% com voz (voice_detected=1)", f"{kpis['voice_rate']:.1f}%"),
])}

---

## 3) Padrões Temporais (Horários/Dias de Pico)

### 3.1 Horas com mais ativações (presença=1)
{md_table_from_series(peak_hours, "Hora (0–23)", top_n=8)}

### 3.2 Dias com mais ativações (presença=1)
{md_table_from_series(peak_days, "Dia", top_n=7)}

---

## 4) Machine Learning (Classificação) — Métricas e Qualidade

**Problema:** classificar nível de engajamento por evento com base em sinais de interação.  
**Target:** `quick` (≤5s), `normal` (6–20s), `engaged` (≥21s).

**Modelo:** {model_name}  
**Versão:** {model_version}  
**Treinado em:** {trained_at}  
**Linhas usadas no treino:** {rows_used}

### 4.1 Métricas (Baseline vs Modelo)
{md_key_value_table([
    ("Baseline Accuracy (most_frequent)", f"{baseline_acc:.4f}" if baseline_acc is not None else "-"),
    ("Baseline F1-macro", f"{baseline_f1:.4f}" if baseline_f1 is not None else "-"),
    ("RF Accuracy", f"{rf_acc:.4f}" if rf_acc is not None else "-"),
    ("RF F1-macro", f"{rf_f1:.4f}" if rf_f1 is not None else "-"),
])}

> Observação: recomenda-se sempre comparar com baseline para evidenciar ganho real do modelo.

---

## 5) Previsões em Produção (Gravadas no Banco)

### 5.1 Distribuição de classes previstas
{md_table_from_series(by_label, "Classe", top_n=10)}

### 5.2 Confiança média (probabilidade) por classe
{( "_(sem dados)_" if avg_proba_by_label.empty else md_table_from_series((avg_proba_by_label * 100.0).round(2), "Classe", top_n=10)).replace("Qtde", "Confiança (%)")}

### 5.3 Últimas previsões (amostra)
{format_latest_predictions_table(latest_rows)}

---

## 6) Insights (para decisão / impacto)

{chr(10).join(insights)}

**Interpretação prática:**  
- Previsões `engaged` sugerem **maior interesse** (tempo alto), útil para priorizar conteúdos e ajustar acessibilidade.  
- Picos por hora/dia indicam **melhor janela de atendimento** e planejamento de equipe/infraestrutura.

---

## 7) Integridade e Segurança (conceitual e aplicável)

{chr(10).join(security_notes)}

---

## 8) Limitações e Próximos Passos

{chr(10).join(limitations)}

---

**Fim do relatório.**
"""
    return md


def main() -> None:
    generated_at = iso_now_utc()

    # 1) Load data
    interactions_df = load_interactions_df()

    # 2) Counts básicos
    interactions_count = int(len(interactions_df))
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        predictions_count = conn.execute("SELECT count(*) FROM predictions").fetchone()[0]
    finally:
        conn.close()

    # 3) Metrics.json
    metrics = read_json_safe(METRICS_PATH)
    model_version = metrics.get("model_version") if metrics else None

    # 4) Predictions join
    pred_df = load_predictions_join_df(model_version=model_version)

    # 5) Compute
    kpis = compute_kpis(interactions_df)
    peaks = compute_peaks(interactions_df)
    pred_stats = compute_pred_distribution(pred_df)

    # 6) Build report
    ctx = ReportContext(
        generated_at=generated_at,
        db_path=str(DB_PATH),
        interactions_count=interactions_count,
        predictions_count=int(predictions_count),
        model_version=model_version,
        metrics=metrics,
    )

    report_md = build_report_md(ctx, kpis, peaks, pred_stats)

    # 7) Write file
    REPORT_MD_PATH.write_text(report_md, encoding="utf-8")

    print("== Sprint 3 | Report Generator ==")
    print(f"DB: {DB_PATH}")
    print(f"Metrics: {METRICS_PATH if METRICS_PATH.exists() else '(não encontrado)'}")
    print(f"Interactions: {interactions_count}")
    print(f"Predictions: {predictions_count}")
    print(f"Report generated: {REPORT_MD_PATH}")
    print("✅ report.md atualizado com sucesso.")


if __name__ == "__main__":
    main()

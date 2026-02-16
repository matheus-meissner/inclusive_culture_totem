from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

from database.db import (
    get_conn,
    init_db,
)

# ============================================================
# Paths robustos (Sprint 3)
# ============================================================
DASH_DIR = Path(__file__).resolve().parent
SPRINT3_DIR = DASH_DIR.parent
DB_PATH = SPRINT3_DIR / "database" / "totem.db"

ARTIFACTS_DIR = SPRINT3_DIR / "ml" / "artifacts"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
CM_PATH = ARTIFACTS_DIR / "confusion_matrix.png"

# ============================================================
# Helpers
# ============================================================

def _safe_read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@st.cache_data(ttl=5, show_spinner=False)
def load_interactions_df() -> pd.DataFrame:
    """
    Carrega interações da tabela interactions (Sprint 3).
    """
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        df = pd.read_sql_query(
            """
            SELECT
                id,
                device_id,
                source,
                session_id,
                event_timestamp,
                presence,
                touch,
                voice_detected,
                duration_s,
                location,
                interaction_zone,
                accessibility_mode,
                content_category,
                ui_language,
                is_valid,
                validation_notes,
                ingested_at
            FROM interactions
            ORDER BY event_timestamp ASC
            """,
            conn,
        )
    finally:
        conn.close()

    if df.empty:
        return df

    # Parse timestamp
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", utc=True)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], errors="coerce", utc=True)

    # Features para dashboard
    df["date"] = df["event_timestamp"].dt.date
    df["hour"] = df["event_timestamp"].dt.hour
    df["had_presence"] = df["presence"].apply(lambda x: "sim" if int(x) == 1 else "não")

    # Classe de duração (compatível com o target do ML)
    def duration_class(d: Any) -> str:
        try:
            d = int(d)
        except Exception:
            d = 0
        if d <= 5:
            return "quick"
        if 6 <= d <= 20:
            return "normal"
        return "engaged"

    df["duration_class"] = df["duration_s"].apply(duration_class)

    return df


@st.cache_data(ttl=5, show_spinner=False)
def load_predictions_join_df(model_version: str = "rf_v1", limit: int = 2000) -> pd.DataFrame:
    """
    Carrega previsões com JOIN para análises e tabela de "últimas previsões".
    """
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
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
            ORDER BY p.predicted_at DESC
            LIMIT ?
            """,
            conn,
            params=(model_version, int(limit)),
        )
    finally:
        conn.close()

    if df.empty:
        return df

    df["predicted_at"] = pd.to_datetime(df["predicted_at"], errors="coerce", utc=True)
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", utc=True)

    return df


def apply_filters(
    df: pd.DataFrame,
    date_range: Tuple[pd.Timestamp, pd.Timestamp],
    device_id: str,
    source: str,
    presence_only: bool,
    valid_only: bool,
) -> pd.DataFrame:
    if df.empty:
        return df

    start, end = date_range
    mask = (df["event_timestamp"] >= start) & (df["event_timestamp"] <= end)

    if device_id != "Todos":
        mask &= (df["device_id"] == device_id)

    if source != "Todos":
        mask &= (df["source"] == source)

    if presence_only:
        mask &= (df["presence"] == 1)

    if valid_only and "is_valid" in df.columns:
        mask &= (df["is_valid"] == 1)

    return df.loc[mask].copy()


# ============================================================
# UI
# ============================================================

def main() -> None:
    st.set_page_config(page_title="Totem Inclusivo Flexmedia — Sprint 3", layout="wide")

    st.title("📊 Totem Inteligente Inclusivo — Dashboard (Sprint 3)")
    st.caption(
        "Dados simulados/reais → SQLite → ML (classificação) → Previsões → Visualização/Relatórios. "
        "Este painel comprova a integração ponta a ponta."
    )

    # Carrega dados
    df = load_interactions_df()

    if df.empty:
        st.warning("Ainda não há dados no banco. Rode o simulador para inserir interações.")
        st.code("python -m sensor.simulate_sensor", language="bash")
        return

    # Sidebar filtros
    st.sidebar.header("Filtros")
    min_ts = df["event_timestamp"].min()
    max_ts = df["event_timestamp"].max()

    # Date input com fallback
    start_default = (max_ts - pd.Timedelta(days=1)) if pd.notnull(max_ts) else pd.Timestamp.utcnow()
    end_default = max_ts if pd.notnull(max_ts) else pd.Timestamp.utcnow()

    start_date = st.sidebar.date_input("Data inicial", value=start_default.date())
    end_date = st.sidebar.date_input("Data final", value=end_default.date())

    # Converte para timestamps UTC (intervalo inclusivo)
    start_dt = pd.Timestamp(start_date).tz_localize("UTC")
    end_dt = (pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)).tz_localize("UTC")

    devices = ["Todos"] + sorted([x for x in df["device_id"].dropna().unique().tolist()])
    sources = ["Todos"] + sorted([x for x in df["source"].dropna().unique().tolist()])

    device_sel = st.sidebar.selectbox("Device", devices, index=0)
    source_sel = st.sidebar.selectbox("Source", sources, index=0)
    presence_only = st.sidebar.checkbox("Somente presença=1", value=False)
    valid_only = st.sidebar.checkbox("Somente registros válidos", value=True)

    df_f = apply_filters(
        df,
        date_range=(start_dt, end_dt),
        device_id=device_sel,
        source=source_sel,
        presence_only=presence_only,
        valid_only=valid_only,
    )

    # Tabs
    tab_overview, tab_ml, tab_data = st.tabs(["Visão Geral", "Machine Learning", "Dados"])

    # ============================================================
    # TAB 1 - Overview
    # ============================================================
    with tab_overview:
        st.subheader("KPIs Operacionais")

        total_events = int(len(df_f))
        total_presence = int(df_f["presence"].sum()) if total_events else 0
        pct_presence = (total_presence / total_events * 100.0) if total_events else 0.0
        avg_duration = float(df_f["duration_s"].mean()) if total_events else 0.0
        pct_touch = (df_f["touch"].mean() * 100.0) if total_events else 0.0
        pct_voice = (df_f["voice_detected"].mean() * 100.0) if total_events else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Eventos", f"{total_events}")
        c2.metric("Presença=1", f"{total_presence}", f"{pct_presence:.1f}%")
        c3.metric("Duração média (s)", f"{avg_duration:.1f}")
        c4.metric("% Touch", f"{pct_touch:.1f}%")
        c5.metric("% Voz", f"{pct_voice:.1f}%")

        st.divider()

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Eventos ao longo do tempo")
            # Série temporal: contagem por minuto (mais significativo que plotar 0/1)
            ts = df_f.dropna(subset=["event_timestamp"]).set_index("event_timestamp")
            if ts.empty:
                st.info("Sem timestamps válidos no filtro atual.")
            else:
                per_min = ts["id"].resample("1min").count()
                st.line_chart(per_min)

        with col_b:
            st.subheader("Distribuição de duração (classe)")
            dist = df_f["duration_class"].value_counts()
            st.bar_chart(dist)

        st.divider()

        col_c, col_d = st.columns(2)

        with col_c:
            st.subheader("Ativações por dia (presence=1)")
            by_day = df_f.groupby("date")["presence"].sum()
            st.bar_chart(by_day)

        with col_d:
            st.subheader("Ativações por hora do dia (presence=1)")
            by_hour = df_f.groupby("hour")["presence"].sum()
            st.bar_chart(by_hour)

        st.divider()

        # Qualidade/integridade (bom para “Cognitive CyberSecurity” conceitual)
        st.subheader("Integridade e Qualidade dos Dados")
        invalid = int((df_f["is_valid"] == 0).sum()) if "is_valid" in df_f.columns else 0
        st.write(f"- Registros inválidos no filtro atual: **{invalid}**")
        if invalid > 0:
            st.caption("Amostra de registros inválidos (com notas de validação):")
            st.dataframe(
                df_f[df_f["is_valid"] == 0][["id", "event_timestamp", "device_id", "source", "duration_s", "validation_notes"]].tail(10),
                use_container_width=True,
            )

    # ============================================================
    # TAB 2 - ML
    # ============================================================
    with tab_ml:
        st.subheader("Métricas do Modelo (Artifacts)")

        metrics = _safe_read_json(METRICS_PATH)
        if not metrics:
            st.warning("Não encontrei metrics.json. Rode o treino do modelo primeiro.")
            st.code("python -m ml.train", language="bash")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Baseline Accuracy", f"{metrics.get('baseline_accuracy', 0):.4f}")
            m2.metric("Baseline F1-macro", f"{metrics.get('baseline_f1_macro', 0):.4f}")
            m3.metric("RF Accuracy", f"{metrics.get('rf_accuracy', 0):.4f}")
            m4.metric("RF F1-macro", f"{metrics.get('rf_f1_macro', 0):.4f}")

            st.caption(
                f"Modelo: {metrics.get('model_name')} | Versão: {metrics.get('model_version')} | "
                f"Treinado em: {metrics.get('trained_at')} | Linhas usadas: {metrics.get('rows_used')}"
            )

        st.divider()

        st.subheader("Matriz de Confusão")
        if CM_PATH.exists():
            st.image(str(CM_PATH), use_container_width=True)
        else:
            st.info("confusion_matrix.png não encontrado (opcional).")

        st.divider()

        st.subheader("Previsões gravadas no Banco (JOIN predictions + interactions)")
        model_version = (metrics.get("model_version") if metrics else "rf_v1") or "rf_v1"
        pred_df = load_predictions_join_df(model_version=model_version, limit=2000)

        if pred_df.empty:
            st.warning("Não há previsões no banco para esta versão do modelo. Rode a inferência.")
            st.code("python -m ml.predict", language="bash")
        else:
            # Distribuição por label
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Distribuição de classes previstas**")
                st.bar_chart(pred_df["pred_label"].value_counts())

            with col2:
                st.write("**Probabilidade média por classe (confiança)**")
                proba_mean = pred_df.groupby("pred_label")["pred_proba"].mean().sort_values(ascending=False)
                st.bar_chart(proba_mean)

            st.divider()

            st.write("**Últimas previsões**")
            st.dataframe(
                pred_df[[
                    "predicted_at", "interaction_id", "pred_label", "pred_proba",
                    "duration_s", "presence", "touch", "voice_detected",
                    "device_id", "source", "content_category", "interaction_zone"
                ]].head(50),
                use_container_width=True,
            )

            # Insight simples (explicabilidade leve)
            st.caption(
                "Insight: compare a classe prevista com duration_s e sinais (presence/touch/voice). "
                "Em dados simulados, duration_s tende a dominar a decisão do modelo."
            )

    # ============================================================
    # TAB 3 - Data
    # ============================================================
    with tab_data:
        st.subheader("Dados brutos (interactions) — últimos registros")
        st.dataframe(
            df_f.sort_values("event_timestamp", ascending=False).head(200),
            use_container_width=True,
        )

        st.divider()

        st.subheader("Consultas rápidas (para validação)")
        c1, c2, c3 = st.columns(3)

        with c1:
            st.code("SELECT count(*) FROM interactions;", language="sql")
            st.write(int(len(df)))

        with c2:
            conn = get_conn(DB_PATH)
            try:
                init_db(conn)
                n_pred = conn.execute("SELECT count(*) FROM predictions;").fetchone()[0]
            finally:
                conn.close()
            st.code("SELECT count(*) FROM predictions;", language="sql")
            st.write(int(n_pred))

        with c3:
            conn = get_conn(DB_PATH)
            try:
                init_db(conn)
                n_invalid = conn.execute("SELECT count(*) FROM interactions WHERE is_valid=0;").fetchone()[0]
            finally:
                conn.close()
            st.code("SELECT count(*) FROM interactions WHERE is_valid=0;", language="sql")
            st.write(int(n_invalid))


if __name__ == "__main__":
    main()

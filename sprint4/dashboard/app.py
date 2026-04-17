"""
dashboard/app.py — Dashboard Sprint 4 (Totem Inteligente Inclusivo)
5 abas: Visão Geral | Machine Learning | Chatbot | Visão Computacional | Voz
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

# Adiciona sprint4/ ao path
DASH_DIR = Path(__file__).resolve().parent
SPRINT4_DIR = DASH_DIR.parent
sys.path.insert(0, str(SPRINT4_DIR))

from database.db import get_conn, init_db

DB_PATH = SPRINT4_DIR / "database" / "totem.db"
ARTIFACTS_DIR = SPRINT4_DIR / "ml" / "artifacts"
METRICS_PATH = ARTIFACTS_DIR / "metrics.json"
CM_PATH = ARTIFACTS_DIR / "confusion_matrix.png"


# ============================================================
# Helpers
# ============================================================

def _safe_json(path: Path) -> Optional[Dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


@st.cache_data(ttl=10, show_spinner=False)
def load_interactions() -> pd.DataFrame:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        df = pd.read_sql_query(
            "SELECT * FROM interactions ORDER BY event_timestamp ASC", conn
        )
    finally:
        conn.close()
    if df.empty:
        return df
    df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce", utc=True)
    df["date"] = df["event_timestamp"].dt.date
    df["hour"] = df["event_timestamp"].dt.hour

    def dur_class(d):
        try:
            d = int(d)
        except Exception:
            d = 0
        if d <= 5:
            return "quick"
        if d <= 20:
            return "normal"
        return "engaged"

    df["duration_class"] = df["duration_s"].apply(dur_class)
    return df


@st.cache_data(ttl=10, show_spinner=False)
def load_predictions(model_version: str = "rf_v2") -> pd.DataFrame:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        df = pd.read_sql_query(
            """
            SELECT p.*, i.duration_s, i.presence, i.touch, i.voice_detected,
                   i.content_category, i.interaction_zone, i.device_id AS idevice
            FROM predictions p
            JOIN interactions i ON i.id = p.interaction_id
            WHERE p.model_version = ?
            ORDER BY p.predicted_at DESC LIMIT 3000
            """,
            conn,
            params=(model_version,),
        )
    finally:
        conn.close()
    if not df.empty:
        df["predicted_at"] = pd.to_datetime(df["predicted_at"], errors="coerce", utc=True)
    return df


@st.cache_data(ttl=10, show_spinner=False)
def load_chat_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        sessions = pd.read_sql_query(
            "SELECT * FROM chat_sessions ORDER BY started_at DESC", conn
        )
        messages = pd.read_sql_query(
            "SELECT * FROM chat_messages ORDER BY created_at ASC", conn
        )
    finally:
        conn.close()
    if not sessions.empty:
        sessions["started_at"] = pd.to_datetime(sessions["started_at"], errors="coerce", utc=True)
    if not messages.empty:
        messages["created_at"] = pd.to_datetime(messages["created_at"], errors="coerce", utc=True)
        messages["hour"] = messages["created_at"].dt.hour
    return sessions, messages


@st.cache_data(ttl=10, show_spinner=False)
def load_vision_data() -> pd.DataFrame:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        df = pd.read_sql_query(
            "SELECT * FROM vision_events ORDER BY detected_at DESC LIMIT 2000", conn
        )
    finally:
        conn.close()
    if not df.empty:
        df["detected_at"] = pd.to_datetime(df["detected_at"], errors="coerce", utc=True)
        df["hour"] = df["detected_at"].dt.hour
    return df


@st.cache_data(ttl=10, show_spinner=False)
def load_voice_data() -> pd.DataFrame:
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        df = pd.read_sql_query(
            "SELECT * FROM voice_events ORDER BY recorded_at DESC LIMIT 1000", conn
        )
    finally:
        conn.close()
    if not df.empty:
        df["recorded_at"] = pd.to_datetime(df["recorded_at"], errors="coerce", utc=True)
    return df


# ============================================================
# App principal
# ============================================================

def main() -> None:
    st.set_page_config(
        page_title="Tótem Inclusivo — Sprint 4",
        layout="wide",
        page_icon="🏛️",
    )

    # Header
    st.title("🏛️ Tótem Inteligente Inclusivo — Sprint 4")
    st.caption(
        "Pipeline completo: Sensor → SQLite → ML → Visão Computacional → Voz → Chatbot | 100% local"
    )

    # Aviso de dados
    conn = get_conn(DB_PATH)
    try:
        init_db(conn)
        n_total = conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0]
    finally:
        conn.close()

    if n_total == 0:
        st.warning("⚠️ Banco vazio. Execute o pipeline primeiro:")
        st.code("cd sprint4 && python main.py all", language="bash")
        return

    # Tabs
    tab_overview, tab_ml, tab_chat, tab_vision, tab_voice = st.tabs([
        "📊 Visão Geral",
        "🤖 Machine Learning",
        "💬 Chatbot",
        "👁️ Visão Computacional",
        "🎙️ Reconhecimento de Voz",
    ])

    # ==============================================================
    # TAB 1 — VISÃO GERAL
    # ==============================================================
    with tab_overview:
        df = load_interactions()

        if df.empty:
            st.warning("Sem dados de interação.")
        else:
            st.subheader("📈 KPIs Operacionais")
            total = len(df)
            valid = int(df["is_valid"].sum()) if "is_valid" in df.columns else total
            presence = int(df["presence"].sum())
            avg_dur = float(df["duration_s"].mean())
            pct_touch = float(df["touch"].mean() * 100)
            pct_voice = float(df["voice_detected"].mean() * 100)

            c1, c2, c3, c4, c5, c6 = st.columns(6)
            c1.metric("Total Eventos", f"{total:,}")
            c2.metric("Válidos", f"{valid:,}")
            c3.metric("Com Presença", f"{presence:,}", f"{presence/total*100:.1f}%")
            c4.metric("Duração Média", f"{avg_dur:.1f}s")
            c5.metric("% Touch", f"{pct_touch:.1f}%")
            c6.metric("% Voz", f"{pct_voice:.1f}%")

            st.divider()

            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("Eventos por hora do dia")
                by_hour = df.groupby("hour")["id"].count()
                st.bar_chart(by_hour, color="#4F8EF7")

            with col_b:
                st.subheader("Distribuição de engajamento")
                dist = df["duration_class"].value_counts()
                st.bar_chart(dist, color="#F7844F")

            st.divider()

            col_c, col_d = st.columns(2)
            with col_c:
                st.subheader("Ativações por dia")
                by_day = df.groupby("date")["presence"].sum()
                st.bar_chart(by_day, color="#4FF7A0")

            with col_d:
                st.subheader("Categorias de conteúdo acessadas")
                if "content_category" in df.columns:
                    cat_dist = df["content_category"].value_counts().head(8)
                    st.bar_chart(cat_dist, color="#C84FF7")

            st.divider()

            st.subheader("Modos de Acessibilidade utilizados")
            if "accessibility_mode" in df.columns:
                acc = df["accessibility_mode"].dropna().value_counts()
                if acc.empty:
                    st.info("Nenhum modo de acessibilidade registrado.")
                else:
                    st.bar_chart(acc, color="#F7C84F")

    # ==============================================================
    # TAB 2 — MACHINE LEARNING
    # ==============================================================
    with tab_ml:
        st.subheader("🤖 Modelo de Classificação de Engajamento")

        metrics = _safe_json(METRICS_PATH)

        if not metrics:
            st.warning("metrics.json não encontrado. Execute: `python main.py train`")
        else:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Baseline Accuracy", f"{metrics.get('baseline_accuracy', 0):.4f}")
            m2.metric("Baseline F1-macro", f"{metrics.get('baseline_f1_macro', 0):.4f}")
            m3.metric("RF Accuracy (FULL)", f"{metrics.get('rf_full_accuracy', 0):.4f}")
            m4.metric("RF F1-macro (FULL)", f"{metrics.get('rf_full_f1_macro', 0):.4f}")

            st.caption(
                f"**Modelo:** {metrics.get('model_name')} | "
                f"**Versão:** {metrics.get('model_version')} | "
                f"**Treinado em:** {metrics.get('trained_at')} | "
                f"**Linhas:** {metrics.get('rows_used')}"
            )

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Sanity Check (sem duration_s)")
                st.metric("RF Accuracy (NO duration)", f"{metrics.get('rf_no_duration_accuracy', 0):.4f}")
                st.metric("RF F1-macro (NO duration)", f"{metrics.get('rf_no_duration_f1_macro', 0):.4f}")
                st.caption(
                    "Este modelo verifica robustez: se a acurácia cai muito sem duration_s, "
                    "o modelo estava sobre-dependendo dessa feature."
                )

            with col2:
                st.subheader("Matriz de Confusão")
                if CM_PATH.exists():
                    st.image(str(CM_PATH), use_container_width=True)
                else:
                    st.info("confusion_matrix.png não encontrado.")

        st.divider()

        model_version = metrics.get("model_version", "rf_v2") if metrics else "rf_v2"
        pred_df = load_predictions(model_version=model_version)

        if pred_df.empty:
            st.warning("Sem previsões no banco. Execute: `python main.py predict`")
        else:
            st.subheader("Previsões gravadas no banco")

            col_p1, col_p2 = st.columns(2)
            with col_p1:
                st.write("**Distribuição de classes previstas**")
                st.bar_chart(pred_df["pred_label"].value_counts(), color="#4F8EF7")

            with col_p2:
                st.write("**Confiança média por classe**")
                proba = pred_df.groupby("pred_label")["pred_proba"].mean().sort_values(ascending=False)
                st.bar_chart(proba, color="#F7844F")

            st.divider()
            st.write("**Últimas 30 previsões**")
            cols_show = ["predicted_at", "pred_label", "pred_proba", "duration_s", "presence", "touch", "voice_detected"]
            st.dataframe(pred_df[cols_show].head(30), use_container_width=True)

    # ==============================================================
    # TAB 3 — CHATBOT
    # ==============================================================
    with tab_chat:
        st.subheader("💬 Chatbot Interativo — Tótem Cultural")

        # Widget de chat interativo
        st.markdown("### Converse com o Tótem agora")
        st.caption("Assistente virtual 100% local — reconhecimento de intenções por NLP")

        # Inicializa estado da sessão Streamlit
        if "chat_session_id" not in st.session_state:
            from chatbot.engine import create_session
            st.session_state.chat_session_id = create_session(device_id="dashboard")
            st.session_state.chat_history = []

        # Exibe histórico de mensagens
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant" and "intent" in msg:
                    st.caption(f"intent: {msg['intent']} | confiança: {msg.get('confidence', 0):.0%}")

        # Input do usuário
        user_input = st.chat_input("Digite sua mensagem ou pergunta sobre o espaço cultural...")

        if user_input:
            from chatbot.engine import chat as chatbot_chat

            # Adiciona mensagem do usuário
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            # Processa resposta
            with st.spinner("Processando..."):
                response = chatbot_chat(
                    user_message=user_input,
                    session_id=st.session_state.chat_session_id,
                    input_mode="text",
                )

            # Exibe resposta
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": response.bot_response,
                "intent": response.intent,
                "confidence": response.confidence,
            })
            with st.chat_message("assistant"):
                st.write(response.bot_response)
                st.caption(f"intent: {response.intent} | confiança: {response.confidence:.0%}")

            st.rerun()

        # Botões de atalho
        st.divider()
        st.markdown("**Perguntas rápidas:**")
        quick_questions = [
            "Quais exposições têm hoje?",
            "Qual o horário de funcionamento?",
            "Tem acessibilidade para cadeirante?",
            "Onde fica o banheiro?",
            "Qual a senha do Wi-Fi?",
            "A entrada é gratuita?",
        ]
        cols = st.columns(3)
        for i, q in enumerate(quick_questions):
            if cols[i % 3].button(q, key=f"quick_{i}"):
                from chatbot.engine import chat as chatbot_chat
                st.session_state.chat_history.append({"role": "user", "content": q})
                response = chatbot_chat(
                    user_message=q,
                    session_id=st.session_state.chat_session_id,
                    input_mode="touch",
                )
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response.bot_response,
                    "intent": response.intent,
                    "confidence": response.confidence,
                })
                st.rerun()

        if st.button("🔄 Nova sessão"):
            from chatbot.engine import create_session, end_session
            end_session(st.session_state.chat_session_id)
            st.session_state.chat_session_id = create_session(device_id="dashboard")
            st.session_state.chat_history = []
            st.rerun()

        st.divider()

        # Analytics do chatbot
        st.subheader("📊 Analytics do Chatbot")
        sessions_df, messages_df = load_chat_data()

        if sessions_df.empty:
            st.info("Sem dados de chat ainda. Use o chat acima ou execute: `python main.py simulate-chat`")
        else:
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Sessões totais", len(sessions_df))
            k2.metric("Mensagens totais", len(messages_df))
            k3.metric(
                "Média msgs/sessão",
                f"{sessions_df['total_messages'].mean():.1f}" if not sessions_df.empty else "0",
            )
            user_msgs = messages_df[messages_df["role"] == "user"]
            k4.metric("Mensagens de usuário", len(user_msgs))

            st.divider()

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.write("**Intenções mais frequentes**")
                if not user_msgs.empty and "intent" in user_msgs.columns:
                    intent_dist = user_msgs["intent"].value_counts().head(10)
                    st.bar_chart(intent_dist, color="#4FF7A0")

            with col_c2:
                st.write("**Modos de entrada**")
                if not messages_df.empty and "input_mode" in messages_df.columns:
                    mode_dist = messages_df[messages_df["role"] == "user"]["input_mode"].value_counts()
                    st.bar_chart(mode_dist, color="#C84FF7")

            st.write("**Distribuição de confiança do NLP**")
            if not user_msgs.empty and "confidence" in user_msgs.columns:
                conf_data = user_msgs["confidence"].dropna()
                if not conf_data.empty:
                    st.bar_chart(conf_data.value_counts(bins=10).sort_index(), color="#F7C84F")

    # ==============================================================
    # TAB 4 — VISÃO COMPUTACIONAL
    # ==============================================================
    with tab_vision:
        st.subheader("👁️ Visão Computacional — Detecção de Presença")

        vision_df = load_vision_data()

        if vision_df.empty:
            st.info("Sem dados de visão. Execute: `python main.py vision-bulk`")
        else:
            total_frames = len(vision_df)
            with_person = int(vision_df["person_detected"].sum())
            avg_attention = float(vision_df[vision_df["person_detected"] == 1]["attention_score"].mean() or 0)
            avg_count = float(vision_df[vision_df["person_detected"] == 1]["person_count"].mean() or 0)

            v1, v2, v3, v4 = st.columns(4)
            v1.metric("Frames analisados", f"{total_frames:,}")
            v2.metric("Com pessoa detectada", f"{with_person:,}", f"{with_person/total_frames*100:.1f}%")
            v3.metric("Atenção média", f"{avg_attention:.2f}")
            v4.metric("Média pessoas/frame", f"{avg_count:.1f}")

            st.divider()

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                st.write("**Distribuição por faixa etária detectada**")
                age_dist = vision_df["age_group"].dropna().value_counts()
                st.bar_chart(age_dist, color="#4F8EF7")

            with col_v2:
                st.write("**Distribuição por emoção detectada**")
                emo_dist = vision_df["emotion"].dropna().value_counts()
                st.bar_chart(emo_dist, color="#F7844F")

            st.divider()

            col_v3, col_v4 = st.columns(2)
            with col_v3:
                st.write("**Zonas de interação mais acessadas**")
                zone_dist = vision_df["zone"].dropna().value_counts()
                st.bar_chart(zone_dist, color="#4FF7A0")

            with col_v4:
                st.write("**Detecção por hora do dia**")
                hour_presence = vision_df[vision_df["person_detected"] == 1].groupby("hour")["id"].count()
                st.bar_chart(hour_presence, color="#C84FF7")

            st.divider()

            # Demo de detecção ao vivo
            st.subheader("🎥 Simulação de Detecção em Tempo Real")
            col_demo1, col_demo2 = st.columns([1, 2])

            with col_demo1:
                if st.button("🔍 Capturar frame agora", type="primary"):
                    from vision.detector import detect
                    with st.spinner("Analisando frame..."):
                        result = detect(use_camera=False, save=True)

                    if result.person_detected:
                        st.success(f"✅ Pessoa detectada!")
                        st.metric("Faixa etária", result.age_group or "-")
                        st.metric("Emoção", result.emotion or "-")
                        st.metric("Atenção", f"{result.attention_score:.0%}")
                        st.metric("Zona", result.zone or "-")
                    else:
                        st.info("👤 Nenhuma pessoa detectada neste frame.")

                    st.caption(f"Confiança: {result.confidence:.0%} | Fonte: {result.source}")

            with col_demo2:
                st.write("**Últimos 10 frames detectados**")
                recent = vision_df[vision_df["person_detected"] == 1].head(10)
                if not recent.empty:
                    show_cols = ["detected_at", "age_group", "emotion", "attention_score", "zone", "confidence"]
                    st.dataframe(recent[show_cols], use_container_width=True)

    # ==============================================================
    # TAB 5 — VOZ
    # ==============================================================
    with tab_voice:
        st.subheader("🎙️ Reconhecimento de Voz — Comandos por Fala")

        voice_df = load_voice_data()

        if voice_df.empty:
            st.info("Sem dados de voz. Execute: `python main.py voice-bulk`")
        else:
            total_v = len(voice_df)
            processed_v = int(voice_df["processed"].sum())
            avg_conf_v = float(voice_df[voice_df["processed"] == 1]["confidence"].mean() or 0)
            avg_dur_v = float(voice_df[voice_df["processed"] == 1]["duration_ms"].mean() or 0)

            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Eventos de voz", f"{total_v:,}")
            r2.metric("Transcrições OK", f"{processed_v:,}", f"{processed_v/total_v*100:.1f}%")
            r3.metric("Confiança média", f"{avg_conf_v:.0%}")
            r4.metric("Duração média", f"{avg_dur_v:.0f}ms")

            st.divider()

            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.write("**Distribuição por idioma**")
                lang_dist = voice_df["language"].value_counts()
                st.bar_chart(lang_dist, color="#4F8EF7")

            with col_r2:
                st.write("**Distribuição por fonte**")
                src_dist = voice_df["source"].value_counts()
                st.bar_chart(src_dist, color="#F7844F")

            st.divider()

            # Demo de reconhecimento
            st.subheader("🎤 Simulação de Reconhecimento de Voz")
            col_r3, col_r4 = st.columns([1, 2])

            with col_r3:
                if st.button("🎤 Simular entrada de voz", type="primary"):
                    from voice.recognizer import recognize
                    from chatbot.engine import chat as chatbot_chat

                    with st.spinner("Reconhecendo fala..."):
                        vresult = recognize(use_microphone=False, save=True)

                    if vresult.success:
                        st.success(f"✅ Transcrição: *\"{vresult.transcript}\"*")
                        st.metric("Confiança", f"{vresult.confidence:.0%}")
                        st.metric("Duração", f"{vresult.duration_ms}ms")

                        # Processa a transcrição no chatbot
                        if "chat_session_id" in st.session_state:
                            chat_resp = chatbot_chat(
                                user_message=vresult.transcript,
                                session_id=st.session_state.chat_session_id,
                                input_mode="voice",
                            )
                            st.divider()
                            st.write("**Resposta do chatbot:**")
                            st.info(chat_resp.bot_response)
                            st.caption(f"intent: {chat_resp.intent}")
                    else:
                        st.warning(f"Não foi possível transcrever: {vresult.error}")

            with col_r4:
                st.write("**Últimas 10 transcrições**")
                recent_v = voice_df[voice_df["processed"] == 1].head(10)
                if not recent_v.empty:
                    show_v = ["recorded_at", "transcript", "confidence", "duration_ms", "language", "source"]
                    st.dataframe(recent_v[show_v], use_container_width=True)


if __name__ == "__main__":
    main()

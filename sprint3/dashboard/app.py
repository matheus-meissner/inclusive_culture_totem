import sqlite3
import pandas as pd
import streamlit as st
from datetime import datetime

DB_PATH = "../database/totem.db"


@st.cache_data(ttl=5)
def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM interactions", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    df["houve_interacao"] = df["presence"].apply(lambda x: "sim" if x == 1 else "nao")

    def classificar_interacao(dur):
        if dur == 0:
            return "sem_interacao"
        elif dur < 5:
            return "rapida"
        elif dur <= 12:
            return "media"
        else:
            return "longa"

    df["tipo_interacao"] = df["duration"].apply(classificar_interacao)
    df["data"] = df["timestamp"].dt.date
    df["hora"] = df["timestamp"].dt.hour

    return df


def main():
    st.set_page_config(
        page_title="Dashboard – Totem Inclusivo Flexmedia",
        layout="wide",
    )

    st.title("📊 Dashboard – Totem Inteligente Inclusivo")
    st.caption("Monitoramento de uso e interações do totem (dados simulados).")

    df = carregar_dados()

    if df.empty:
        st.warning("Ainda não há dados no banco. Rode o simulador de sensores primeiro.")
        st.code("cd sprint2/sensor_simulation\npython simulate_sensor.py")
        return

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    total_registros = len(df)
    total_ativacoes = int(df["presence"].sum())
    media_duracao = df["duration"].mean()
    interacoes_unicas = df[df["duration"] > 0].shape[0]

    col1.metric("Registros totais", total_registros)
    col2.metric("Ativações (presence = 1)", total_ativacoes)
    col3.metric("Duração média (s)", f"{media_duracao:.1f}")
    col4.metric("Interações com permanência", interacoes_unicas)

    st.divider()

    # Gráficos principais
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Ativações ao longo do tempo")
        df_plot = df.set_index("timestamp")
        st.line_chart(df_plot["presence"])

    with col_b:
        st.subheader("Distribuição dos tipos de interação")
        tipos = df["tipo_interacao"].value_counts()
        st.bar_chart(tipos)

    st.divider()

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Ativações por dia")
        ativ_por_dia = df.groupby("data")["presence"].sum()
        st.bar_chart(ativ_por_dia)

    with col_d:
        st.subheader("Ativações por hora do dia")
        ativ_por_hora = df.groupby("hora")["presence"].sum()
        st.bar_chart(ativ_por_hora)

    st.divider()

    st.subheader("Tabela de dados bruta")
    st.dataframe(df.tail(50), use_container_width=True)


if __name__ == "__main__":
    main()

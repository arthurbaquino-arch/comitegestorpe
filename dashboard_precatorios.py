import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Dashboard de Precatórios - EC 136/2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregar os dados CSV
df = pd.read_csv("Painel-Entes.csv", delimiter=";")

df["ENTE"] = df["ENTE"].astype(str)
df["STATUS"] = df["STATUS"].astype(str)

st.sidebar.header("Filtros de Visualização")
entes_lista = df["ENTE"].unique().tolist()
status_lista = df["STATUS"].unique().tolist()

selected_entes = st.sidebar.multiselect(
    "Selecione o(s) Ente(s) Devedor(es):", 
    options=entes_lista, default=entes_lista
)

selected_status = st.sidebar.selectbox(
    "Selecione o Status:", 
    options=["Todos"] + status_lista
)

filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
filtro_entes = df["ENTE"].isin(selected_entes)
df_filtrado = df[filtro_status & filtro_entes]

st.title("Dashboard de Precatórios - Organização por Ente Devedor")

st.subheader("Entes Devedores Filtrados")
st.dataframe(df_filtrado[
    ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6"]
].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False))

st.subheader("Distribuição do Endividamento Total")
fig = px.bar(
    df_filtrado,
    x="ENTE",
    y="ENDIVIDAMENTO TOTAL",
    color="STATUS",
    labels={"ENTE": "Ente Devedor", "ENDIVIDAMENTO TOTAL": "Endividamento Total"},
    height=400,
    title="Dívida Total por Ente Devedor"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Aportes por Tribunal")
fig_aportes = px.bar(
    df_filtrado,
    x="ENTE",
    y=["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"],
    labels={"value": "Valores de Aportes", "ENTE": "Ente Devedor", "variable": "Tribunal"},
    height=400,
    title="Aportes Realizados por Tribunal"
)
st.plotly_chart(fig_aportes, use_container_width=True)

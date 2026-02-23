import streamlit as st
import pandas as pd
import numpy as np
from typing import Union
import os
import unicodedata

# ----------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ----------------------------------------------------
st.set_page_config(
    page_title="💰 Situação dos Entes Devedores",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 2. MAPEAMENTO DE COLUNAS (CONFORME SUA PLANILHA)
# ----------------------------------------------------
# Nomes exatos para os cálculos (o strip() no código tratará espaços extras)
COL_TOTAL_APORTAR = "TOTAL A SER APORTADO"
COL_VALOR_APORTADO = "VALOR APORTADO"
COL_SALDO_REMANESCENTE = "SALDO REMANESCENTE A APORTAR"

# Colunas específicas solicitadas para a aba de RATEIO
COLS_RATEIO_PCT = ["TJPE (%)", "TRF5 (%)", "TRT6 (%)"]
COLS_RATEIO_RS = ["TJPE (R$)", "TRF5 (R$)", "TRT6 (R$)"]

# Colunas para os KPIs de Tribunal
COL_KPI_TJPE = "TJPE"
COL_KPI_TRF5 = "TRF5"
COL_KPI_TRT6 = "TRT6"

# ----------------------------------------------------
# 3. FUNÇÕES DE SUPORTE (TRATAMENTO DE DADOS)
# ----------------------------------------------------
def sort_key_without_accents(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()

def converter_e_formatar(valor, formato):
    """Trata a conversão de valores e evita o sinal de % duplicado."""
    if pd.isna(valor) or valor is None or valor == "": return "-"
    
    num_valor = None
    if isinstance(valor, (float, int, np.number)):
        num_valor = float(valor)
    else:
        # Limpa string de resíduos comuns
        s = str(valor).replace('R$', '').replace('%', '').replace('(', '').replace(')', '').strip()
        try:
            # Converte padrão BR (1.234,56) para float
            num_valor = float(s.replace('.', '').replace(',', '.'))
        except: return "-"

    if formato == 'moeda':
        return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    
    elif formato == 'percentual':
        # Se a planilha trouxer 0.66 para 66%, multiplicamos por 100. 
        # Se já trouxer 66.0, apenas formatamos.
        if abs(num_valor) <= 1.0 and num_valor != 0:
            num_valor = num_valor * 100
        return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    
    return str(num_valor)

# ----------------------------------------------------
# 4. CARREGAMENTO E LIMPEZA
# ----------------------------------------------------
@st.cache_data
def load_data(file_path):
    encodings = ['utf-8', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, sep=";", encoding=enc)
            # Limpa espaços invisíveis nos nomes das colunas
            df.columns = [c.strip() for c in df.columns]
            return df
        except: continue
    return None

# ----------------------------------------------------
# 5. EXECUÇÃO DO LAYOUT
# ----------------------------------------------------
# Títulos com a cor Azul Marinho original
st.markdown("<h1 style='color: #000080;'>Comitê Gestor de Precatórios - PE</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #000080; margin-top: -15px;'>TJPE - TRF5 - TRT6</h3>", unsafe_allow_html=True)
st.markdown("<h2>💰 Painel de Rateio - 2025</h2>", unsafe_allow_html=True)
st.markdown("---")

if not os.path.exists("Painel Entes.csv"):
    st.error("Arquivo 'Painel Entes.csv' não encontrado.")
else:
    df_raw = load_data("Painel Entes.csv")
    
    # Limpeza básica (mantendo a última linha)
    df = df_raw.dropna(subset=['ENTE']).copy()
    df = df[df["ENTE"].astype(str).str.lower() != 'nan']

    # Criar DF numérico para cálculos de soma (KPIs)
    df_calc = df.copy()
    for col in df_calc.columns:
        if col != 'ENTE' and col != 'STATUS':
            s = df_calc[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
            s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_calc[col] = pd.to_numeric(s, errors='coerce')

    # --- FILTROS ---
    st.header("⚙️ Filtros Analíticos")
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        ente_sel = st.selectbox("👤 Ente Devedor:", ["Todos"] + sorted(df["ENTE"].unique(), key=sort_key_without_accents))
    with c_f2:
        status_sel = st.selectbox("🚦 Status da Dívida:", ["Todos"] + sorted(df["STATUS"].astype(str).unique()))

    # Aplicação dos filtros
    mask = (df["ENTE"].notnull())
    if ente_sel != "Todos": mask &= (df["ENTE"] == ente_sel)
    if status_sel != "Todos": mask &= (df["STATUS"] == status_sel)

    df_final = df_calc[mask]
    df_final_str = df[mask]

    if df_final.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        # --- BLOCO DE KPIs PRINCIPAIS ---
        st.header("📈 Dados Consolidados: Geral")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total a Ser Aportado", converter_e_formatar(df_final[COL_TOTAL_APORTAR].sum(), 'moeda'))
        k2.metric("Valor Aportado", converter_e_formatar(df_final[COL_VALOR_APORTADO].sum(), 'moeda'))
        k3.metric("Saldo Remanescente", converter_e_formatar(df_final[COL_SALDO_REMANESCENTE].sum(), 'moeda'))
        k4.metric("Status", df_final_str["STATUS"].iloc[0] if ente_sel != "Todos" else "Múltiplos")

        st.markdown("---")

        # --- BLOCO DE KPIs POR TRIBUNAL ---
        st.header("➡️ Total a ser aportado por Tribunal")
        t1, t2, t3 = st.columns(3)
        t1.metric("TJPE (R$)", converter_e_formatar(df_final[COL_KPI_TJPE].sum(), 'moeda'))
        t2.metric("TRF5 (R$)", converter_e_formatar(df_final[COL_KPI_TRF5].sum(), 'moeda'))
        t3.metric("TRT6 (R$)", converter_e_formatar(df_final[COL_KPI_TRT6].sum(), 'moeda'))
        
        st.caption("*Valores baseados no rateio proporcional à dívida de cada tribunal.")
        st.markdown("---")

        # --- ABAS DETALHADAS ---
        st.header("🔎 Detalhamento dos Índices")
        tab_rcl, tab_rateio, tab_divida = st.tabs(["📊 RCL e Aporte", "⚖️ Aba de Rateio", "💰 Dívida Total"])

        with tab_rcl:
            # Tabela de RCL e Percentuais Aplicados
            cols_show = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", COL_TOTAL_APORTAR]
            df_tab1 = df_final[cols_show].copy()
            df_tab1["RCL 2024"] = df_tab1["RCL 2024"].apply(lambda x: converter_e_formatar(x, 'moeda'))
            df_tab1["DÍVIDA EM MORA / RCL"] = df_tab1["DÍVIDA EM MORA / RCL"].apply(lambda x: converter_e_formatar(x, 'percentual'))
            df_tab1["% APLICADO"] = df_tab1["% APLICADO"].apply(lambda x: converter_e_formatar(x, 'percentual'))
            df_tab1[COL_TOTAL_APORTAR] = df_tab1[COL_TOTAL_APORTAR].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_tab1, use_container_width=True, hide_index=True)

        with tab_rateio:
            # Tabela de Rateio corrigida (Percentual vs Real)
            tipo_view = st.radio("Mostrar rateio por:", ["Porcentual (%)", "Valor (R$)"], horizontal=True)
            if tipo_view == "Porcentual (%)":
                df_tab2 = df_final[["ENTE"] + COLS_RATEIO_PCT].copy()
                for c in COLS_RATEIO_PCT:
                    df_tab2[c] = df_tab2[c].apply(lambda x: converter_e_formatar(x, 'percentual'))
            else:
                df_tab2 = df_final[["ENTE"] + COLS_RATEIO_RS].copy()
                for c in COLS_RATEIO_RS:
                    df_tab2[c] = df_tab2[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_tab2, use_container_width=True, hide_index=True)

        with tab_divida:
            # Composição da dívida por tribunal
            cols_div = ["ENTE", "ENDIVIDAMENTO TOTAL - [TJPE]", "ENDIVIDAMENTO TOTAL - [TRF5]", "ENDIVIDAMENTO TOTAL - [TRT6]", "ENDIVIDAMENTO TOTAL"]
            df_tab3 = df_final[cols_div].copy()
            for c in cols_div[1:]:
                df_tab3[c] = df_tab3[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_tab3, use_container_width=True, hide_index=True)

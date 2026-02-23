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
# 2. MAPEAMENTO DE COLUNAS
# ----------------------------------------------------
COL_TOTAL_APORTAR = "TOTAL A SER APORTADO"
COL_VALOR_APORTADO = "VALOR APORTADO"
COL_SALDO_REMANESCENTE = "SALDO REMANESCENTE A APORTAR"
COLS_RATEIO_PCT = ["TJPE (%)", "TRF5 (%)", "TRT6 (%)"]
COLS_RATEIO_RS = ["TJPE (R$)", "TRF5 (R$)", "TRT6 (R$)"]
COL_APORTE_TJPE = "APORTES - [TJPE]"
COL_APORTE_TRF5 = "APORTES - [TRF5]"
COL_APORTE_TRT6 = "APORTES - [TRT6]"

# ----------------------------------------------------
# 3. FUNÇÕES DE SUPORTE
# ----------------------------------------------------
def sort_key_without_accents(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()

def converter_e_formatar(valor, formato):
    if pd.isna(valor) or valor is None or valor == "": return "-"
    
    num_valor = None
    original_era_string_com_percent = False
    
    if isinstance(valor, (float, int, np.number)):
        num_valor = float(valor)
    else:
        s = str(valor).strip()
        if '%' in s: original_era_string_com_percent = True
        s_limpa = s.replace('R$', '').replace('%', '').replace('(', '').replace(')', '').strip()
        try:
            num_valor = float(s_limpa.replace('.', '').replace(',', '.'))
        except: return "-"

    if formato == 'moeda':
        return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    
    elif formato == 'percentual':
        # REGRA: Se o valor veio como decimal (0.026) e NÃO tinha o símbolo % na string original, multiplica por 100.
        # Se ele já era 2.60 ou vinha com %, apenas formata.
        if not original_era_string_com_percent and abs(num_valor) <= 1.0 and num_valor != 0:
            num_valor = num_valor * 100
        return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    
    return str(num_valor)

# ----------------------------------------------------
# 4. PROCESSAMENTO
# ----------------------------------------------------
@st.cache_data
def load_data(file_path):
    encodings = ['utf-8', 'latin1', 'cp1252']
    for enc in encodings:
        try:
            df = pd.read_csv(file_path, sep=";", encoding=enc)
            df.columns = [c.strip() for c in df.columns]
            return df
        except: continue
    return None

# Interface
st.markdown("<h1 style='color: #000080;'>Comitê Gestor de Precatórios - PE</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #000080; margin-top: -15px;'>TJPE - TRF5 - TRT6</h3>", unsafe_allow_html=True)
st.markdown("<h2>💰 Painel de Rateio - 2025</h2>", unsafe_allow_html=True)
st.markdown("---")

if not os.path.exists("Painel Entes.csv"):
    st.error("Arquivo não encontrado.")
else:
    df_raw = load_data("Painel Entes.csv")
    df = df_raw.dropna(subset=['ENTE']).copy()
    df = df[df["ENTE"].astype(str).str.lower() != 'nan']

    # Criar DF numérico para cálculos (Preservando strings originais para checagem de %)
    df_calc = df.copy()
    for col in df_calc.columns:
        if col not in ['ENTE', 'STATUS']:
            s = df_calc[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
            s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_calc[col] = pd.to_numeric(s, errors='coerce')

    # Filtros
    st.header("⚙️ Filtros Analíticos")
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        ente_sel = st.selectbox("👤 Ente Devedor:", ["Todos"] + sorted(df["ENTE"].unique(), key=sort_key_without_accents))
    with c_f2:
        status_sel = st.selectbox("🚦 Status da Dívida:", ["Todos"] + sorted(df["STATUS"].astype(str).unique()))

    mask = (df["ENTE"].notnull())
    if ente_sel != "Todos": mask &= (df["ENTE"] == ente_sel)
    if status_sel != "Todos": mask &= (df["STATUS"] == status_sel)

    df_res_calc = df_calc[mask]
    df_res_str = df[mask]

    if df_res_calc.empty:
        st.warning("Sem dados.")
    else:
        # KPIs
        st.header("📈 Dados Consolidados: Geral")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total a Ser Aportado", converter_e_formatar(df_res_calc[COL_TOTAL_APORTAR].sum(), 'moeda'))
        k2.metric("Valor Aportado", converter_e_formatar(df_res_calc[COL_VALOR_APORTADO].sum(), 'moeda'))
        k3.metric("Saldo Remanescente", converter_e_formatar(df_res_calc[COL_SALDO_REMANESCENTE].sum(), 'moeda'))
        k4.metric("Status", df_res_str["STATUS"].iloc[0] if ente_sel != "Todos" else "Múltiplos")

        st.markdown("---")
        st.header("➡️ Total a ser aportado por Tribunal")
        t1, t2, t3 = st.columns(3)
        t1.metric("TJPE (R$)", converter_e_formatar(df_res_calc["TJPE"].sum(), 'moeda'))
        t2.metric("TRF5 (R$)", converter_e_formatar(df_res_calc["TRF5"].sum(), 'moeda'))
        t3.metric("TRT6 (R$)", converter_e_formatar(df_res_calc["TRT6"].sum(), 'moeda'))
        
        st.markdown("---")

        # ABAS
        st.header("🔎 Detalhamento dos Índices")
        tab1, tab2, tab3, tab4 = st.tabs(["📊 RCL/Aporte", "📈 Aportes", "⚖️ Rateio", "💰 Dívida"])

        with tab1:
            # Usamos o df_res_str para verificar se o valor original tinha '%'
            df_t1 = df_res_str[["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", COL_TOTAL_APORTAR]].copy()
            df_t1["RCL 2024"] = df_t1["RCL 2024"].apply(lambda x: converter_e_formatar(x, 'moeda'))
            df_t1["DÍVIDA EM MORA / RCL"] = df_t1["DÍVIDA EM MORA / RCL"].apply(lambda x: converter_e_formatar(x, 'percentual'))
            df_t1["% APLICADO"] = df_t1["% APLICADO"].apply(lambda x: converter_e_formatar(x, 'percentual'))
            df_t1[COL_TOTAL_APORTAR] = df_t1[COL_TOTAL_APORTAR].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_t1, use_container_width=True, hide_index=True)

        with tab2:
            df_t2 = df_res_str[["ENTE", COL_APORTE_TJPE, COL_APORTE_TRF5, COL_APORTE_TRT6, COL_VALOR_APORTADO]].copy()
            for c in df_t2.columns[1:]:
                df_t2[c] = df_t2[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_t2, use_container_width=True, hide_index=True)

        with tab3:
            tipo = st.radio("Mostrar por:", ["Porcentual (%)", "Valor (R$)"], horizontal=True)
            cols_sel = COLS_RATEIO_PCT if tipo == "Porcentual (%)" else COLS_RATEIO_RS
            df_t3 = df_res_str[["ENTE"] + cols_sel].copy()
            fmt = 'percentual' if tipo == "Porcentual (%)" else 'moeda'
            for c in cols_sel:
                df_t3[c] = df_t3[c].apply(lambda x: converter_e_formatar(x, fmt))
            st.dataframe(df_t3, use_container_width=True, hide_index=True)

        with tab4:
            cols_d = ["ENTE", "ENDIVIDAMENTO TOTAL - [TJPE]", "ENDIVIDAMENTO TOTAL - [TRF5]", "ENDIVIDAMENTO TOTAL - [TRT6]", "ENDIVIDAMENTO TOTAL"]
            df_t4 = df_res_str[cols_d].copy()
            for c in cols_d[1:]:
                df_t4[c] = df_t4[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_t4, use_container_width=True, hide_index=True)

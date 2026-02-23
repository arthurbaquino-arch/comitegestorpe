import streamlit as st
import pandas as pd
import numpy as np
from typing import Union
import os
import unicodedata

# ----------------------------------------------------
# CONFIGURAÇÃO DO ARQUIVO E MAPEAMENTO
# ----------------------------------------------------
FILE_PATH = "Painel Entes.csv"

# Mapeamento exato conforme sua planilha
COLUNA_PARCELA_ANUAL_INTERNO = "TOTAL A SER APORTADO"
COLUNA_APORTES_INTERNO = "VALOR APORTADO"
COLUNA_SALDO_A_PAGAR_INTERNO = "SALDO REMANESCENTE A APORTAR"

# Nomes para a Aba de Rateio (Percentual e Real)
COLS_RATEIO_PCT = ["TJPE (%)", "TRF5 (%)", "TRT6 (%)"]
COLS_RATEIO_RS = ["TJPE (R$)", "TRF5 (R$)", "TRT6 (R$)"]

COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY = "ENDIVIDAMENTO TOTAL EM JAN/2025"
COLUNAS_CRITICAS = ["ENTE", "STATUS", COLUNA_PARCELA_ANUAL_INTERNO, "VALOR APORTADO", "DÍVIDA EM MORA / RCL"]

st.set_page_config(page_title="💰 Situação dos Entes Devedores", layout="wide")

# ----------------------------------------------------
# FUNÇÕES DE APOIO
# ----------------------------------------------------
def sort_key_without_accents(text):
    if not isinstance(text, str): return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()

def read_csv_robustly(file_path):
    encodings = ['utf-8', 'latin1', 'cp1252']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, sep=";", encoding=encoding, header=0, na_values=['#N/D', '#VALOR!', '-', ' -   '])
            # Limpeza rigorosa de espaços nos nomes das colunas (visto que sua planilha tem espaços extras)
            df.columns = [c.strip() for c in df.columns]
            # Correção específica para caracteres especiais mal interpretados
            df.rename(columns=lambda x: x.replace('DÃVIDA', 'DÍVIDA'), inplace=True)
            return df
        except: continue
    raise Exception("Erro ao ler o CSV. Verifique o formato.")

def converter_e_formatar(valor, formato):
    """
    Trata a conversão de valores. 
    Se for percentual e o valor for um decimal pequeno (ex: 0.66), multiplica por 100.
    """
    if pd.isna(valor) or valor is None: return "-"
    
    num_valor = None
    if isinstance(valor, (float, int, np.number)):
        num_valor = float(valor)
    else:
        # Limpa string: remove R$, %, parênteses e espaços
        str_limpa = str(valor).replace('R$', '').replace('%', '').replace('(', '').replace(')', '').strip()
        try:
            # Converte padrão BR (1.000,00) para US (1000.00)
            str_float = str_limpa.replace('.', '').replace(',', '.')
            num_valor = float(str_float)
        except: return "-"

    if formato == 'moeda':
        if abs(num_valor) < 0.01: return "-"
        return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    
    elif formato == 'percentual':
        # REGRA: Se a planilha traz 0.66 para representar 66%, multiplicamos por 100.
        # Se traz 66.0 ou "66%", mantemos o valor.
        if abs(num_valor) <= 1.0 and num_valor != 0:
            num_valor = num_valor * 100
        return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    
    return str(num_valor)

# ----------------------------------------------------
# INTERFACE E PROCESSAMENTO
# ----------------------------------------------------
st.markdown("<h1 style='color: #000080;'>Comitê Gestor de Precatórios - PE</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='color: #000080;'>💰 Painel de Rateio - 2025</h2>", unsafe_allow_html=True)

if not os.path.exists(FILE_PATH):
    st.error("Arquivo não encontrado.")
else:
    df = read_csv_robustly(FILE_PATH)
    
    # Limpeza de dados nulos (removendo "nan" e linhas vazias)
    df = df[df["ENTE"].astype(str).str.lower() != 'nan'].dropna(subset=['ENTE'])
    df["ENTE"] = df["ENTE"].str.strip()

    # Conversão das colunas numéricas para cálculos internos
    df_float = df.copy()
    colunas_para_converter = list(set(COLS_RATEIO_PCT + COLS_RATEIO_RS + [COLUNA_PARCELA_ANUAL_INTERNO, "VALOR APORTADO", "SALDO REMANESCENTE A APORTAR", "RCL 2024"]))
    
    for col in [c for c in colunas_para_converter if c in df_float.columns]:
        s = df_float[col].astype(str).str.replace('R$', '', regex=False).str.replace('%', '', regex=False).str.strip()
        s = s.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        df_float[col] = pd.to_numeric(s, errors='coerce')

    # Filtros
    st.header("⚙️ Filtros")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_ente = st.selectbox("👤 Ente Devedor:", ["Todos"] + sorted(df["ENTE"].unique(), key=sort_key_without_accents))
    with col_f2:
        selected_status = st.selectbox("🚦 Status:", ["Todos"] + sorted(df["STATUS"].astype(str).unique()))

    # Aplicação do Filtro
    mask = (df["ENTE"].notnull())
    if selected_ente != "Todos": mask &= (df["ENTE"] == selected_ente)
    if selected_status != "Todos": mask &= (df["STATUS"] == selected_status)
    
    df_filtrado = df_float[mask]
    df_filtrado_str = df[mask]

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado.")
    else:
        # KPIs Principais
        st.header("📈 Dados Consolidados")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total a Ser Aportado", converter_e_formatar(df_filtrado[COLUNA_PARCELA_ANUAL_INTERNO].sum(), 'moeda'))
        k2.metric("Valor Aportado", converter_e_formatar(df_filtrado["VALOR APORTADO"].sum(), 'moeda'))
        k3.metric("Saldo Remanescente", converter_e_formatar(df_filtrado["SALDO REMANESCENTE A APORTAR"].sum(), 'moeda'))
        k4.metric("Status", df_filtrado_str["STATUS"].iloc[0] if selected_ente != "Todos" else "-")

        # Seção de Rateio por Tribunal (KPIs Rápidos)
        st.header("➡️ Total por Tribunal")
        rt1, rt2, rt3 = st.columns(3)
        rt1.metric("TJPE (R$)", converter_e_formatar(df_filtrado["TJPE"].sum(), 'moeda'))
        rt2.metric("TRF5 (R$)", converter_e_formatar(df_filtrado["TRF5"].sum(), 'moeda'))
        rt3.metric("TRT6 (R$)", converter_e_formatar(df_filtrado["TRT6"].sum(), 'moeda'))

        # Abas de Detalhes
        tab1, tab2, tab3 = st.tabs(["📊 RCL e Aporte", "⚖️ Aba de Rateio", "💰 Composição da Dívida"])

        with tab1:
            cols_t1 = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", COLUNA_PARCELA_ANUAL_INTERNO]
            df_t1 = df_filtrado[cols_t1].copy()
            df_t1["RCL 2024"] = df_t1["RCL 2024"].apply(lambda x: converter_e_formatar(x, 'moeda'))
            df_t1["TOTAL A SER APORTADO"] = df_t1[COLUNA_PARCELA_ANUAL_INTERNO].apply(lambda x: converter_e_formatar(x, 'moeda'))
            df_t1["DÍVIDA EM MORA / RCL"] = df_t1["DÍVIDA EM MORA / RCL"].apply(lambda x: converter_e_formatar(x, 'percentual'))
            df_t1["% APLICADO"] = df_t1["% APLICADO"].apply(lambda x: converter_e_formatar(x, 'percentual'))
            st.dataframe(df_t1[["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", "TOTAL A SER APORTADO"]], use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("Informações de Rateio por Tribunal")
            tipo_rateio = st.radio("Visualizar por:", ["Porcentual (%)", "Valor (R$)"], horizontal=True)
            
            if tipo_rateio == "Porcentual (%)":
                # Usa exatamente as colunas TJPE (%), TRF5 (%), TRT6 (%)
                cols_r = ["ENTE"] + COLS_RATEIO_PCT
                df_r = df_filtrado[cols_r].copy()
                for c in COLS_RATEIO_PCT:
                    df_r[c] = df_r[c].apply(lambda x: converter_e_formatar(x, 'percentual'))
            else:
                # Usa exatamente as colunas TJPE (R$), TRF5 (R$), TRT6 (R$)
                cols_r = ["ENTE"] + COLS_RATEIO_RS
                df_r = df_filtrado[cols_r].copy()
                for c in COLS_RATEIO_RS:
                    df_r[c] = df_r[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
            
            st.dataframe(df_r, use_container_width=True, hide_index=True)

        with tab3:
            # Exibe o endividamento total por tribunal conforme a planilha
            cols_d = ["ENTE", "ENDIVIDAMENTO TOTAL - [TJPE]", "ENDIVIDAMENTO TOTAL - [TRF5]", "ENDIVIDAMENTO TOTAL - [TRT6]", "ENDIVIDAMENTO TOTAL"]
            df_d = df_filtrado[cols_d].copy()
            for c in cols_d[1:]:
                df_d[c] = df_d[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
            st.dataframe(df_d, use_container_width=True, hide_index=True)

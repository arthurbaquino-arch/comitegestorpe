import streamlit as st
import pandas as pd
import numpy as np
from typing import Union
import os
import unicodedata

# ----------------------------------------------------
# CONFIGURAÇÃO DO ARQUIVO FIXO E MAPEAMENTO DE NOMES
# ----------------------------------------------------
FILE_PATH = "Painel Entes.csv"

# Nomes Internos (Baseados nos nomes exatos da planilha mais recente)
COLUNA_PARCELA_ANUAL_INTERNO = "TOTAL A SER APORTADO"
COLUNA_APORTES_INTERNO = "VALOR APORTADO"
COLUNA_SALDO_A_PAGAR_INTERNO = "SALDO REMANESCENTE A APORTAR"

# Nomes de Colunas de Aportes Detalhados por Tribunal
COLUNA_APORTES_TJPE_INTERNO = "APORTES - [TJPE]"
COLUNA_APORTES_TRF5_INTERNO = "APORTES - [TRF5]"
COLUNA_APORTES_TRT6_INTERNO = "APORTES - [TRT6]"

# Nomes de Colunas de Rateio Percentual
COLUNA_PERCENTUAL_TJPE_INTERNO = "TJPE (%)"
COLUNA_PERCENTUAL_TRF5_INTERNO = "TRF5 (%)"
COLUNA_PERCENTUAL_TRT6_INTERNO = "TRT6 (%)"

# COLUNAS SOLICITADAS PARA A NOVA SEÇÃO DE KPI
COLUNA_TJPE_SIMPLES_INTERNO = "TJPE"
COLUNA_TRF5_SIMPLES_INTERNO = "TRF5"
COLUNA_TRT6_SIMPLES_INTERNO = "TRT6"
COLUNA_TJPE_RS_INTERNO = "TJPE (R$)"
COLUNA_TRF5_RS_INTERNO = "TRF5 (R$)"
COLUNA_TRT6_RS_INTERNO = "TRT6 (R$)"


# Nomes de Display (Para manter o visual anterior consistente)
COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY = "ENDIVIDAMENTO TOTAL EM JAN/2025"
COLUNA_PARCELA_ANUAL_DISPLAY = "Total a Ser Aportado (R$)" 
COLUNA_APORTES_DISPLAY = "Valor Aportado (R$)" 
COLUNA_SALDO_A_PAGAR_DISPLAY = "Saldo Remanescente a Aportar (R$)" 


# Colunas críticas esperadas no formato limpo
COLUNAS_CRITICAS = ["ENTE", "STATUS", COLUNA_PARCELA_ANUAL_INTERNO, COLUNA_APORTES_INTERNO, "DÍVIDA EM MORA / RCL"]


# --- Configuração da página ---
st.set_page_config(
    page_title="💰 Situação dos Entes Devedores",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# FUNÇÃO DE ORDENAÇÃO SEM ACENTOS
# ----------------------------------------------------
def sort_key_without_accents(text):
    """Normaliza e converte para minúsculas, removendo acentos para ordenação alfabética correta."""
    if not isinstance(text, str):
        return ""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()

# ----------------------------------------------------
# FUNÇÃO ROBUSTA DE LEITURA
# ----------------------------------------------------
def read_csv_robustly(file_path):
    """Tenta ler o CSV usando múltiplos encodings e limpa cabeçalhos."""
    encodings = ['utf-8', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            # A planilha usa o separador ";"
            df = pd.read_csv(file_path, sep=";", encoding=encoding, header=0, na_values=['#N/D', '#VALOR!', '-', ' -   '])
            
            # Limpeza de cabeçalhos
            col_map = {}
            for col in df.columns:
                stripped_col = col.strip()
                if stripped_col.startswith('\ufeff'):
                    stripped_col = stripped_col.lstrip('\ufeff').strip()
                if stripped_col.startswith('ï»¿'):
                    stripped_col = stripped_col.lstrip('ï»¿').strip()

                if 'DÃVIDA EM MORA / RCL' in stripped_col:
                    stripped_col = 'DÍVIDA EM MORA / RCL'
                
                col_map[col] = stripped_col.strip()
            
            df.rename(columns=col_map, inplace=True)
            return df
            
        except Exception:
            continue
    
    raise Exception("Erro de Codificação na leitura do CSV.")


# ----------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO E CONVERSÃO
# ----------------------------------------------------
def converter_e_formatar(valor: Union[str, float, int, None], formato: str):
    """Formata valor para o padrão monetário/percentual brasileiro."""
    if pd.isna(valor) or valor is None:
        return "-"
    
    num_valor = None
    
    if isinstance(valor, (float, int, np.number)):
        num_valor = float(valor)
    else:
        str_valor = str(valor).strip()
        str_limpa = str_valor.replace('R$', '').replace('(', '').replace(')', '').replace('%', '').strip()

        try:
            str_float = str_limpa.replace('.', 'TEMP').replace(',', '.').replace('TEMP', '')
            num_valor = float(str_float)
        except Exception:
            return "-"
            
    try:
        if formato == 'moeda':
            if abs(num_valor) < 0.01:
                return "-"
            return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        elif formato == 'percentual':
            return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        else:
            return str(num_valor)
    except Exception:
        return "-"


# ----------------------------------------------------
# TÍTULOS E LAYOUT INICIAL
# ----------------------------------------------------
st.markdown("<h1 style='color: #000080;'>Comitê Gestor de Precatórios - PE</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #000080; margin-top: -15px;'>TJPE - TRF5 - TRT6</h3>", unsafe_allow_html=True)
st.markdown("<h2>💰 Painel de Rateio - 2025</h2>", unsafe_allow_html=True)
st.markdown("---")

# ----------------------------------------------------
# Processamento
# ----------------------------------------------------

if not os.path.exists(FILE_PATH):
    st.error(f"❌ Erro: O arquivo '{FILE_PATH}' não foi encontrado.")
else:
    with st.spinner('⏳ Processando dados...'):
        try:
            df = read_csv_robustly(FILE_PATH)
            
            # Verificação de colunas
            if not all(col in df.columns for col in COLUNAS_CRITICAS):
                 st.error(f"❌ Colunas críticas ausentes.")
                 st.stop()
            
            # --- REMOVIDA A EXCLUSÃO DA ÚLTIMA LINHA PARA CONTEMPLAR TODOS OS MUNICÍPIOS ---

            # --- LIMPEZA DE LINHAS VAZIAS OU "NAN" ---
            df["ENTE"] = df["ENTE"].astype(str).str.strip()
            df = df[df["ENTE"] != '']
            df = df[df["ENTE"].str.lower() != 'nan']
            df.dropna(subset=['ENTE'], inplace=True) 
            
            # Renomeação de colunas de exibição
            rename_map = {
                "ENDIVIDAMENTO TOTAL": COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY,
                "ENDIVIDAMENTO TOTAL - [TJPE]": "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]",
                "ENDIVIDAMENTO TOTAL - [TRF5]": "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]",
                "ENDIVIDAMENTO TOTAL - [TRT6]": "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]",
            }
            df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
            
            # Conversão Numérica
            df_float = df.copy()
            colunas_num = [
                COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY, COLUNA_PARCELA_ANUAL_INTERNO, COLUNA_APORTES_INTERNO, "RCL 2024",
                "DÍVIDA EM MORA / RCL", "% APLICADO",
                COLUNA_SALDO_A_PAGAR_INTERNO, COLUNA_PERCENTUAL_TJPE_INTERNO, COLUNA_PERCENTUAL_TRF5_INTERNO, COLUNA_PERCENTUAL_TRT6_INTERNO,
                COLUNA_APORTES_TJPE_INTERNO, COLUNA_APORTES_TRF5_INTERNO, COLUNA_APORTES_TRT6_INTERNO,
                COLUNA_TJPE_RS_INTERNO, COLUNA_TRF5_RS_INTERNO, COLUNA_TRT6_RS_INTERNO,
                COLUNA_TJPE_SIMPLES_INTERNO, COLUNA_TRF5_SIMPLES_INTERNO, COLUNA_TRT6_SIMPLES_INTERNO,
                "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]",
                "ESTOQUE EM MORA - [TJPE]", "ESTOQUE VINCENDOS - [TJPE]",
                "ESTOQUE EM MORA - [TRF5]", "ESTOQUE VINCENDOS - [TRF5]",
                "ESTOQUE EM MORA - [TRT6]", "ESTOQUE VINCENDOS - [TRT6]",
                "ESTOQUE EM MORA", "ESTOQUE VINCENDOS"
            ]
            
            for col in [c for c in colunas_num if c in df_float.columns]:
                 s = df_float[col].astype(str).str.replace('R$', '').replace('(', '').replace(')', '').replace('%', '').str.strip()
                 s = s.str.replace('.', 'TEMP').str.replace(',', '.').str.replace('TEMP', '')
                 df_float[col] = pd.to_numeric(s, errors='coerce')

            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros ---
            st.header("⚙️ Filtros analíticos")
            status_lista = [s for s in df["STATUS"].unique().tolist() if s.lower() != 'nan']
            entes_lista = df["ENTE"].unique().tolist()
            
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                 selected_ente = st.selectbox("👤 Ente Devedor:", options=["Todos"] + sorted(entes_lista, key=sort_key_without_accents))
            with col_f2:
                selected_status = st.selectbox("🚦 Status da Dívida:", options=["Todos"] + sorted(status_lista))
            
            st.markdown("---")

            # Aplicação dos filtros
            f_ente = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            f_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            
            df_calc = df_float[f_status & f_ente]
            df_str = df[f_status & f_ente]
            
            if df_calc.empty:
                st.warning("Nenhum dado encontrado.")
            else:
                df_exibicao = df_calc.sort_values(by=COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY, ascending=False) if COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY in df_calc.columns else df_calc

                # --- KPIs Consolidados ---
                st.header("📈 Dados consolidados: TJPE - TRF5 - TRT6")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric(COLUNA_PARCELA_ANUAL_DISPLAY, converter_e_formatar(df_calc[COLUNA_PARCELA_ANUAL_INTERNO].sum(), 'moeda'))
                with c2: st.metric(COLUNA_APORTES_DISPLAY, converter_e_formatar(df_calc[COLUNA_APORTES_INTERNO].sum(), 'moeda'))
                with c3: st.metric(COLUNA_SALDO_A_PAGAR_DISPLAY, converter_e_formatar(df_calc[COLUNA_SALDO_A_PAGAR_INTERNO].sum(), 'moeda'))
                with c4: st.metric("Status", df_str["STATUS"].iloc[0] if selected_ente != "Todos" else "-")
                
                st.markdown("---")

                # --- KPIs por Tribunal ---
                st.header("➡️ Total a ser aportado para cada tribunal *") 
                ct1, ct2, ct3 = st.columns(3)
                with ct1: st.metric("TJPE (R$)", converter_e_formatar(df_calc[COLUNA_TJPE_SIMPLES_INTERNO].sum(), 'moeda'))
                with ct2: st.metric("TRF5 (R$)", converter_e_formatar(df_calc[COLUNA_TRF5_SIMPLES_INTERNO].sum(), 'moeda'))
                with ct3: st.metric("TRT6 (R$)", converter_e_formatar(df_calc[COLUNA_TRT6_SIMPLES_INTERNO].sum(), 'moeda'))
                
                st.markdown("*_Caso o valor da dívida seja inferior ao percentual aplicado sobre a Receita Corrente Líquida (RCL), o ente poderá regularizar sua situação mediante a quitação integral do débito, atualizado até a data do pagamento._*")
                st.markdown("---")

                # --- Abas Detalhadas ---
                st.header("🔎 Análise detalhada de índices e aportes")
                t1, t2, t3, t4 = st.tabs(["📊 RCL/Aporte", "📈 Aportes", "⚖️ Rateio", "💰 Dívida"])
                
                with t1:
                    cols = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", COLUNA_PARCELA_ANUAL_INTERNO]
                    df_t1 = df_exibicao[[c for c in cols if c in df_exibicao.columns]].copy()
                    df_t1.rename(columns={COLUNA_PARCELA_ANUAL_INTERNO: "TOTAL A SER APORTADO"}, inplace=True)
                    for c in ["RCL 2024", "TOTAL A SER APORTADO"]: df_t1[c] = df_t1[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    for c in ["DÍVIDA EM MORA / RCL", "% APLICADO"]: df_t1[c] = df_t1[c].apply(lambda x: converter_e_formatar(x, 'percentual'))
                    st.dataframe(df_t1, use_container_width=True, hide_index=True)

                with t2:
                    cols_orig = ["ENTE", COLUNA_APORTES_TJPE_INTERNO, COLUNA_APORTES_TRF5_INTERNO, COLUNA_APORTES_TRT6_INTERNO, COLUNA_APORTES_INTERNO]
                    df_t2 = df_exibicao[[c for c in cols_orig if c in df_exibicao.columns]].copy()
                    df_t2.rename(columns={COLUNA_APORTES_TJPE_INTERNO: "APORTES TJPE", COLUNA_APORTES_TRF5_INTERNO: "APORTES TRF5", COLUNA_APORTES_TRT6_INTERNO: "APORTES TRT6", COLUNA_APORTES_INTERNO: "TOTAL APORTADO"}, inplace=True)
                    for c in ["APORTES TJPE", "APORTES TRF5", "APORTES TRT6", "TOTAL APORTADO"]: df_t2[c] = df_t2[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    st.dataframe(df_t2, use_container_width=True, hide_index=True)
                
                with t3:
                    rateio_v = st.radio("Métrica:", ["Porcentual (%)", "Valor (R$)"], key="rv", horizontal=True)
                    if rateio_v == "Porcentual (%)":
                        cols_p = ["ENTE", COLUNA_PERCENTUAL_TJPE_INTERNO, COLUNA_PERCENTUAL_TRF5_INTERNO, COLUNA_PERCENTUAL_TRT6_INTERNO]
                        df_t3 = df_exibicao[[c for c in cols_p if c in df_exibicao.columns]].copy()
                        df_t3.rename(columns={COLUNA_PERCENTUAL_TJPE_INTERNO: "TJPE (%)", COLUNA_PERCENTUAL_TRF5_INTERNO: "TRF5 (%)", COLUNA_PERCENTUAL_TRT6_INTERNO: "TRT6 (%)"}, inplace=True)
                        for c in ["TJPE (%)", "TRF5 (%)", "TRT6 (%)"]: df_t3[c] = df_t3[c].apply(lambda x: converter_e_formatar(x, 'percentual'))
                    else:
                        cols_r = ["ENTE", COLUNA_TJPE_SIMPLES_INTERNO, COLUNA_TRF5_SIMPLES_INTERNO, COLUNA_TRT6_SIMPLES_INTERNO]
                        df_t3 = df_exibicao[[c for c in cols_r if c in df_exibicao.columns]].copy()
                        df_t3.rename(columns={COLUNA_TJPE_SIMPLES_INTERNO: "TJPE (R$)", COLUNA_TRF5_SIMPLES_INTERNO: "TRF5 (R$)", COLUNA_TRT6_SIMPLES_INTERNO: "TRT6 (R$)"}, inplace=True)
                        for c in ["TJPE (R$)", "TRF5 (R$)", "TRT6 (R$)"]: df_t3[c] = df_t3[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    st.dataframe(df_t3, use_container_width=True, hide_index=True)

                with t4:
                    div_v = st.radio("Situação:", ["Total", "Em Mora", "Vincendos"], key="dv", horizontal=True)
                    map_div = {
                        "Em Mora": (["ENTE", "ESTOQUE EM MORA - [TJPE]", "ESTOQUE EM MORA - [TRF5]", "ESTOQUE EM MORA - [TRT6]", "ESTOQUE EM MORA"], {"ESTOQUE EM MORA - [TJPE]": "TJPE (Mora)", "ESTOQUE EM MORA - [TRF5]": "TRF5 (Mora)", "ESTOQUE EM MORA - [TRT6]": "TRT6 (Mora)", "ESTOQUE EM MORA": "TOTAL MORA"}),
                        "Vincendos": (["ENTE", "ESTOQUE VINCENDOS - [TJPE]", "ESTOQUE VINCENDOS - [TRF5]", "ESTOQUE VINCENDOS - [TRT6]", "ESTOQUE VINCENDOS"], {"ESTOQUE VINCENDOS - [TJPE]": "TJPE (Vinc)", "ESTOQUE VINCENDOS - [TRF5]": "TRF5 (Vinc)", "ESTOQUE VINCENDOS - [TRT6]": "TRT6 (Vinc)", "ESTOQUE VINCENDOS": "TOTAL VINC"}),
                        "Total": (["ENTE", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]", COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY], {"ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]": "TJPE (Tot)", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]": "TRF5 (Tot)", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]": "TRT6 (Tot)", COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY: "TOTAL DÍVIDA"})
                    }
                    c_orig, c_disp = map_div[div_v]
                    df_t4 = df_exibicao[[c for c in c_orig if c in df_exibicao.columns]].copy()
                    df_t4.rename(columns=c_disp, inplace=True)
                    for c in df_t4.columns: 
                        if c != "ENTE": df_t4[c] = df_t4[c].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    st.dataframe(df_t4, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Erro: {e}")

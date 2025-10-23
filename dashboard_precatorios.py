import streamlit as st
import pandas as pd
import numpy as np 

# --- Configuração da página ---
st.set_page_config(
    page_title="💰 Painel de Precatórios: Foco e Detalhe",
    layout="wide", # Usar a largura máxima da tela
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO EXPLICITA BRASILEIRA (R$ 1.234.567,89)
# ----------------------------------------------------
def formatar_br(valor, formato):
    """Formata um float ou int para o padrão monetário/percentual brasileiro (ponto milhar, vírgula decimal)."""
    try:
        if pd.isna(valor) or valor is None:
            return "-"
        
        # Inverte a formatação americana para simular o padrão brasileiro (milhar = ., decimal = ,).
        if formato == 'moeda':
            return f"R$ {valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        elif formato == 'percentual':
            return f"{valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        else: # Formato genérico com 2 casas
            return f"{valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    except Exception:
        return "-"


# ----------------------------------------------------
# 1. Widget de Upload (na Sidebar)
# ----------------------------------------------------
with st.sidebar:
    st.header("📁 Upload de Dados")
    uploaded_file = st.file_uploader(
        "1. Carregar 'Painel-Entes.csv'",
        type=['csv'],
        help="O arquivo deve ser formatado com ponto-e-vírgula (;)"
    )

# NOVO TÍTULO EM AZUL PROFUNDO
st.markdown("<h1 style='color: #00BFFF;'>💰 Visão Geral Financeira de Precatórios</h1>", unsafe_allow_html=True)
st.caption("Organização Foco e Detalhe por Ente Devedor")
st.markdown("---") 

# ----------------------------------------------------
# Processamento Condicional
# ----------------------------------------------------
if uploaded_file is not None:
    
    with st.spinner('⏳ Carregando e processando os indicadores...'):
        try:
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- Limpeza e Conversão de Colunas Numéricas ---
            colunas_numericas = [
                "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]
            for col in colunas_numericas:
                if col in df.columns:
                    df[col] = (df[col].astype(str).str.replace(r'[R$\(\)]', '', regex=True) 
                        .str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip())
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            colunas_criticas = ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES"]
            if not all(col in df.columns for col in colunas_criticas):
                 st.error(f"Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(colunas_criticas)}. Verifique o cabeçalho.")
                 st.stop()
                 
            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros (na Sidebar) ---
            with st.sidebar:
                st.markdown("---")
                st.header("⚙️ Filtros Analíticos")
                
                status_lista_limpa = df["STATUS"].dropna().unique().tolist()
                status_lista = [s for s in status_lista_limpa if s.lower() != 'nan' and s is not np.nan]
                entes_lista = df["ENTE"].unique().tolist()
                
                selected_ente = st.selectbox("👤 Ente Devedor:", options=["Todos"] + sorted(entes_lista))
                selected_status = st.selectbox("🚦 Status da Dívida:", options=["Todos"] + sorted(status_lista))
            
            # 4. Aplicação dos filtros
            filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            df_filtrado = df[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # INÍCIO DO NOVO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (4 KPIs) ---
                st.header("📈 Indicadores Consolidado (Total)")
                
                total_divida = df_filtrado["ENDIVIDAMENTO TOTAL"].sum()
                total_aportes = df_filtrado["APORTES"].sum()
                saldo_a_pagar = df_filtrado["SALDO A PAGAR"].sum()
                num_entes = df_filtrado["ENTE"].nunique()

                # 4 Colunas, incluindo o contador de entes
                col_entes, col_divida, col_aportes, col_saldo = st.columns(4)
                
                with col_entes:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col_divida:

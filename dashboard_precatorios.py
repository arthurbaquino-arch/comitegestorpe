import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(
    page_title="Dashboard de Precatórios - EC 136/2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 1. Widget de Upload (na Sidebar)
# ----------------------------------------------------
with st.sidebar:
    st.header("Upload de Dados")
    uploaded_file = st.file_uploader(
        "1. Carregar 'Painel-Entes.csv'",
        type=['csv'],
        help="O arquivo deve ser formatado com ponto-e-vírgula (;)"
    )

st.title("Monitoramento de Precatórios (EC 136/2025)")
st.caption("Organização e Análise por Ente Devedor")

# ----------------------------------------------------
# Processamento Condicional
# ----------------------------------------------------
if uploaded_file is not None:
    # Adicionar um 'spinner' para dar feedback profissional
    with st.spinner('Processando e limpando dados...'):
        try:
            # 2. Leitura do arquivo (usando o separador ;)
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- CORREÇÃO: Limpeza e Conversão de Colunas Numéricas ---
            
            # 1. Definir as colunas que DEVEM ser numéricas no formato Real Brasileiro
            colunas_numericas = [
                "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]

            # 2. Iterar e limpar cada coluna
            for col in colunas_numericas:
                if col in df.columns:
                    # Remove R$, parênteses, pontos de milhar, e substitui vírgula decimal por ponto
                    df[col] = (
                        df[col]
                        .astype(str) # Garante que está como string para a limpeza
                        .str.replace(r'[R$\(\)]', '', regex=True) # Remove R$, (, e )
                        .str.replace('.', '', regex=False) # Remove pontos (separador de milhares)
                        .str.replace(',', '.', regex=False) # Troca vírgula por ponto (separador decimal)
                        .str.strip() # Remove espaços em branco
                    )
                    # Força a conversão para numérico (float). errors='coerce' transforma erros em NaN.
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # 3. Tratar colunas categóricas e verificar a existência das colunas críticas
            colunas_criticas = ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES"]
            if not all(col in df.columns for col in colunas_criticas):
                 st.error(f"Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(colunas_criticas)}. Verifique o cabeçalho.")
                 st.stop()
                 
            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
                 
        except Exception as e:
            st.error(f"Ocorreu um erro fatal durante a leitura ou

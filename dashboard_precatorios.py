import streamlit as st
import pandas as pd
import numpy as np # Necessário para identificar NaN

# --- Configuração da página ---
st.set_page_config(
    page_title="Painel de Controle: Monitoramento de Precatórios (EC 136/2025)",
    layout="wide", # Usar a largura máxima da tela
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

st.title("Painel de Controle: Precatórios por Ente Devedor")
st.caption("Foco em Métricas e Indicadores Chave (KPIs)")
st.markdown("---") 

# ----------------------------------------------------
# Processamento Condicional
# ----------------------------------------------------
if uploaded_file is not None:
    
    with st.spinner('Carregando e processando os indicadores...'):
        try:
            # 2. Leitura do arquivo (usando o separador ;)
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- Limpeza e Conversão de Colunas Numéricas (Corrigido) ---
            
            colunas_numericas = [
                "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]

            for col in colunas_numericas:
                if col in df.columns:
                    df[col] = (
                        df[col]
                        .astype(str)
                        .str.replace(r'[R$\(\)]', '', regex=True) 
                        .str.replace('.', '', regex=False) 
                        .str.replace(',', '.', regex=False) 
                        .str.strip()
                    )
                    # Força a conversão para float, convertendo erros (strings residuais) para NaN
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # 3. Verificação de Colunas Críticas
            colunas_criticas = ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES"]
            if not all(col in df.columns for col in colunas_criticas):
                 st.error(f"Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(colunas_criticas)}. Verifique o cabeçalho.")
                 st.stop()
                 
            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros (na Sidebar) ---
            with st.sidebar:
                st.markdown("---")
                st.header("Filtros Analíticos")
                
                # Remoção de 'nan' dos filtros de Status
                status_lista_limpa = df["STATUS"].dropna().unique().tolist()
                status_lista = [s for s in status_lista_limpa if s.lower() != 'nan' and s is not np.nan]
                
                entes_lista = df["ENTE"].unique().tolist()
                
                # Filtro Selectbox Ente Devedor (lista suspensa)
                selected_ente = st.selectbox(
                    "Ente Devedor:", 
                    options=["Todos"] + sorted(entes_lista) 
                )
                
                # Filtro Selectbox de Status
                selected_status = st.selectbox(
                    "Status da Dívida:", 
                    options=["Todos"] + sorted(status_lista)
                )
            
            # 4. Aplicação dos filtros
            filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            
            df_filtrado = df[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # Layout Painel (Modo Escuro e Foco em Tabela/Métrica)
            # ----------------------------------------------------
            
            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (KPIs) ---
                st.header("Indicadores de Desempenho Chave")
                
                # Cálculo dos KPIs
                total_divida = df_filtrado["ENDIVIDAMENTO TOTAL"].sum()
                total_aportes = df_filtrado["APORTES"].sum()
                saldo_a_pagar = df_filtrado["SALDO A PAGAR"].sum()
                num_entes = df_filtrado["ENTE"].nunique()
                
                col_entes, col_divida, col_aportes, col_saldo = st.columns(4)
                
                with col_entes:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col_divida:
                    st.metric(label="Endividamento Total (R$)", value=f"R$ {total_divida:,.2f}")
                with col_aportes:
                    st.metric(label="Total de Aportes (R$)", value=f"R$ {total_aportes:,.2f}")
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=f"R$ {saldo_a_pagar:,.2f}")
                
                st.markdown("---") 

                # --- Seção 2: Tabela de Resumo (Foco Principal do Painel) ---
                st.header("Resumo da Situação por Ente (Tabela Principal)")
                
                colunas_resumo = [
                    "ENTE", 
                    "STATUS", 
                    "ENDIVIDAMENTO TOTAL", 
                    "APORTES", 
                    "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                # Seleciona colunas e remove NaN da coluna STATUS (para manter a coerência)
                df_resumo = df_filtrado[[col for col in colunas_resumo if col in df_filtrado.columns]].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                
                # FORMATOS PARA TABELAS (GARANTINDO QUE APENAS COLUNAS NUMÉRICAS SEJAM FORMATADAS)
                formatos = {}
                if "ENDIVIDAMENTO TOTAL" in df_resumo.columns:
                    formatos["ENDIVIDAMENTO TOTAL"] = "R$ {:,.2f}"
                if "APORTES" in df_resumo.columns:
                    formatos["APORTES"] = "R$ {:,.2f}"
                if "SALDO A PAGAR" in df_resumo.columns:
                    formatos["SALDO A PAGAR"] = "R$ {:,.2f}"
                if "DÍVIDA EM MORA / RCL" in df_resumo.columns:
                    formatos["DÍVIDA EM MORA / RCL"] = "{:.2f}%"


                df_resumo_styled = df_resumo.style.format(formatos, na_rep="-") # 'na_rep' garante que NaN seja exibido como '-', mas SÓ na visualização

                st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- Seção 3: Detalhes dos Índices e Aportes (em abas para organizar o layout) ---
                st.header("Análise Detalhada (Índices e Tribunais)")
                
                tab1, tab2 = st.tabs(["📊 Detalhes de Índices (RCL)", "🏛️ Detalhes de Aportes por Tribunal"])
                
                with tab1:
                    st.subheader("Índices e Responsabilidade Fiscal")
                    colunas_indices = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_indices = df_filtrado[[col for col in colunas_indices if col in df_filtrado.columns]].sort_values(by="DÍVIDA EM MORA / RCL", ascending=False)
                    
                    formatos_indices = {}
                    if "RCL 2024" in df_indices.columns:
                        formatos_indices["RCL 2024"] = "R$ {:,.2f}"
                    if "DÍVIDA EM MORA / RCL" in df_indices.columns:
                        formatos_indices["DÍVIDA EM MORA / RCL"] = "{:.2f}%"
                    if "% TJPE" in df_indices.columns:
                        formatos_indices["% TJPE"] = "{:.2f}%"
                    if "% TRF5" in df_indices.columns:
                        formatos_indices["% TRF5"] = "{:.2f}%"
                    if "% TRT6" in df_indices.columns:
                        formatos_indices["% TRT6"] = "{:.2f}%"
                        
                    df_indices_styled = df_indices.style.format(formatos_indices, na_rep="-")
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("Distribuição de Aportes (TJPE, TRF5, TRT6)")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes = df_filtrado[[col for col in colunas_aportes if col in df_filtrado.columns]]
                    
                    formatos_aportes = {}
                    if "APORTES - [TJPE]" in df_aportes.columns:
                         formatos_aportes["APORTES - [TJPE]"] = "R$ {:,.2f}"
                    if "APORTES - [TRF5]" in df_aportes.columns:
                         formatos_aportes["APORTES - [TRF5]"] = "R$ {:,.2f}"
                    if "APORTES - [TRT6]" in df_aportes.columns:
                         formatos_aportes["APORTES - [TRT6]"] = "R$ {:,.2f}"

                    df_aportes_styled = df_aportes.style.format(formatos_aportes, na_rep="-")
                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento. Verifique se o formato do seu CSV está correto (separador ';'). Detalhes: {e}")

else:
    # Mensagem quando o arquivo não está carregado
    st.info("Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do painel de controle.")

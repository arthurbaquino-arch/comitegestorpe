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
st.markdown("---") # Linha separadora elegante

# ----------------------------------------------------
# Processamento Condicional
# ----------------------------------------------------
if uploaded_file is not None:
    # Adicionar um 'spinner' para dar feedback profissional
    with st.spinner('Carregando e processando os indicadores...'):
        try:
            # 2. Leitura do arquivo (usando o separador ;)
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- Limpeza e Conversão de Colunas Numéricas (Corrigindo o erro 'f' para 'str') ---
            
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
                
                # Remoção do 'nan' para filtros limpos
                status_lista_limpa = df["STATUS"].dropna().unique().tolist()
                status_lista = [s for s in status_lista_limpa if s.lower() != 'nan' and s is not np.nan]
                entes_lista = df["ENTE"].unique().tolist()
                
                # Filtro Selectbox Ente Devedor
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
            # Novo Layout: Foco em Painel e KPIs (Dark Mode)
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
                
                # Layout de colunas para os KPIs
                col_entes, col_divida, col_aportes, col_saldo = st.columns(4)
                
                with col_entes:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col_divida:
                    # Usando delta para mostrar a diferença (pode ser ajustado para mostrar a dívida anterior, se disponível)
                    st.metric(label="Endividamento Total (R$)", value=f"R$ {total_divida:,.2f}")
                with col_aportes:
                    st.metric(label="Total de Aportes (R$)", value=f"R$ {total_aportes:,.2f}")
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=f"R$ {saldo_a_pagar:,.2f}")
                
                st.markdown("---") 

                # --- Seção 2: Tabela de Status e Dívida por Ente ---
                st.header("Resumo da Situação por Ente")
                
                # Tabela Consolidada (Mais limpa e com formatação de números)
                df_resumo = df_filtrado[[
                    "ENTE", 
                    "STATUS", 
                    "ENDIVIDAMENTO TOTAL", 
                    "APORTES", 
                    "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False).fillna('-')

                # Formatação de Moeda na Tabela
                df_resumo_styled = df_resumo.style.format({
                    "ENDIVIDAMENTO TOTAL": "R$ {:,.2f}",
                    "APORTES": "R$ {:,.2f}",
                    "SALDO A PAGAR": "R$ {:,.2f}",
                    "DÍVIDA EM MORA / RCL": "{:.2f}%"
                })

                st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- Seção 3: Detalhes dos Índices e Aportes (em abas) ---
                st.header("Análise Detalhada de Índices e Aportes")
                
                tab1, tab2 = st.tabs(["📊 Índices e RCL", "🏛️ Aportes por Tribunal"])
                
                with tab1:
                    st.subheader("Índices e Responsabilidade Fiscal")
                    df_indices = df_filtrado[[
                        "ENTE", 
                        "RCL 2024", 
                        "DÍVIDA EM MORA / RCL"
                    ]].sort_values(by="DÍVIDA EM MORA / RCL", ascending=False).fillna('-')
                    
                    df_indices_styled = df_indices.style.format({
                        "RCL 2024": "R$ {:,.2f}",
                        "DÍVIDA EM MORA / RCL": "{:.2f}%"
                    })
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("Distribuição de Aportes (TJPE, TRF5, TRT6)")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes = df_filtrado[[col for col in colunas_aportes if col in df_filtrado.columns]].fillna(0)
                    
                    df_aportes_styled = df_aportes.style.format({
                        "APORTES - [TJPE]": "R$ {:,.2f}",
                        "APORTES - [TRF5]": "R$ {:,.2f}",
                        "APORTES - [TRT6]": "R$ {:,.2f}",
                    })
                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado. Detalhes: {e}")

else:
    # Mensagem quando o arquivo não está carregado
    st.info("Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do painel de controle.")

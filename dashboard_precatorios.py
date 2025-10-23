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
# FUNÇÃO DE FORMATAÇÃO EXPLICITA BRASILEIRA (Para corrigir o formato americano)
# ----------------------------------------------------
def formatar_br(valor, formato):
    """Formata um float ou int para o padrão monetário brasileiro (ponto milhar, vírgula decimal)."""
    try:
        if pd.isna(valor) or valor is None:
            return "-"
        
        # O truque abaixo usa a formatação padrão do Python (que é americana) e inverte os separadores
        # para simular o padrão brasileiro (milhar = ., decimal = ,).
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
            
            # --- Limpeza e Conversão de Colunas Numéricas ---
            
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
                
                status_lista_limpa = df["STATUS"].dropna().unique().tolist()
                status_lista = [s for s in status_lista_limpa if s.lower() != 'nan' and s is not np.nan]
                
                entes_lista = df["ENTE"].unique().tolist()
                
                selected_ente = st.selectbox(
                    "Ente Devedor:", 
                    options=["Todos"] + sorted(entes_lista) 
                )
                
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
                    st.metric(label="Endividamento Total (R$)", value=formatar_br(total_divida, 'moeda'))
                with col_aportes:
                    st.metric(label="Total de Aportes (R$)", value=formatar_br(total_aportes, 'moeda'))
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=formatar_br(saldo_a_pagar, 'moeda'))
                
                st.markdown("---") 

                # --- Seção 2: Tabela de Resumo ---
                st.header("Resumo da Situação por Ente (Tabela Principal)")
                
                colunas_resumo = [
                    "ENTE", 
                    "STATUS", 
                    "ENDIVIDAMENTO TOTAL", 
                    "APORTES", 
                    "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                df_resumo = df_filtrado[[col for col in colunas_resumo if col in df_filtrado.columns]].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                
                df_resumo_styled = df_resumo.copy()
                
                # Aplica a formatação de moeda e percentual explicitamente para exibição
                for col in ["ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR", "RCL 2024"]:
                    if col in df_resumo_styled.columns:
                        df_resumo_styled[col] = df_resumo_styled[col].apply(lambda x: formatar_br(x, 'moeda'))
                        
                for col in ["DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]:
                    if col in df_resumo_styled.columns:
                        df_resumo_styled[col] = df_resumo_styled[col].apply(lambda x: formatar_br(x, 'percentual'))

                st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- Seção 3: Detalhes dos Índices e Aportes (em abas) ---
                st.header("Análise Detalhada (Índices e Tribunais)")
                
                tab1, tab2 = st.tabs(["📊 Detalhes de Índices (RCL)", "🏛️ Detalhes de Aportes por Tribunal"])
                
                with tab1:
                    st.subheader("Índices e Responsabilidade Fiscal")
                    colunas_indices = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_indices = df_filtrado[[col for col in colunas_indices if col in df_filtrado.columns]].sort_values(by="DÍVIDA EM MORA / RCL", ascending=False)
                    
                    df_indices_styled = df_indices.copy()
                    
                    if "RCL 2024" in df_indices_styled.columns:
                        df_indices_styled["RCL 2024"] = df_indices_styled["RCL 2024"].apply(lambda x: formatar_br(x, 'moeda'))
                    if "DÍVIDA EM MORA / RCL" in df_indices_styled.columns:
                        df_indices_styled["DÍVIDA EM MORA / RCL"] = df_indices_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: formatar_br(x, 'percentual'))
                    if "% TJPE" in df_indices_styled.columns:
                        df_indices_styled["% TJPE"] = df_indices_styled["% TJPE"].apply(lambda x: formatar_br(x, 'percentual'))
                    if "% TRF5" in df_indices_styled.columns:
                        df_indices_styled["% TRF5"] = df_indices_styled["% TRF5"].apply(lambda x: formatar_br(x, 'percentual'))
                    if "% TRT6" in df_indices_styled.columns:
                        df_indices_styled["% TRT6"] = df_indices_styled["% TRT6"].apply(lambda x: formatar_br(x, 'percentual'))
                        
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("Distribuição de Aportes (TJPE, TRF5, TRT6)")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes = df_filtrado[[col for col in colunas_aportes if col in df_filtrado.columns]]
                    
                    df_aportes_styled = df_aportes.copy()
                    
                    if "APORTES - [TJPE]" in df_aportes_styled.columns:
                         df_aportes_styled["APORTES - [TJPE]"] = df_aportes_styled["APORTES - [TJPE]"].apply(lambda x: formatar_br(x, 'moeda'))
                    if "APORTES - [TRF5]" in df_aportes_styled.columns:
                         df_aportes_styled["APORTES - [TRF5]"] = df_aportes_styled["APORTES - [TRF5]"].apply(lambda x: formatar_br(x, 'moeda'))
                    if "APORTES - [TRT6]" in df_aportes_styled.columns:
                         df_aportes_styled["APORTES - [TRT6]"] = df_aportes_styled["APORTES - [TRT6]"].apply(lambda x: formatar_br(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado durante o processamento. Verifique se o formato do seu CSV está correto (separador ';'). Detalhes: {e}")

# CORREÇÃO DA INDENTAÇÃO NA LINHA 120 (OU PRÓXIMA)
else:
    # Mensagem quando o arquivo não está carregado
    st.info("Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do painel de controle.")

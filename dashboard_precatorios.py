import streamlit as st
import pandas as pd
import numpy as np 

# --- Configuração da página ---
st.set_page_config(
    page_title="💜 Painel de Precatórios: Visão Segmentada",
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
        
        # O truque abaixo inverte a formatação americana para simular o padrão brasileiro (milhar = ., decimal = ,).
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

# NOVO TÍTULO EM ROXO/MAGENTA
st.markdown("<h1 style='color: #8A2BE2;'>💜 🚀 Painel de Precatórios: Visão Segmentada</h1>", unsafe_allow_html=True)
st.caption("Organização de Dados Fiscais e Jurídicos por Ente Devedor")
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
            # INÍCIO DO NOVO LAYOUT SEGMENTADO
            # ----------------------------------------------------
            
            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (3 KPIs) ---
                st.header("💰 Visão Geral Financeira")
                
                total_divida = df_filtrado["ENDIVIDAMENTO TOTAL"].sum()
                total_aportes = df_filtrado["APORTES"].sum()
                saldo_a_pagar = df_filtrado["SALDO A PAGAR"].sum()
                
                # Apenas 3 colunas para foco nos valores
                col_divida, col_aportes, col_saldo = st.columns(3)
                
                with col_divida:
                    st.metric(label="Endividamento Total (R$)", value=formatar_br(total_divida, 'moeda'))
                with col_aportes:
                    st.metric(label="Total de Aportes (R$)", value=formatar_br(total_aportes, 'moeda'))
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=formatar_br(saldo_a_pagar, 'moeda'))
                
                st.markdown("---") 

                # --- Bloco 2: Risco Fiscal e Percentuais (2 Colunas) ---
                st.header("📊 Risco Fiscal e Distribuição de Dívida")
                
                col_fiscal, col_tribunal = st.columns(2)
                
                # Coluna Esquerda: RCL e Dívida/RCL
                with col_fiscal:
                    st.subheader("Risco Fiscal")
                    colunas_fiscal = ["ENTE", "STATUS", "RCL 2024", "DÍVIDA EM MORA / RCL"]
                    df_fiscal = df_filtrado[[col for col in colunas_fiscal if col in df_filtrado.columns]].sort_values(by="DÍVIDA EM MORA / RCL", ascending=False)
                    
                    df_fiscal_styled = df_fiscal.copy()
                    if "RCL 2024" in df_fiscal_styled.columns:
                        df_fiscal_styled["RCL 2024"] = df_fiscal_styled["RCL 2024"].apply(lambda x: formatar_br(x, 'moeda'))
                    if "DÍVIDA EM MORA / RCL" in df_fiscal_styled.columns:
                        df_fiscal_styled["DÍVIDA EM MORA / RCL"] = df_fiscal_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: formatar_br(x, 'percentual'))

                    st.dataframe(df_fiscal_styled, use_container_width=True, hide_index=True)

                # Coluna Direita: Percentuais por Tribunal
                with col_tribunal:
                    st.subheader("Distribuição da Dívida (%)")
                    colunas_tribunal = ["ENTE", "% TJPE", "% TRF5", "% TRT6"]
                    df_tribunal = df_filtrado[[col for col in colunas_tribunal if col in df_filtrado.columns]]
                    
                    df_tribunal_styled = df_tribunal.copy()
                    for col in ["% TJPE", "% TRF5", "% TRT6"]:
                        if col in df_tribunal_styled.columns:
                            df_tribunal_styled[col] = df_tribunal_styled[col].apply(lambda x: formatar_br(x, 'percentual'))
                            
                    st.dataframe(df_tribunal_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- Bloco 3: Detalhe dos Aportes (Expander) ---
                with st.expander("💸 Detalhe dos Aportes por Tribunal (Clique para Expandir)"):
                    st.subheader("Aportes Detalhados por Ente e Tribunal")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes = df_filtrado[[col for col in colunas_aportes if col in df_filtrado.columns]]
                    df_aportes_styled = df_aportes.copy()
                    
                    for col in ["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]:
                        if col in df_aportes_styled.columns:
                             df_aportes_styled[col] = df_aportes_styled[col].apply(lambda x: formatar_br(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)


                st.markdown("---")
                
                # --- Seção 4: Tabela de Resumo Principal ---
                st.header("📋 Resumo da Situação por Ente (Tabela Principal)")
                
                colunas_resumo = [
                    "ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                df_resumo = df_filtrado[[col for col in colunas_resumo if col in df_filtrado.columns]].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                df_resumo_styled = df_resumo.copy()
                
                for col in ["ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR"]:
                    if col in df_resumo_styled.columns:
                        df_resumo_styled[col] = df_resumo_styled[col].apply(lambda x: formatar_br(x, 'moeda'))
                        
                if "DÍVIDA EM MORA / RCL" in df_resumo_styled.columns:
                    df_resumo_styled["DÍVIDA EM MORA / RCL"] = df_resumo_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: formatar_br(x, 'percentual'))

                st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado durante o processamento. Verifique se o formato do seu CSV está correto (separador ';'). Detalhes: {e}")

else:
    # Mensagem quando o arquivo não está carregado
    st.info("ℹ️ Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do painel de controle.")

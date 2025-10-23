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
    """
    Formata um valor (float) para o padrão monetário/percentual brasileiro.
    Se o formato for 'DÍVIDA_TEXTO', apenas adiciona o % na string.
    """
    try:
        if pd.isna(valor) or valor is None:
            return "-"
        
        # Caso especial para a coluna problemática (tratada como string)
        if formato == 'DÍVIDA_TEXTO':
            # Remove % se houver e adiciona de volta
            str_valor = str(valor).strip().replace('%', '')
            # Mantém a vírgula/ponto do original, apenas adiciona o %
            return f"{str_valor}%"
        
        # Inverte a formatação americana para simular o padrão brasileiro (milhar = ., decimal = ,).
        if formato == 'moeda':
            return f"R$ {valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        elif formato == 'percentual':
            # Formata o número (ex: 95.0) para 95,00%
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

# TÍTULO EM AZUL PROFUNDO
st.markdown("<h1 style='color: #00BFFF;'>💰 Visão Geral Financeira de Precatórios</h1>", unsafe_allow_html=True)
st.caption("Organização Foco e Detalhe por Ente Devedor")
st.markdown("---") 

# ----------------------------------------------------
# Processamento Condicional
# ----------------------------------------------------
if uploaded_file is not None:
    
    with st.spinner('⏳ Carregando e processando os indicadores...'):
        try:
            # Lista de colunas que devem ser lidas como STRING
            colunas_string = ["DÍVIDA EM MORA / RCL"]
            
            # Lê o CSV com a instrução para ler a coluna problemática como string
            df = pd.read_csv(uploaded_file, delimiter=";", dtype={col: str for col in colunas_string})
            
            # --- REMOVER A ÚLTIMA LINHA (TOTALIZAÇÃO) ---
            df = df.iloc[:-1]
            
            # --- Limpeza e Conversão de Colunas Numéricas ---
            # Remove a coluna DÍVIDA EM MORA / RCL da lista de colunas a serem convertidas
            colunas_numericas_float = [
                "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "SALDO A PAGAR", 
                "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]
            
            for col in colunas_numericas_float:
                if col in df.columns:
                    # 1. Limpeza: remove R$, (), %
                    df[col] = df[col].astype(str).str.replace(r'[R$\(\)%,]', '', regex=True).str.strip()
                    
                    # 2. ESSENCIAL: Troca PONTO por VÍRGULA e VÍRGULA por PONTO (Padrão BR -> Padrão Float)
                    df[col] = df[col].str.replace('.', 'TEMP', regex=False) # Protege o ponto milhar
                    df[col] = df[col].str.replace(',', '.', regex=False)    # Transforma vírgula decimal em ponto decimal
                    df[col] = df[col].str.replace('TEMP', '', regex=False)  # Remove o separador de milhar

                    # 3. Conversão para float
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
            # INÍCIO DO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (4 KPIs) ---
                st.header("📈 Indicadores Consolidado (Total)")
                
                # Para o cálculo de KPI, a DÍVIDA EM MORA / RCL não é somada, então não precisamos nos preocupar.
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

                # --- Seção 2: Tabela Principal (Resumo de Foco) ---
                st.header("📋 Resumo da Situação por Ente (Foco Principal)")
                
                colunas_resumo = [
                    "ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                df_resumo = df_filtrado[[col for col in colunas_resumo if col in df_filtrado.columns]].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                df_resumo_styled = df_resumo.copy()
                
                for col in ["ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR"]:
                    if col in df_resumo_styled.columns:
                        df_resumo_styled[col] = df_resumo_styled[col].apply(lambda x: formatar_br(x, 'moeda'))
                        
                # APLICA O FORMATO DÍVIDA_TEXTO para apenas anexar o %
                if "DÍVIDA EM MORA / RCL" in df_resumo_styled.columns:
                    df_resumo_styled["DÍVIDA EM MORA / RCL"] = df_resumo_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: formatar_br(x, 'DÍVIDA_TEXTO'))

                st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- Seção 3: Detalhes Técnicos (Abas) ---
                st.header("🔎 Análise Detalhada de Índices e Aportes")
                
                tab1, tab2 = st.tabs(["📊 Índices Fiscais e RCL", "⚖️ Aportes Detalhados por Tribunal"])
                
                with tab1:
                    st.subheader("RCL e Percentuais por Tribunal")
                    colunas_indices = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_indices = df_filtrado[[col for col in colunas_indices if col in df_filtrado.columns]].sort_values(by="DÍVIDA EM MORA / RCL", ascending=False)
                    df_indices_styled = df_indices.copy()
                    
                    if "RCL 2024" in df_indices_styled.columns:
                        df_indices_styled["RCL 2024"] = df_indices_styled["RCL 2024"].apply(lambda x: formatar_br(x, 'moeda'))
                    
                    # DÍVIDA EM MORA / RCL é tratada como texto
                    if "DÍVIDA EM MORA / RCL" in df_indices_styled.columns:
                        df_indices_styled["DÍVIDA EM MORA / RCL"] = df_indices_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: formatar_br(x, 'DÍVIDA_TEXTO'))
                        
                    # Os outros percentuais continuam como números (float)
                    for col in ["% TJPE", "% TRF5", "% TRT6"]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: formatar_br(x, 'percentual'))
                        
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("Valores Aportados por Tribunal")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes = df_filtrado[[col for col in colunas_aportes if col in df_filtrado.columns]]
                    df_aportes_styled = df_aportes.copy()
                    
                    for col in ["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]:
                        if col in df_aportes_styled.columns:
                             df_aportes_styled[col] = df_aportes_styled[col].apply(lambda x: formatar_br(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado durante o processamento. Verifique se o formato do seu CSV está correto (separador ';'). Detalhes: {e}")

else:
    # Mensagem quando o arquivo não está carregado
    st.info("ℹ️ Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do painel de controle.")

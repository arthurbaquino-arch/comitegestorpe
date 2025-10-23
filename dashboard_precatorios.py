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
# FUNÇÃO DE FORMATAÇÃO E CONVERSÃO (Mais Simples)
# ----------------------------------------------------
def converter_e_formatar(valor, formato):
    """
    Tenta converter uma string (formato BR) para float e a formata.
    Se falhar, retorna o valor original (string) ou '-'.
    """
    if pd.isna(valor) or valor is None or valor == "":
        return "-"
    
    str_valor = str(valor).strip().replace(r'[R$\(\)%,]', '', regex=True)
    
    # 1. Tentar converter para float (Assumindo formato BR: vírgula decimal)
    try:
        # 1.1 Limpeza e conversão de formato BR para float: 
        # R$ 1.234.567,89 -> "1.234.567,89" -> "1234567.89" -> 1234567.89
        str_limpa = str_valor.replace('.', 'TEMP').replace(',', '.').replace('TEMP', '')
        num_valor = float(str_limpa)

        # 2. Formatação
        if formato == 'moeda':
            return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        elif formato == 'percentual':
            # Assume que o valor lido (0.41 ou 95) é o valor numérico a ser exibido.
            return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        else:
            return str(num_valor)
            
    except Exception:
        # Se a conversão falhar (ex: célula vazia ou com erro), retorna o valor original
        return str_valor

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
            # Lendo o CSV SEM FORÇAR NENHUM TIPO, DEIXANDO COMO STRING
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- REMOVER A ÚLTIMA LINHA (TOTALIZAÇÃO) ---
            df = df.iloc[:-1].copy()
            
            # --- Conversão para DataFrame de TRABALHO (apenas para filtros e gráficos) ---
            
            # Colunas que precisam ser FLOAT para somas/filtros/gráficos
            colunas_para_float = [
                "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]

            # Cria um DataFrame de trabalho temporário (df_float) para cálculos
            df_float = df.copy()
            
            # Aplica a limpeza e conversão de formato BR para float em todas as colunas numéricas
            for col in colunas_para_float:
                if col in df_float.columns:
                    str_series = df_float[col].astype(str).str.replace(r'[R$\(\)%,]', '', regex=True).str.strip()
                    str_limpa = str_series.str.replace('.', 'TEMP', regex=False).str.replace(',', '.', regex=False).str.replace('TEMP', '', regex=False)
                    df_float[col] = pd.to_numeric(str_limpa, errors='coerce')


            colunas_criticas = ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES"]
            if not all(col in df_float.columns for col in colunas_criticas):
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
            
            # 4. Aplicação dos filtros no DataFrame original e no de cálculo
            filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            
            # Filtrado para exibição (DF_FILTRADO)
            df_filtrado_exibicao = df[filtro_status & filtro_entes]
            # Filtrado para cálculos (DF_FLOAT_FILTRADO)
            df_filtrado_calculo = df_float[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # INÍCIO DO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado_exibicao.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (4 KPIs) ---
                st.header("📈 Indicadores Consolidado (Total)")
                
                # USANDO O DF DE CÁLCULO (DF_FLOAT_FILTRADO)
                total_divida = df_filtrado_calculo["ENDIVIDAMENTO TOTAL"].sum()
                total_aportes = df_filtrado_calculo["APORTES"].sum()
                saldo_a_pagar = df_filtrado_calculo["SALDO A PAGAR"].sum()
                num_entes = df_filtrado_calculo["ENTE"].nunique()

                col_entes, col_divida, col_aportes, col_saldo = st.columns(4)
                
                with col_entes:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col_divida:
                    st.metric(label="Endividamento Total (R$)", value=converter_e_formatar(total_divida, 'moeda'))
                with col_aportes:
                    st.metric(label="Total de Aportes (R$)", value=converter_e_formatar(total_aportes, 'moeda'))
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=converter_e_formatar(saldo_a_pagar, 'moeda'))
                
                st.markdown("---") 

                # --- Seção 2: Tabela Principal (Resumo de Foco) ---
                st.header("📋 Resumo da Situação por Ente (Foco Principal)")
                
                colunas_resumo = [
                    "ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                # ORDENAÇÃO USANDO O DF DE CÁLCULO
                df_resumo_float = df_filtrado_calculo.sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                # SELECIONA AS LINHAS ORDENADAS NO DF DE EXIBIÇÃO
                df_resumo = df_filtrado_exibicao.set_index('ENTE').loc[df_resumo_float['ENTE']].reset_index()
                df_resumo_styled = df_resumo[[col for col in colunas_resumo if col in df_resumo.columns]].copy()
                
                # APLICA FORMATO (converter_e_formatar AGORA ACEITA STRING OU FLOAT)
                for col in ["ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR"]:
                    if col in df_resumo_styled.columns:
                        df_resumo_styled[col] = df_resumo_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                        
                if "DÍVIDA EM MORA / RCL" in df_resumo_styled.columns:
                    df_resumo_styled["DÍVIDA EM MORA / RCL"] = df_resumo_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: converter_e_formatar(x, 'percentual'))

                st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
                st.markdown("---")

                # --- Seção 3: Detalhes Técnicos (Abas) ---
                st.header("🔎 Análise Detalhada de Índices e Aportes")
                
                tab1, tab2 = st.tabs(["📊 Índices Fiscais e RCL", "⚖️ Aportes Detalhados por Tribunal"])
                
                with tab1:
                    st.subheader("RCL e Percentuais por Tribunal")
                    colunas_indices = ["ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_indices = df_filtrado_exibicao.set_index('ENTE').loc[df_resumo_float['ENTE']].reset_index()
                    df_indices_styled = df_indices[[col for col in colunas_indices if col in df_indices.columns]].copy()
                    
                    if "RCL 2024" in df_indices_styled.columns:
                        df_indices_styled["RCL 2024"] = df_indices_styled["RCL 2024"].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    
                    for col in ["DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'percentual'))
                        
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("Valores Aportados por Tribunal")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes = df_filtrado_exibicao.set_index('ENTE').loc[df_resumo_float['ENTE']].reset_index()
                    df_aportes_styled = df_aportes[[col for col in colunas_aportes if col in df_aportes.columns]].copy()
                    
                    for col in ["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]:
                        if col in df_aportes_styled.columns:
                             df_aportes_styled[col] = df_aportes_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado durante o processamento. Verifique se o formato do seu CSV está correto (separador ';'). Detalhes: {e}")

else:
    # Mensagem quando o arquivo não está carregado
    st.info("ℹ️ Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do painel de controle.")

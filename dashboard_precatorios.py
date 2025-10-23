import streamlit as st
import pandas as pd
import numpy as np 
from typing import Union
import os 

# ----------------------------------------------------
# CONFIGURAÇÃO DO ARQUIVO FIXO (MANTENHA ESTE NOME NO SEU DIRETÓRIO)
# ----------------------------------------------------
# ⚠️ GARANTA que o arquivo 'Painel Entes.csv' esteja no MESMO DIRETÓRIO do script.
FILE_PATH = "Painel Entes.csv"
COLUNA_PARCELA_ANUAL = "PARCELA ANUAL"
COLUNAS_CRITICAS = ["ENTE", "STATUS", COLUNA_PARCELA_ANUAL, "APORTES"]


# --- Configuração da página ---
st.set_page_config(
    page_title="💰 Painel de Precatórios: Foco e Detalhe",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO E CONVERSÃO (Mantida)
# ----------------------------------------------------
def converter_e_formatar(valor: Union[str, float, int, None], formato: str):
    """
    Formata um valor (string BR ou float) para o padrão monetário/percentual brasileiro.
    """
    if pd.isna(valor) or valor is None or valor == "":
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
st.markdown("<h1 style='color: #00BFFF;'>💰 Visão Geral Financeira de Precatórios</h1>", unsafe_allow_html=True)
st.caption("Organização Foco e Detalhe por Ente Devedor")
st.markdown("---") 

# ----------------------------------------------------
# Processamento Condicional - LENDO DIRETAMENTE DO DISCO
# ----------------------------------------------------

# Verifica se o arquivo existe antes de tentar ler
if not os.path.exists(FILE_PATH):
    st.error(f"❌ Erro: O arquivo de dados '{FILE_PATH}' não foi encontrado.")
    st.info("Para que este código funcione, garanta que o arquivo CSV (`Painel Entes.csv`) esteja no mesmo diretório do script.")
else:
    with st.spinner('⏳ Carregando e processando os indicadores...'):
        try:
            # 1. Lendo o CSV: Usando ENCODING='latin1' para maior compatibilidade com arquivos BR
            df = pd.read_csv(FILE_PATH, delimiter=";", encoding='latin1', header=0)
            
            # --- CORREÇÃO CRÍTICA 1: Remove o caractere BOM (Byte Order Mark - \ufeff ou ï»¿) ---
            df.columns = df.columns.str.replace('\ufeff', '', regex=False)
            
            # --- CORREÇÃO CRÍTICA 2: Remove espaços em branco do início/fim dos nomes das colunas ---
            df.columns = df.columns.str.strip()

            # --- CORREÇÃO CRÍTICA 3: Força a correção de nomes de colunas que vieram com erro de codificação (DÃVIDA) ---
            # O nome da coluna pode ter sido lido de forma diferente, então corrigimos o alvo.
            df.columns = df.columns.str.replace('DÃVIDA EM MORA / RCL', 'DÍVIDA EM MORA / RCL', regex=False)
            
            
            # --- VERIFICAÇÃO CRÍTICA MÍNIMA ---
            
            if not all(col in df.columns for col in COLUNAS_CRITICAS):
                 # Se alguma coluna crítica não existir, exibe o erro e a lista de colunas.
                 st.error(f"❌ Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(COLUNAS_CRITICAS)}. Verifique a ortografia exata dos cabeçalhos.")
                 st.info(f"Colunas disponíveis no arquivo (após correção de BOM/espaços): {', '.join(df.columns.tolist())}")
                 st.stop()
            
            # --- REMOVER A ÚLTIMA LINHA (TOTALIZAÇÃO) ---
            df = df.iloc[:-1].copy()
            
            # --- Conversão para DataFrame de TRABALHO (df_float) ---
            
            colunas_para_float = [
                "ENDIVIDAMENTO TOTAL", COLUNA_PARCELA_ANUAL, "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]
            
            colunas_para_float = list(set([col for col in colunas_para_float if col in df.columns]))

            df_float = df.copy()
            
            # Aplica a limpeza e conversão de formato BR para float em todas as colunas numéricas
            for col in colunas_para_float:
                if col in df_float.columns:
                    str_series = df_float[col].astype(str).str.strip().str.replace('R$', '').str.replace('(', '').str.replace(')', '').str.replace('%', '').str.strip()
                    try:
                        str_limpa = str_series.str.replace('.', 'TEMP', regex=False).str.replace(',', '.', regex=False).str.replace('TEMP', '', regex=False)
                    except TypeError:
                        str_limpa = str_series.str.replace('.', 'TEMP').str.replace(',', '.').str.replace('TEMP', '')
                    
                    df_float[col] = pd.to_numeric(str_limpa, errors='coerce')

                 
            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros (na Sidebar) ---
            with st.sidebar:
                st.header("⚙️ Filtros Analíticos")
                
                status_lista_limpa = df["STATUS"].dropna().unique().tolist()
                status_lista = [s for s in status_lista_limpa if s.lower() != 'nan' and s is not np.nan]
                entes_lista = df["ENTE"].unique().tolist()
                
                selected_ente = st.selectbox("👤 Ente Devedor:", options=["Todos"] + sorted(entes_lista))
                selected_status = st.selectbox("🚦 Status da Dívida:", options=["Todos"] + sorted(status_lista))
            
            # 4. Aplicação dos filtros no DataFrame original e no de cálculo
            filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            
            df_filtrado_exibicao = df[filtro_status & filtro_entes]
            df_filtrado_calculo = df_float[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # INÍCIO DO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado_exibicao.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (4 KPIs) ---
                st.header("📈 Indicadores Consolidado (Total)")
                
                total_parcela_anual = df_filtrado_calculo[COLUNA_PARCELA_ANUAL].sum()
                total_aportes = df_filtrado_calculo["APORTES"].sum()
                saldo_a_pagar = df_filtrado_calculo["SALDO A PAGAR"].sum()
                num_entes = df_filtrado_calculo["ENTE"].nunique()

                col_entes, col_parcela_anual, col_aportes, col_saldo = st.columns(4)
                
                with col_entes:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col_parcela_anual:
                    st.metric(label=f"Parcela Anual (R$)", value=converter_e_formatar(total_parcela_anual, 'moeda'))
                with col_aportes:
                    st.metric(label="Total de Aportes (R$)", value=converter_e_formatar(total_aportes, 'moeda'))
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=converter_e_formatar(saldo_a_pagar, 'moeda'))
                
                st.markdown("---") 

                # --- Seção 2: Tabela Principal (Resumo de Foco) ---
                st.header("📋 Resumo da Situação por Ente")
                
                colunas_resumo = [
                    "ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                # Certifique-se de que a coluna "ENDIVIDAMENTO TOTAL" existe antes de ordenar
                if "ENDIVIDAMENTO TOTAL" in df_filtrado_calculo.columns:
                    df_resumo_float = df_filtrado_calculo.sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                else:
                    df_resumo_float = df_filtrado_calculo # Não ordena se não tiver a coluna

                
                df_resumo = df_filtrado_exibicao.set_index('ENTE').loc[df_resumo_float['ENTE']].reset_index()
                df_resumo_styled = df_resumo[[col for col in colunas_resumo if col in df_resumo.columns]].copy()
                
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
                    colunas_indices = ["ENTE", "RCL 2024", COLUNA_PARCELA_ANUAL, "DÍVIDA EM MORA / RCL", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_indices = df_filtrado_exibicao.set_index('ENTE').loc[df_resumo_float['ENTE']].reset_index()
                    df_indices_styled = df_indices[[col for col in colunas_indices if col in df_indices.columns]].copy()
                    
                    for col in ["RCL 2024", COLUNA_PARCELA_ANUAL]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    
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

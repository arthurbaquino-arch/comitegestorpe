import streamlit as st
import pandas as pd
import numpy as np 
from typing import Union
import os 

# ----------------------------------------------------
# CONFIGURAÇÃO DO ARQUIVO FIXO
# ----------------------------------------------------
FILE_PATH = "Painel Entes.csv"
COLUNA_PARCELA_ANUAL = "PARCELA ANUAL"

# Colunas críticas esperadas no formato limpo
COLUNAS_CRITICAS = ["ENTE", "STATUS", COLUNA_PARCELA_ANUAL, "APORTES", "DÍVIDA EM MORA / RCL"]


# --- Configuração da página ---
st.set_page_config(
    page_title="💰 Painel de Precatórios: Foco e Detalhe",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# FUNÇÃO ROBUSTA DE LEITURA (PRESERVAÇÃO DO ARQUIVO)
# ----------------------------------------------------
def read_csv_robustly(file_path):
    """Tenta ler o CSV usando múltiplos encodings e limpa cabeçalhos."""
    encodings = ['utf-8', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            # Tentar ler com o encoding atual. 
            # Não usaremos decimal/thousands aqui, pois o símbolo '%' no dado original 
            # confunde o Pandas. Faremos a conversão manual no loop abaixo.
            df = pd.read_csv(file_path, sep=";", encoding=encoding, header=0, na_values=['#N/D', '#VALOR!', '-'])
            
            # Limpeza e Renomeação Agressiva dos cabeçalhos
            col_map = {}
            for col in df.columns:
                stripped_col = col.strip()
                
                # 1. Remove o caractere BOM (\ufeff) e ï»¿
                if stripped_col.startswith('\ufeff'):
                    stripped_col = stripped_col.lstrip('\ufeff').strip()
                if stripped_col.startswith('ï»¿'):
                    stripped_col = stripped_col.lstrip('ï»¿').strip()

                # 2. Corrige a codificação conhecida (DÃVIDA -> DÍVIDA)
                if 'DÃVIDA EM MORA / RCL' in stripped_col:
                    stripped_col = 'DÍVIDA EM MORA / RCL'

                col_map[col] = stripped_col
            
            df.rename(columns=col_map, inplace=True)
            return df
            
        except Exception:
            # Se falhar, tenta o próximo encoding
            continue
    
    # Se todas as tentativas falharem
    raise Exception("Erro de Codificação Incurável.")


# ----------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO E CONVERSÃO (CORRIGIDA)
# ----------------------------------------------------
def converter_e_formatar(valor: Union[str, float, int, None], formato: str):
    """
    Formata um valor (float ou string) para o padrão monetário/percentual brasileiro.
    """
    # Se o valor for NaN ou None, retorna "-"
    if pd.isna(valor) or valor is None:
        return "-"
    
    num_valor = None
    
    if isinstance(valor, (float, int, np.number)):
        num_valor = float(valor)
    else:
        # Lógica de conversão de strings (se o Pandas não conseguiu na leitura)
        str_valor = str(valor).strip()
        
        # Remove símbolos de moeda, parênteses e %
        str_limpa = str_valor.replace('R$', '').replace('(', '').replace(')', '').replace('%', '').strip()

        try:
            # Converte formato BR (ponto milhar, vírgula decimal) para Float (ponto decimal)
            # Regex=False para compatibilidade
            str_float = str_limpa.replace('.', 'TEMP', regex=False).replace(',', '.', regex=False).replace('TEMP', '', regex=False)
            num_valor = float(str_float)
        except Exception:
            return "-" # Retorna '-' se não for conversível
            
    # CRITICAL FIX: Remover esta verificação permite exibir 0.00%
    # if abs(num_valor) < 0.01 and formato != 'percentual': 
    #      return "-"
         
    try:
        # Formatação final para exibição
        if formato == 'moeda':
            # Verifica se é zero, e se for, retorna "-" (regra de negócio para moeda)
            if num_valor == 0:
                return "-"
            return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        elif formato == 'percentual':
            # Formata o percentual. Se for zero, aparecerá 0,00%
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
# Processamento
# ----------------------------------------------------

# Verifica se o arquivo existe antes de tentar ler
if not os.path.exists(FILE_PATH):
    st.error(f"❌ Erro: O arquivo de dados '{FILE_PATH}' não foi encontrado.")
    st.info("Para que este código funcione, garanta que o arquivo CSV (`Painel Entes.csv`) esteja no mesmo diretório do script.")
else:
    with st.spinner('⏳ Carregando e processando os indicadores...'):
        try:
            # 1. Leitura do arquivo usando a função robusta
            df = read_csv_robustly(FILE_PATH)
            
            # --- VERIFICAÇÃO CRÍTICA MÍNIMA ---
            
            if not all(col in df.columns for col in COLUNAS_CRITICAS):
                 st.error(f"❌ Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(COLUNAS_CRITICAS)}. Verifique a ortografia exata dos cabeçalhos.")
                 st.info(f"Colunas disponíveis no arquivo (após limpeza): {', '.join(df.columns.tolist())}")
                 st.stop()
            
            # --- REMOVER A ÚLTIMA LINHA (TOTALIZAÇÃO) ---
            # Assume que a última linha é uma totalização
            df = df.iloc[:-1].copy()
            
            # --- Conversão para DataFrame de TRABALHO (df_float) ---
            df_float = df.copy() 
            
            # Garante que as colunas críticas de cálculo sejam numéricas
            colunas_para_float_final = [
                "ENDIVIDAMENTO TOTAL", COLUNA_PARCELA_ANUAL, "APORTES", "RCL 2024", 
                "DÍVIDA EM MORA / RCL", "% APLICADO", # Adicionado % APLICADO aqui
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]
            
            colunas_para_float_final = list(set([col for col in colunas_para_float_final if col in df_float.columns]))

            # Aplica conversão forçada de string para float para todas as colunas numéricas
            for col in colunas_para_float_final:
                 # Usa a mesma lógica de limpeza da função converter_e_formatar, mas em massa
                 str_series = df_float[col].astype(str).str.strip().str.replace('R$', '', regex=False).str.replace('(', '', regex=False).str.replace(')', '', regex=False).str.replace('%', '', regex=False).str.strip()
                 
                 # Converte formato BR (ponto milhar, vírgula decimal) para Float (ponto decimal)
                 str_limpa = str_series.str.replace('.', 'TEMP', regex=False).str.replace(',', '.', regex=False).str.replace('TEMP', '', regex=False)
                 
                 df_float[col] = pd.to_numeric(str_limpa, errors='coerce')


            # Garante que as colunas de ENTE e STATUS sejam strings
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
            
            # 4. Aplicação dos filtros
            filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            
            # Filtra o dataframe float (para cálculos e exibição de dados formatados)
            df_filtrado_calculo = df_float[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # INÍCIO DO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado_calculo.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                # --- Seção 1: Indicadores Chave (4 KPIs) ---
                st.header("📈 Indicadores Consolidado (Total)")
                
                # Calcula os totais do dataframe FLOAT
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
                
                if "ENDIVIDAMENTO TOTAL" in df_filtrado_calculo.columns:
                    # Ordena pelo DF de cálculo (float)
                    df_exibicao_final = df_filtrado_calculo.sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                else:
                    df_exibicao_final = df_filtrado_calculo 

                
                # Cria a tabela de exibição final, puxando os floats e formatando
                df_resumo_styled = df_exibicao_final[[col for col in colunas_resumo if col in df_exibicao_final.columns]].copy()
                
                for col in ["ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR"]:
                    if col in df_resumo_styled.columns:
                        # Aplica a formatação em cada linha
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
                    # Incluído o % APLICADO aqui
                    colunas_indices = ["ENTE", "RCL 2024", COLUNA_PARCELA_ANUAL, "DÍVIDA EM MORA / RCL", "% APLICADO", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_indices_styled = df_exibicao_final[[col for col in colunas_indices if col in df_exibicao_final.columns]].copy()
                    
                    for col in ["RCL 2024", COLUNA_PARCELA_ANUAL]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    
                    for col in ["DÍVIDA EM MORA / RCL", "% APLICADO", "% TJPE", "% TRF5", "% TRT6"]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'percentual'))
                        
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2:
                    st.subheader("Valores Aportados por Tribunal")
                    colunas_aportes = ["ENTE", "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]
                    
                    df_aportes_styled = df_exibicao_final[[col for col in colunas_aportes if col in df_exibicao_final.columns]].copy()
                    
                    for col in ["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"]:
                        if col in df_aportes_styled.columns:
                             df_aportes_styled[col] = df_aportes_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado durante o processamento. Detalhes: {e}")
            st.warning("O problema de leitura persiste. Por favor, verifique se seu arquivo CSV: 1. Usa o ponto e vírgula (`;`) como separador. 2. A última linha de Totalização foi removida. 3. Não possui quebras de linha no meio de células de texto.")

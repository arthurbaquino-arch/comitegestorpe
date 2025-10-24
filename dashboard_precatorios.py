import streamlit as st
import pandas as pd
import numpy as np 
from typing import Union
import os 
import altair as alt # Importado para o gráfico Meta vs Realizado

# ----------------------------------------------------
# CONFIGURAÇÃO DO ARQUIVO FIXO
# ----------------------------------------------------
FILE_PATH = "Painel Entes.csv"
COLUNA_PARCELA_ANUAL = "PARCELA ANUAL"
COLUNA_APORTES = "APORTES" 

# Colunas críticas esperadas no formato limpo
COLUNAS_CRITICAS = ["ENTE", "STATUS", COLUNA_PARCELA_ANUAL, COLUNA_APORTES, "DÍVIDA EM MORA / RCL"]


# --- Configuração da página ---
st.set_page_config(
    page_title="💰 Situação dos Entes Devedores",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# FUNÇÃO ROBUSTA DE LEITURA 
# ----------------------------------------------------
def read_csv_robustly(file_path):
    """Tenta ler o CSV usando múltiplos encodings e limpa cabeçalhos."""
    encodings = ['utf-8', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, sep=";", encoding=encoding, header=0, na_values=['#N/D', '#VALOR!', '-'])
            
            col_map = {}
            for col in df.columns:
                stripped_col = col.strip()
                if stripped_col.startswith('\ufeff'):
                    stripped_col = stripped_col.lstrip('\ufeff').strip()
                if stripped_col.startswith('ï»¿'):
                    stripped_col = stripped_col.lstrip('ï»¿').strip()
                if 'DÃVIDA EM MORA / RCL' in stripped_col:
                    stripped_col = 'DÍVIDA EM MORA / RCL'
                
                col_map[col] = stripped_col.strip()
            
            df.rename(columns=col_map, inplace=True)
            return df
            
        except Exception:
            continue
    
    raise Exception("Erro de Codificação Incurável na leitura do CSV.")


# ----------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO E CONVERSÃO
# ----------------------------------------------------
def converter_e_formatar(valor: Union[str, float, int, None], formato: str, delta=False):
    """
    Formata um valor (float ou string) para o padrão monetário/percentual brasileiro.
    """
    if pd.isna(valor) or valor is None:
        return "-"
    
    num_valor = None
    
    if isinstance(valor, (float, int, np.number)):
        num_valor = float(valor)
    else:
        str_valor = str(valor).strip()
        str_limpa = str_valor.replace('R$', '').replace('(', '').replace(')', '').replace('%', '').strip()

        try:
            str_float = str_limpa.replace('.', 'TEMP', regex=False).replace(',', '.', regex=False).replace('TEMP', '', regex=False)
            num_valor = float(str_float)
        except Exception:
            return "-" 
            
    try:
        if formato == 'moeda':
            if not delta and (num_valor == 0 or abs(num_valor) < 0.01):
                return "-"
            return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        elif formato == 'percentual':
            return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        else:
            return str(num_valor)
            
    except Exception:
        return "-"

# ----------------------------------------------------
# FUNÇÃO DE ESTILIZAÇÃO DO PANDAS (NOVA)
# ----------------------------------------------------
def highlight_status(val):
    """
    Destaca a célula STATUS na tabela de resumo.
    """
    val_upper = str(val).upper().strip()
    if 'ADIMPLENTE' in val_upper:
        # Cor de fundo suave (Verde) e texto escuro
        return 'background-color: #E6F7E6; color: #1E8449; font-weight: bold;'
    elif 'INADIMPLENTE' in val_upper:
        # Cor de fundo suave (Laranja/Vermelho) e texto escuro
        return 'background-color: #FEEEEE; color: #C0392B; font-weight: bold;'
    return '' # Estilo padrão

# ----------------------------------------------------
# TÍTULOS E LAYOUT INICIAL (MELHORADO)
# ----------------------------------------------------
st.markdown("<h1 style='color: #00BFFF;'>💰 Situação dos Entes Devedores no Contexto da EC 136/2025</h1>", unsafe_allow_html=True)
st.markdown("<h3>Comitê Gestor</h3>", unsafe_allow_html=True)
st.markdown("TJPE - TRF5 - TRT6")
st.divider() # <--- IMPLEMENTAÇÃO 1: DIVIDER

# ----------------------------------------------------
# Processamento
# ----------------------------------------------------

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
                 st.error(f"❌ Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(COLUNAS_CRITICAS)}. Colunas encontradas: {', '.join(df.columns.tolist())}")
                 st.stop()
            
            # --- REMOVER A ÚLTIMA LINHA (TOTALIZAÇÃO) ---
            df = df.iloc[:-1].copy()
            
            # --- Conversão para DataFrame de TRABALHO (df_float) ---
            df_float = df.copy() 
            
            colunas_para_float_final = [
                "ENDIVIDAMENTO TOTAL", COLUNA_PARCELA_ANUAL, COLUNA_APORTES, "RCL 2024", 
                "DÍVIDA EM MORA / RCL", "% APLICADO", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]",
                "ENDIVIDAMENTO TOTAL - [TJPE]", "ENDIVIDAMENTO TOTAL - [TRF5]", "ENDIVIDAMENTO TOTAL - [TRT6]"
            ]
            
            colunas_para_float_final = list(set([col for col in colunas_para_float_final if col in df_float.columns]))

            for col in colunas_para_float_final:
                 str_series = df_float[col].astype(str).str.strip().str.replace('R$', '', regex=False).str.replace('(', '', regex=False).str.replace(')', '', regex=False).str.replace('%', '', regex=False).str.strip()
                 str_limpa = str_series.str.replace('.', 'TEMP', regex=False).str.replace(',', '.', regex=False).str.replace('TEMP', '', regex=False)
                 df_float[col] = pd.to_numeric(str_limpa, errors='coerce')


            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros (na Sidebar) ---
            with st.sidebar:
                # <--- IMPLEMENTAÇÃO 3: LOGO/IMAGEM PLACEHOLDER
                st.markdown("### Logo Comitê Gestor/EC 136")
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
            
            df_filtrado_calculo = df_float[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # INÍCIO DO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado_calculo.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
            else:
                
                if "ENDIVIDAMENTO TOTAL" in df_filtrado_calculo.columns:
                    df_exibicao_final = df_filtrado_calculo.sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False)
                else:
                    df_exibicao_final = df_filtrado_calculo 

                # --- Seção 1: Indicadores Chave (4 KPIs com Delta) ---
                st.header("📈 Indicadores Consolidado (Total)")
                
                total_parcela_anual = df_filtrado_calculo[COLUNA_PARCELA_ANUAL].sum()
                total_aportes = df_filtrado_calculo[COLUNA_APORTES].sum()
                saldo_a_pagar = df_filtrado_calculo["SALDO A PAGAR"].sum()
                num_entes = df_filtrado_calculo["ENTE"].nunique()

                delta_aportes = total_aportes - total_parcela_anual
                
                col_entes, col_parcela_anual, col_aportes, col_saldo = st.columns(4)
                
                with col_entes:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col_parcela_anual:
                    st.metric(label=f"Parcela Anual (R$)", value=converter_e_formatar(total_parcela_anual, 'moeda'))
                with col_aportes:
                    st.metric(
                        label="Total de Aportes (R$)", 
                        value=converter_e_formatar(total_aportes, 'moeda'),
                        delta=converter_e_formatar(delta_aportes, 'moeda', delta=True),
                        delta_color='normal' if delta_aportes >= 0 else 'inverse'
                    )
                with col_saldo:
                    st.metric(label="Saldo Remanescente a Pagar (R$)", value=converter_e_formatar(saldo_a_pagar, 'moeda'))
                
                st.divider()

                # --- Seção 2: Tabela Principal (Resumo de Foco) ---
                st.header("📋 Resumo da Situação por Ente")
                
                colunas_resumo = [
                    "ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR",
                    "DÍVIDA EM MORA / RCL"
                ]
                
                # Cria o DF de exibição a partir do df_exibicao_final
                df_resumo_raw = df_exibicao_final[[col for col in colunas_resumo if col in df_exibicao_final.columns]].copy()
                
                # Cria a cópia do DF com formatação de moeda/percentual (para estilizar)
                df_resumo_styled = df_resumo_raw.copy()

                for col in ["ENDIVIDAMENTO TOTAL", "APORTES", "SALDO A PAGAR"]:
                    if col in df_resumo_styled.columns:
                        df_resumo_styled[col] = df_resumo_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                        
                if "DÍVIDA EM MORA / RCL" in df_resumo_styled.columns:
                    df_resumo_styled["DÍVIDA EM MORA / RCL"] = df_resumo_styled["DÍVIDA EM MORA / RCL"].apply(lambda x: converter_e_formatar(x, 'percentual'))

                # <--- IMPLEMENTAÇÃO 2: PANDAS STYLER
                if "STATUS" in df_resumo_styled.columns:
                    st.dataframe(
                        df_resumo_styled.style.applymap(
                            highlight_status, 
                            subset=pd.IndexSlice[:, ['STATUS']]
                        ), 
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.dataframe(df_resumo_styled, use_container_width=True, hide_index=True)
                
                st.divider()

                # --- Seção 3: Detalhes Técnicos (Quatro Abas) ---
                st.header("🔎 Análise Detalhada de Índices e Aportes")
                
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 Índices Fiscais e RCL", 
                    "📈 Aportes Detalhados",
                    "⚖️ Rateio por Tribunal",
                    "💰 Composição da Dívida"
                ])
                
                with tab1:
                    st.subheader("RCL e Parcela Anual")
                    
                    colunas_indices = [
                        "ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", COLUNA_PARCELA_ANUAL
                    ]
                    
                    df_indices_styled = df_exibicao_final[[col for col in colunas_indices if col in df_exibicao_final.columns]].copy()
                    
                    for col in ["RCL 2024", COLUNA_PARCELA_ANUAL]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    
                    for col in ["DÍVIDA EM MORA / RCL", "% APLICADO"]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'percentual'))
                        
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2: # ABA APORTES DETALHADOS (Com Gráfico Meta vs. Realizado)
                    st.subheader("Comparativo: Meta (Parcela Anual) vs. Realizado (Aportes)")
                    
                    # <--- IMPLEMENTAÇÃO 4: GRÁFICO META VS. REALIZADO
                    df_chart = df_filtrado_calculo[["ENTE", COLUNA_PARCELA_ANUAL, COLUNA_APORTES]].copy()
                    
                    # Derretendo (melt) o DataFrame para o formato longo que o Altair espera
                    df_chart_melted = df_chart.melt(
                        id_vars='ENTE',
                        value_vars=[COLUNA_PARCELA_ANUAL, COLUNA_APORTES],
                        var_name='Tipo',
                        value_name='Valor'
                    )

                    # Gráfico de Barras Empilhadas (ou lado a lado)
                    chart = alt.Chart(df_chart_melted).mark_bar().encode(
                        # Para melhor visualização, só mostramos o gráfico se houver mais de um ente
                        x=alt.X('ENTE', sort='-y', title="Ente Devedor"),
                        y=alt.Y('Valor', title="Valor (R$)"),
                        color='Tipo',
                        tooltip=['ENTE', 'Tipo', alt.Tooltip('Valor', format='$,.2f')]
                    ).properties(
                        height=400
                    ).interactive() # Permite zoom e pan

                    if num_entes > 0:
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.info("O gráfico 'Meta vs. Realizado' será exibido aqui ao selecionar um ou mais Entes Devedores.")

                    st.markdown("---")
                    st.subheader("Valores Aportados por Tribunal")
                    
                    colunas_aportes_original = [
                        "ENTE", 
                        "APORTES - [TJPE]", 
                        "APORTES - [TRF5]", 
                        "APORTES - [TRT6]",
                        COLUNA_APORTES # Total
                    ]
                    
                    colunas_renomeadas_aportes = {
                        "APORTES - [TJPE]": "TJPE", 
                        "APORTES - [TRF5]": "TRF5", 
                        "APORTES - [TRT6]": "TRT6",
                        COLUNA_APORTES: "TOTAL"
                    }
                    
                    df_aportes_styled = df_exibicao_final[[col for col in colunas_aportes_original if col in df_exibicao_final.columns]].copy()
                    df_aportes_styled.rename(columns=colunas_renomeadas_aportes, inplace=True)
                    
                    colunas_moeda_aportes = ["TJPE", "TRF5", "TRT6", "TOTAL"]
                    
                    for col in colunas_moeda_aportes:
                        if col in df_aportes_styled.columns:
                             df_aportes_styled[col] = df_aportes_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
                with tab3:
                    st.subheader("Percentuais de Rateio por Tribunal")
                    
                    colunas_rateio = ["ENTE", "% TJPE", "% TRF5", "% TRT6"]
                    
                    df_rateio_styled = df_exibicao_final[[col for col in colunas_rateio if col in df_exibicao_final.columns]].copy()
                    
                    for col in ["% TJPE", "% TRF5", "% TRT6"]:
                        if col in df_rateio_styled.columns:
                            df_rateio_styled[col] = df_rateio_styled[col].apply(lambda x: converter_e_formatar(x, 'percentual'))
                        
                    st.dataframe(df_rateio_styled, use_container_width=True, hide_index=True)

                with tab4: 
                    st.subheader("Endividamento Total por Tribunal")
                    
                    colunas_divida_original = [
                        "ENTE", 
                        "ENDIVIDAMENTO TOTAL - [TJPE]", 
                        "ENDIVIDAMENTO TOTAL - [TRF5]", 
                        "ENDIVIDAMENTO TOTAL - [TRT6]", 
                        "ENDIVIDAMENTO TOTAL"
                    ]
                    
                    colunas_renomeadas_divida = {
                        "ENDIVIDAMENTO TOTAL - [TJPE]": "TJPE", 
                        "ENDIVIDAMENTO TOTAL - [TRF5]": "TRF5", 
                        "ENDIVIDAMENTO TOTAL - [TRT6]": "TRT6", 
                        "ENDIVIDAMENTO TOTAL": "TOTAL"
                    }
                    
                    df_divida_styled = df_exibicao_final[[col for col in colunas_divida_original if col in df_exibicao_final.columns]].copy()
                    df_divida_styled.rename(columns=colunas_renomeadas_divida, inplace=True)
                    
                    colunas_moeda_divida = ["TJPE", "TRF5", "TRT6", "TOTAL"]

                    for col in colunas_moeda_divida:
                        if col in df_divida_styled.columns:
                             df_divida_styled[col] = df_divida_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))

                    st.dataframe(df_divida_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            st.error(f"❌ Ocorreu um erro inesperado durante o processamento. Detalhes: {e}")
            st.warning("Verifique se o seu CSV possui problemas de formatação que impedem a leitura robusta, como quebras de linha ou caracteres ilegais.")

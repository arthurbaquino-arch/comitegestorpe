import streamlit as st
import pandas as pd
import numpy as np 
from typing import Union
import os 
import unicodedata 

# ----------------------------------------------------
# CONFIGURAÇÃO DO ARQUIVO FIXO E MAPEAMENTO DE NOMES
# ----------------------------------------------------
FILE_PATH = "Painel Entes.csv"

# Nomes Internos (Baseados nos nomes exatos da planilha mais recente)
COLUNA_PARCELA_ANUAL_INTERNO = "TOTAL A SER APORTADO"
COLUNA_APORTES_INTERNO = "VALOR APORTADO"
COLUNA_SALDO_A_PAGAR_INTERNO = "SALDO REMANESCENTE A APORTAR"

# Nomes de Colunas de Aportes Detalhados por Tribunal 
COLUNA_APORTES_TJPE_INTERNO = "APORTES - [TJPE]"
COLUNA_APORTES_TRF5_INTERNO = "APORTES - [TRF5]"
COLUNA_APORTES_TRT6_INTERNO = "APORTES - [TRT6]"

# Nomes de Colunas de Rateio Percentual 
COLUNA_PERCENTUAL_TJPE_INTERNO = "TJPE (%)"
COLUNA_PERCENTUAL_TRF5_INTERNO = "TRF5 (%)"
COLUNA_PERCENTUAL_TRT6_INTERNO = "TRT6 (%)"

# COLUNAS SOLICITADAS PARA A NOVA SEÇÃO DE KPI
COLUNA_TJPE_SIMPLES_INTERNO = "TJPE"
COLUNA_TRF5_SIMPLES_INTERNO = "TRF5"
COLUNA_TRT6_SIMPLES_INTERNO = "TRT6"
COLUNA_TJPE_RS_INTERNO = "TJPE (R$)"
COLUNA_TRF5_RS_INTERNO = "TRF5 (R$)"
COLUNA_TRT6_RS_INTERNO = "TRT6 (R$)"


# Nomes de Display (Para manter o visual anterior consistente)
COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY = "ENDIVIDAMENTO TOTAL EM JAN/2025" 
COLUNA_PARCELA_ANUAL_DISPLAY = "Total a Ser Aportado (R$)" # Display para TOTAL A SER APORTADO
COLUNA_APORTES_DISPLAY = "Valor Aportado (R$)" # Display para VALOR APORTADO
COLUNA_SALDO_A_PAGAR_DISPLAY = "Saldo Remanescente a Aportar (R$)" # Display para SALDO REMANESCENTE A APORTAR


# Colunas críticas esperadas no formato limpo
COLUNAS_CRITICAS = ["ENTE", "STATUS", COLUNA_PARCELA_ANUAL_INTERNO, COLUNA_APORTES_INTERNO, "DÍVIDA EM MORA / RCL"]


# --- Configuração da página ---
st.set_page_config(
    page_title="💰 Situação dos Entes Devedores",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# FUNÇÃO DE ORDENAÇÃO SEM ACENTOS
# ----------------------------------------------------
def sort_key_without_accents(text):
    """Normaliza e converte para minúsculas, removendo acentos para ordenação alfabética correta."""
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8').lower()

# ----------------------------------------------------
# FUNÇÃO ROBUSTA DE LEITURA (PRESERVAÇÃO DO ARQUIVO)
# ----------------------------------------------------
def read_csv_robustly(file_path):
    """Tenta ler o CSV usando múltiplos encodings e limpa cabeçalhos."""
    encodings = ['utf-8', 'latin1', 'cp1252']
    
    for encoding in encodings:
        try:
            # Tentar ler com o encoding atual. 
            # A planilha usa o separador ";" e deve estar em latin1
            df = pd.read_csv(file_path, sep=";", encoding=encoding, header=0, na_values=['#N/D', '#VALOR!', '-', ' -   '])
            
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
                
                # 3. Garante que os nomes finais não tenham espaços desnecessários
                col_map[col] = stripped_col.strip()
            
            df.rename(columns=col_map, inplace=True)
            return df
            
        except Exception:
            # Se falhar, tenta o próximo encoding
            continue
    
    # Se todas as tentativas falharem
    raise Exception("Erro de Codificação Incurável na leitura do CSV.")


# ----------------------------------------------------
# FUNÇÃO DE FORMATAÇÃO E CONVERSÃO
# ----------------------------------------------------
def converter_e_formatar(valor: Union[str, float, int, None], formato: str):
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
        str_limpa = str_valor.replace('R$', '', regex=False).replace('(', '', regex=False).replace(')', '', regex=False).replace('%', '', regex=False).strip()

        try:
            # Conversão robusta de formato brasileiro para float
            str_float = str_limpa.replace('.', 'TEMP', regex=False).replace(',', '.', regex=False).replace('TEMP', '', regex=False)
            num_valor = float(str_float)
        except Exception:
            return "-" 
            
    try:
        if formato == 'moeda':
            if num_valor == 0 or abs(num_valor) < 0.01:
                return "-"
            # Formatação monetária (ponto como milhar, vírgula como decimal)
            return f"R$ {num_valor:,.2f}".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        elif formato == 'percentual':
            # Formatação percentual
            return f"{num_valor:,.2f}%".replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        
        else:
            return str(num_valor)
            
    except Exception:
        return "-"


# ----------------------------------------------------
# TÍTULOS E LAYOUT INICIAL
# ----------------------------------------------------
# TÍTULO PRINCIPAL (H1, com a cor AZUL MARINHO #000080)
st.markdown("<h1 style='color: #000080;'>Comitê Gestor de Precatórios - PE</h1>", unsafe_allow_html=True)
# SUBTÍTULO (Usando H3 com a mesma cor do H1 e ajuste de margem)
st.markdown("<h3 style='color: #000080; margin-top: -15px;'>TJPE - TRF5 - TRT6</h3>", unsafe_allow_html=True) 
# TÍTULO SECUNDÁRIO (H2)
st.markdown("<h2>💰 Painel de Rateio - 2025</h2>", unsafe_allow_html=True)
st.markdown("---") 

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

            # --- RENOMEAR COLUNAS (PARA MANTER OS NOMES DE EXIBIÇÃO) ---
            rename_map = {
                "ENDIVIDAMENTO TOTAL": COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY,
                "ENDIVIDAMENTO TOTAL - [TJPE]": "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]",
                "ENDIVIDAMENTO TOTAL - [TRF5]": "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]",
                "ENDIVIDAMENTO TOTAL - [TRT6]": "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]",
            }
            # Aplica o rename no df (apenas se as colunas existirem, para não dar erro)
            df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
            
            # --- Conversão para DataFrame de TRABALHO (df_float) ---
            df_float = df.copy() 
            
            # LISTA FINAL DE COLUNAS NUMÉRICAS
            colunas_para_float_final = [
                COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY, COLUNA_PARCELA_ANUAL_INTERNO, COLUNA_APORTES_INTERNO, "RCL 2024", 
                "DÍVIDA EM MORA / RCL", "% APLICADO", 
                COLUNA_SALDO_A_PAGAR_INTERNO, COLUNA_PERCENTUAL_TJPE_INTERNO, COLUNA_PERCENTUAL_TRF5_INTERNO, COLUNA_PERCENTUAL_TRT6_INTERNO,
                # Colunas de Aportes/Endividamento/Rateio R$ por Tribunal
                COLUNA_APORTES_TJPE_INTERNO, COLUNA_APORTES_TRF5_INTERNO, COLUNA_APORTES_TRT6_INTERNO, 
                COLUNA_TJPE_RS_INTERNO, COLUNA_TRF5_RS_INTERNO, COLUNA_TRT6_RS_INTERNO, # R$ 
                COLUNA_TJPE_SIMPLES_INTERNO, COLUNA_TRF5_SIMPLES_INTERNO, COLUNA_TRT6_SIMPLES_INTERNO, # Simples
                "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]", "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]",
                # Colunas de Estoque (Novas colunas para a tab4)
                "ESTOQUE EM MORA - [TJPE]", "ESTOQUE VINCENDOS - [TJPE]",
                "ESTOQUE EM MORA - [TRF5]", "ESTOQUE VINCENDOS - [TRF5]",
                "ESTOQUE EM MORA - [TRT6]", "ESTOQUE VINCENDOS - [TRT6]",
                "ESTOQUE EM MORA", "ESTOQUE VINCENDOS"
            ]
            
            colunas_para_float_final = list(set([col for col in colunas_para_float_final if col in df_float.columns]))

            # Aplica conversão forçada de string para float para todas as colunas numéricas
            for col in colunas_para_float_final:
                 str_series = df_float[col].astype(str).str.strip().str.replace('R$', '', regex=False).str.replace('(', '', regex=False).str.replace(')', '', regex=False).str.replace('%', '', regex=False).str.strip()
                 str_limpa = str_series.str.replace('.', 'TEMP', regex=False).str.replace(',', '.', regex=False).str.replace('TEMP', '', regex=False)
                 df_float[col] = pd.to_numeric(str_limpa, errors='coerce')


            # Garante que as colunas de ENTE e STATUS sejam strings e aplica limpeza
            df["ENTE"] = df["ENTE"].astype(str).str.strip() 
            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros (NO PAINEL PRINCIPAL) ---
            st.header("⚙️ Filtros analíticos") # Formatação solicitada
            
            status_lista_limpa = df["STATUS"].dropna().unique().tolist()
            status_lista = [s for s in status_lista_limpa if s.lower() != 'nan' and s is not np.nan]
            
            # Extrai a lista de entes JÁ LIMPA para a ordenação correta
            entes_lista = df["ENTE"].unique().tolist()
            
            # Cria colunas para os filtros no corpo do app
            col_filtro_ente, col_filtro_status = st.columns(2)
            
            with col_filtro_ente:
                 # APLICAÇÃO DA CHAVE DE ORDENAÇÃO SEM ACENTOS
                selected_ente = st.selectbox("👤 Ente Devedor:", 
                                             options=["Todos"] + sorted(entes_lista, key=sort_key_without_accents))
            
            with col_filtro_status:
                selected_status = st.selectbox("🚦 Status da Dívida:", options=["Todos"] + sorted(status_lista))
            
            st.markdown("---") 

            # 4. Aplicação dos filtros
            filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            
            df_filtrado_calculo = df_float[filtro_status & filtro_entes]
            # Usar o DF original para pegar o STATUS como string, se aplicável
            df_filtrado_string = df[filtro_status & filtro_entes] 
            
            # ----------------------------------------------------
            # INÍCIO DO LAYOUT 1: FOCO E DETALHE
            # ----------------------------------------------------
            
            if df_filtrado_calculo.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros.")
            else:
                
                # Ordena pelo DF de cálculo (float)
                if COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY in df_filtrado_calculo.columns:
                    df_exibicao_final = df_filtrado_calculo.sort_values(by=COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY, ascending=False)
                else:
                    df_exibicao_final = df_filtrado_calculo 

                # --- Seção 1: Indicadores Chave (4 KPIs) ---
                st.header("📈 Dados consolidados dos tribunais: TJPE - TRF5 - TRT6")
                
                # USANDO OS NOMES INTERNOS CORRETOS DA PLANILHA
                total_parcela_anual = df_filtrado_calculo[COLUNA_PARCELA_ANUAL_INTERNO].sum()
                total_aportes = df_filtrado_calculo[COLUNA_APORTES_INTERNO].sum()
                saldo_a_pagar = df_filtrado_calculo[COLUNA_SALDO_A_PAGAR_INTERNO].sum()
                num_entes = df_filtrado_calculo["ENTE"].nunique() 

                # LÓGICA DO KPI "STATUS"
                if selected_ente == "Todos":
                    status_display = "-"
                elif num_entes == 1 and "STATUS" in df_filtrado_string.columns:
                    # Pega o primeiro (e único) status no resultado do filtro
                    status_display = df_filtrado_string["STATUS"].iloc[0]
                else:
                    # Caso inesperado de mais de um ente com filtro de status, retorna "-"
                    status_display = "-"


                # Ajuste para 4 colunas (Removido o KPI "Total de Entes Selecionados")
                col_parcela_anual, col_aportes, col_saldo, col_status = st.columns(4)
                
                with col_parcela_anual:
                    # USANDO O NOME DE DISPLAY
                    st.metric(label=COLUNA_PARCELA_ANUAL_DISPLAY, value=converter_e_formatar(total_parcela_anual, 'moeda'))
                with col_aportes:
                    # USANDO O NOME DE DISPLAY
                    st.metric(label=COLUNA_APORTES_DISPLAY, value=converter_e_formatar(total_aportes, 'moeda'))
                with col_saldo:
                    # USANDO O NOME DE DISPLAY
                    st.metric(label=COLUNA_SALDO_A_PAGAR_DISPLAY, value=converter_e_formatar(saldo_a_pagar, 'moeda'))
                with col_status: # KPI STATUS
                    st.metric(label="Status", value=status_display)
                
                st.markdown("---") 

                # --- NOVA SEÇÃO DE KPI SOLICITADA (USANDO TJPE, TRF5, TRT6) ---
                st.header("➡️ Total a ser aportado para cada tribunal") # Formatação solicitada
                
                # Cálculo das somas dos novos KPIs (USANDO OS NOMES CORRETOS: TJPE, TRF5, TRT6)
                total_tjpe_simples = df_filtrado_calculo[COLUNA_TJPE_SIMPLES_INTERNO].sum()
                total_trf5_simples = df_filtrado_calculo[COLUNA_TRF5_SIMPLES_INTERNO].sum()
                total_trt6_simples = df_filtrado_calculo[COLUNA_TRT6_SIMPLES_INTERNO].sum()

                col_tjpe, col_trf5, col_trt6 = st.columns(3)

                with col_tjpe:
                    st.metric(label="TJPE (R$)", value=converter_e_formatar(total_tjpe_simples, 'moeda'))
                with col_trf5:
                    st.metric(label="TRF5 (R$)", value=converter_e_formatar(total_trf5_simples, 'moeda'))
                with col_trt6:
                    st.metric(label="TRT6 (R$)", value=converter_e_formatar(total_trt6_simples, 'moeda'))
                
                st.markdown("---") 

                # --- Seção 3: Detalhes Técnicos (Quatro Abas) ---
                st.header("🔎 Análise detalhada de índices e aportes") # Formatação solicitada
                
                tab1, tab2, tab3, tab4 = st.tabs([
                    "📊 RCL e Aporte", 
                    "📈 Aportes Detalhados",
                    "⚖️ Rateio por Tribunal",
                    "💰 Composição da Dívida"
                ])
                
                with tab1:
                    st.subheader("RCL e Total a Ser Aportado")
                    
                    # Usando nomes internos para referenciar o DF
                    colunas_indices = [
                        "ENTE", "RCL 2024", "DÍVIDA EM MORA / RCL", "% APLICADO", COLUNA_PARCELA_ANUAL_INTERNO
                    ]
                    
                    df_indices_styled = df_exibicao_final[[col for col in colunas_indices if col in df_exibicao_final.columns]].copy()
                    
                    # Renomeia para o nome de display na tabela
                    df_indices_styled.rename(columns={COLUNA_PARCELA_ANUAL_INTERNO: "TOTAL A SER APORTADO"}, inplace=True)
                    
                    # Formatação
                    for col in ["RCL 2024", "TOTAL A SER APORTADO"]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                    
                    for col in ["DÍVIDA EM MORA / RCL", "% APLICADO"]:
                        if col in df_indices_styled.columns:
                            df_indices_styled[col] = df_indices_styled[col].apply(lambda x: converter_e_formatar(x, 'percentual'))
                        
                    st.dataframe(df_indices_styled, use_container_width=True, hide_index=True)

                with tab2: # ABA APORTES DETALHADOS 
                    st.subheader("Valores Aportados por Tribunal")
                    
                    # Usando nomes internos ATUAIS para referenciar o DF
                    colunas_aportes_original = [
                        "ENTE", 
                        COLUNA_APORTES_TJPE_INTERNO, 
                        COLUNA_APORTES_TRF5_INTERNO, 
                        COLUNA_APORTES_TRT6_INTERNO,
                        COLUNA_APORTES_INTERNO # Total (VALOR APORTADO)
                    ]
                    
                    # Mapeamento para os nomes de exibição na tabela
                    colunas_renomeadas_aportes = {
                        COLUNA_APORTES_TJPE_INTERNO: "APORTES TJPE", 
                        COLUNA_APORTES_TRF5_INTERNO: "APORTES TRF5", 
                        COLUNA_APORTES_TRT6_INTERNO: "APORTES TRT6",
                        COLUNA_APORTES_INTERNO: "TOTAL APORTADO"
                    }
                    
                    df_aportes_styled = df_exibicao_final[[col for col in colunas_aportes_original if col in df_exibicao_final.columns]].copy()
                    
                    # Renomeia as colunas apenas para exibição nesta aba
                    df_aportes_styled.rename(columns=colunas_renomeadas_aportes, inplace=True)
                    
                    # Lista de colunas a serem formatadas em moeda (os novos nomes de exibição)
                    colunas_moeda_aportes = ["APORTES TJPE", "APORTES TRF5", "APORTES TRT6", "TOTAL APORTADO"]
                    
                    for col in colunas_moeda_aportes:
                        if col in df_aportes_styled.columns:
                             df_aportes_styled[col] = df_aportes_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))

                    st.dataframe(df_aportes_styled, use_container_width=True, hide_index=True)
                
                with tab3:
                    st.subheader("Rateio por Tribunal: Visualização")
                    
                    # Seletor para alternar entre % e R$
                    rateio_view = st.radio(
                        "Escolha a métrica:",
                        ["Porcentual (%)", "Valor (R$)", ],
                        key="rateio_view",
                        horizontal=True
                    )
                    
                    if rateio_view == "Porcentual (%)":
                        # --- Visualização por Porcentual (%) ---
                        
                        colunas_rateio = ["ENTE", COLUNA_PERCENTUAL_TJPE_INTERNO, COLUNA_PERCENTUAL_TRF5_INTERNO, COLUNA_PERCENTUAL_TRT6_INTERNO]
                        df_rateio_styled = df_exibicao_final[[col for col in colunas_rateio if col in df_exibicao_final.columns]].copy()
                        
                        # Renomeia
                        df_rateio_styled.rename(columns={
                            COLUNA_PERCENTUAL_TJPE_INTERNO: "TJPE (%)", 
                            COLUNA_PERCENTUAL_TRF5_INTERNO: "TRF5 (%)", 
                            COLUNA_PERCENTUAL_TRT6_INTERNO: "TRT6 (%)"
                        }, inplace=True)

                        # Formatação
                        for col in ["TJPE (%)", "TRF5 (%)", "TRT6 (%)"]:
                            if col in df_rateio_styled.columns:
                                df_rateio_styled[col] = df_rateio_styled[col].apply(lambda x: converter_e_formatar(x, 'percentual'))
                                
                        st.dataframe(df_rateio_styled, use_container_width=True, hide_index=True)

                    elif rateio_view == "Valor (R$)":
                        # --- Visualização por Valor (R$) ---
                        
                        # Usando os nomes internos TJPE, TRF5, TRT6 (que contêm o valor R$)
                        colunas_rateio_rs = ["ENTE", COLUNA_TJPE_SIMPLES_INTERNO, COLUNA_TRF5_SIMPLES_INTERNO, COLUNA_TRT6_SIMPLES_INTERNO]
                        df_rateio_rs_styled = df_exibicao_final[[col for col in colunas_rateio_rs if col in df_exibicao_final.columns]].copy()
                        
                        # Renomeia para o display de valor
                        df_rateio_rs_styled.rename(columns={
                            COLUNA_TJPE_SIMPLES_INTERNO: "TJPE (R$)", 
                            COLUNA_TRF5_SIMPLES_INTERNO: "TRF5 (R$)", 
                            COLUNA_TRT6_SIMPLES_INTERNO: "TRT6 (R$)"
                        }, inplace=True)

                        # Formatação
                        colunas_moeda_rateio = ["TJPE (R$)", "TRF5 (R$)", "TRT6 (R$)"]
                        for col in colunas_moeda_rateio:
                            if col in df_rateio_rs_styled.columns:
                                df_rateio_rs_styled[col] = df_rateio_rs_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))
                        
                        st.dataframe(df_rateio_rs_styled, use_container_width=True, hide_index=True)


                with tab4: 
                    st.subheader("Composição da Dívida: Estoque por Tribunal")
                    
                    # Seletor para alternar entre Em Mora, Vincendos e Total
                    divida_view = st.radio(
                        "Escolha a situação do estoque:",
                        ["Total", "Em Mora", "Vincendos"],
                        key="divida_view",
                        horizontal=True
                    )

                    # 1. Definição das colunas com base na seleção
                    if divida_view == "Em Mora":
                        colunas_originais = [
                            "ENTE", 
                            "ESTOQUE EM MORA - [TJPE]", 
                            "ESTOQUE EM MORA - [TRF5]", 
                            "ESTOQUE EM MORA - [TRT6]", 
                            "ESTOQUE EM MORA" # Total
                        ]
                        colunas_display = {
                            "ESTOQUE EM MORA - [TJPE]": "TJPE (Em Mora)", 
                            "ESTOQUE EM MORA - [TRF5]": "TRF5 (Em Mora)", 
                            "ESTOQUE EM MORA - [TRT6]": "TRT6 (Em Mora)", 
                            "ESTOQUE EM MORA": "TOTAL EM MORA"
                        }
                    elif divida_view == "Vincendos":
                        colunas_originais = [
                            "ENTE", 
                            "ESTOQUE VINCENDOS - [TJPE]", 
                            "ESTOQUE VINCENDOS - [TRF5]", 
                            "ESTOQUE VINCENDOS - [TRT6]", 
                            "ESTOQUE VINCENDOS" # Total
                        ]
                        colunas_display = {
                            "ESTOQUE VINCENDOS - [TJPE]": "TJPE (Vincendos)", 
                            "ESTOQUE VINCENDOS - [TRF5]": "TRF5 (Vincendos)", 
                            "ESTOQUE VINCENDOS - [TRT6]": "TRT6 (Vincendos)", 
                            "ESTOQUE VINCENDOS": "TOTAL VINCENDOS"
                        }
                    else: # Default: Total (Endividamento Total)
                        colunas_originais = [
                            "ENTE", 
                            "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]", 
                            "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]", 
                            "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]", 
                            COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY # Total
                        ]
                        colunas_display = {
                            "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TJPE]": "TJPE (Total)", 
                            "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRF5]": "TRF5 (Total)", 
                            "ENDIVIDAMENTO TOTAL EM JAN/2025 - [TRT6]": "TRT6 (Total)", 
                            COLUNA_ENDIVIDAMENTO_TOTAL_DISPLAY: "TOTAL ENDIVIDAMENTO"
                        }

                    # 2. Processamento e estilização da tabela
                    # Filtra apenas as colunas que existem no DataFrame
                    df_divida_styled = df_exibicao_final[[col for col in colunas_originais if col in df_exibicao_final.columns]].copy()
                    
                    # Renomeia as colunas
                    df_divida_styled.rename(columns=colunas_display, inplace=True)
                    
                    # Colunas de valor a serem formatadas (excluindo 'ENTE')
                    colunas_moeda_divida = [col for col in df_divida_styled.columns if col != "ENTE"]

                    # Formatação em moeda
                    for col in colunas_moeda_divida:
                        if col in df_divida_styled.columns:
                             df_divida_styled[col] = df_divida_styled[col].apply(lambda x: converter_e_formatar(x, 'moeda'))

                    st.dataframe(df_divida_styled, use_container_width=True, hide_index=True)
                
        except Exception as e:
            # Mantém a mensagem de erro robusta em caso de falha de leitura (por segurança)
            st.error(f"❌ Ocorreu um erro inesperado durante o processamento. Detalhes: {e}")
            st.warning(f"Verifique se o seu CSV possui problemas de formatação. As colunas críticas esperadas são: {', '.join(COLUNAS_CRITICAS)}.")

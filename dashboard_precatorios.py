import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página (Modo Escuro será aplicado se o tema do usuário for "Dark") ---
st.set_page_config(
    page_title="Dashboard de Precatórios - EC 136/2025",
    layout="wide",
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

st.title("Monitoramento de Precatórios (EC 136/2025)")
st.caption("Organização e Análise por Ente Devedor")

# ----------------------------------------------------
# Processamento Condicional
# ----------------------------------------------------
if uploaded_file is not None:
    # Adicionar um 'spinner' para dar feedback profissional
    with st.spinner('Processando e limpando dados...'):
        try:
            # 2. Leitura do arquivo (usando o separador ;)
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- Limpeza e Conversão de Colunas Numéricas ---
            
            # Definir as colunas que DEVEM ser numéricas no formato Real Brasileiro
            colunas_numericas = [
                "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", 
                "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6",
                "APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]" 
            ]

            # Iterar e limpar cada coluna
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
                    
            # Tratar colunas categóricas e verificar a existência das colunas críticas
            colunas_criticas = ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES"]
            if not all(col in df.columns for col in colunas_criticas):
                 st.error(f"Erro: O arquivo CSV deve conter as colunas críticas: {', '.join(colunas_criticas)}. Verifique o cabeçalho.")
                 st.stop()
                 
            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
                 
        except Exception as e:
            st.error(f"Ocorreu um erro fatal durante a leitura ou limpeza dos dados. Detalhes: {e}")
            st.stop()


    # --- Filtros (na Sidebar) ---
    with st.sidebar:
        st.markdown("---")
        st.header("Filtros Analíticos")
        
        entes_lista = df["ENTE"].unique().tolist()
        status_lista = df["STATUS"].unique().tolist()
        
        # FILTRO DE ENTE AGORA É LISTA SUSPENSA (st.selectbox)
        selected_ente = st.selectbox(
            "Ente Devedor:", 
            options=["Todos"] + sorted(entes_lista) # Opção "Todos" + Entes em ordem alfabética
        )
        
        # Filtro Selectbox de Status
        selected_status = st.selectbox(
            "Status da Dívida:", 
            options=["Todos"] + status_lista
        )
    
    # 4. Aplicação dos filtros
    # Lógica de filtro para ENTE (se "Todos", filtra todos)
    filtro_entes = df["ENTE"] == selected_ente if selected_ente != "Todos" else df["ENTE"].notnull()
    filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
    
    df_filtrado = df[filtro_status & filtro_entes]
    
    # ----------------------------------------------------
    # Visualização Principal (Modo Escuro e Formal)
    # ----------------------------------------------------
    
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados. Ajuste os filtros na barra lateral.")
    else:
        
        # Exibição de Métricas Chave (KPls) em colunas
        total_divida = df_filtrado["ENDIVIDAMENTO TOTAL"].sum()
        total_aportes = df_filtrado["APORTES"].sum()
        num_entes = df_filtrado["ENTE"].nunique()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
        with col2:
            st.metric(label="Endividamento Total (R$)", value=f"R$ {total_divida:,.2f}")
        with col3:
            st.metric(label="Total de Aportes Realizados (R$)", value=f"R$ {total_aportes:,.2f}")


        st.header("Análise Detalhada dos Entes Devedores")
        
        # Gráfico 1: Endividamento Total
        st.subheader("1. Dívida Consolidada por Ente e Status")
        fig = px.bar(
            df_filtrado.sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False),
            x="ENTE",
            y="ENDIVIDAMENTO TOTAL",
            color="STATUS",
            labels={"ENTE": "Ente Devedor", "ENDIVIDAMENTO TOTAL": "Endividamento Total (R$)"},
            height=500,
            template="plotly_dark", # TEMA ESCURO
            title="Endividamento Total por Ente (Ordem Decrescente)"
        )
        st.plotly_chart(fig, use_container_width=True)

        # Gráfico 2: Aportes por Tribunal
        st.subheader("2. Comparativo de Aportes por Tribunal")
        
        try:
            df_aportes_viz = df_filtrado.melt(
                id_vars="ENTE", 
                value_vars=["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"],
                var_name="Tribunal",
                value_name="Valor Aportado"
            )
            
            fig_aportes = px.bar(
                df_aportes_viz,
                x="ENTE",
                y="Valor Aportado",
                color="Tribunal",
                barmode="group",
                labels={"ENTE": "Ente Devedor", "Valor Aportado": "Valor Aportado (R$)", "Tribunal": "Tribunal de Referência"},
                height=500,
                template="plotly_dark", # TEMA ESCURO
                title="Aportes Detalhados por Ente e Tribunal"
            )
            st.plotly_chart(fig_aportes, use_container_width=True)
        except Exception:
            st.warning("Não foi possível gerar o gráfico de Aportes. Verifique se as colunas de aportes por Tribunal estão corretas.")

        # Tabela de Dados (Mais Formal)
        st.header("Tabela de Dados Brutos (Filtrados)")
        
        colunas_tabela = [
            "ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", 
            "DÍVIDA EM MORA / RCL", "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6"
        ]
        
        colunas_existentes_tabela = [col for col in colunas_tabela if col in df_filtrado.columns]
        
        st.dataframe(
            df_filtrado[colunas_existentes_tabela].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False), 
            use_container_width=True
        )

else:
    # Mensagem quando o arquivo não está carregado
    st.info("Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do dashboard.")

import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(
    page_title="Dashboard de Precatórios - EC 136/2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# 1. NOVO: Mover o Widget de Upload para a Sidebar
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
    with st.spinner('Processando dados...'):
        try:
            # 2. Leitura do arquivo (usando o separador ;)
            df = pd.read_csv(uploaded_file, delimiter=";")
            
            # --- Conversão e Verificação de Colunas ---
            # Verificação das colunas ENTE e STATUS
            if "ENTE" not in df.columns or "STATUS" not in df.columns:
                st.error("Erro: O arquivo CSV deve conter as colunas 'ENTE' e 'STATUS'. Verifique o cabeçalho.")
                st.stop()
            
            df["ENTE"] = df["ENTE"].astype(str)
            df["STATUS"] = df["STATUS"].astype(str)
            
            # --- Filtros (Permanece na Sidebar) ---
            st.sidebar.markdown("---") # Linha separadora
            st.sidebar.header("Filtros Analíticos")
            
            entes_lista = df["ENTE"].unique().tolist()
            status_lista = df["STATUS"].unique().tolist()
            
            # Filtro Multiselect
            selected_entes = st.sidebar.multiselect(
                "Ente(s) Devedor(es):", 
                options=entes_lista, default=entes_lista
            )
            
            # Filtro Selectbox
            selected_status = st.sidebar.selectbox(
                "Status da Dívida:", 
                options=["Todos"] + status_lista
            )
            
            # 4. Aplicação dos filtros
            filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
            filtro_entes = df["ENTE"].isin(selected_entes)
            df_filtrado = df[filtro_status & filtro_entes]
            
            # ----------------------------------------------------
            # Visualização Principal (Mais Formal)
            # ----------------------------------------------------
            
            if df_filtrado.empty:
                st.warning("Nenhum dado encontrado com os filtros selecionados.")
            else:
                
                # Exibição de Métricas Chave (KPls) em colunas
                total_divida = df_filtrado["ENDIVIDAMENTO TOTAL"].sum()
                total_aportes = df_filtrado["APORTES"].sum()
                num_entes = df_filtrado["ENTE"].nunique()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(label="Total de Entes Selecionados", value=f"{num_entes}")
                with col2:
                    st.metric(label="Endividamento Total (R$)", value=f"R$ {total_divida:,.2f}", delta_color="inverse")
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
                    template="plotly_white", # Tema mais limpo e formal
                    title="Endividamento Total por Ente (Ordem Decrescente)"
                )
                st.plotly_chart(fig, use_container_width=True)

                # Gráfico 2: Aportes por Tribunal (em uma coluna)
                st.subheader("2. Comparativo de Aportes por Tribunal")
                
                # Tentativa de criar o gráfico de Aportes
                try:
                    # Agrupando os dados para o gráfico de aportes (mais limpo)
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
                        template="plotly_white",
                        title="Aportes Detalhados por Ente e Tribunal"
                    )
                    st.plotly_chart(fig_aportes, use_container_width=True)
                except Exception:
                    st.warning("Não foi possível gerar o gráfico de Aportes. Verifique se as colunas 'APORTES - [TJPE]', 'APORTES - [TRF5]' e 'APORTES - [TRT6]' existem no arquivo com valores numéricos.")

                # Tabela de Dados (Mais Formal)
                st.header("Tabela de Dados Brutos (Filtrados)")
                st.dataframe(df_filtrado, use_container_width=True)
                
        except Exception as e:
            st.error(f"Ocorreu um erro fatal durante o processamento dos dados. Verifique a formatação do arquivo CSV. Detalhes: {e}")

else:
    # Mensagem quando o arquivo não está carregado
    st.info("Por favor, acesse a **barra lateral (seta superior esquerda)** e carregue o seu arquivo CSV para iniciar a análise do dashboard.")

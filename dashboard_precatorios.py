import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(
    page_title="Dashboard de Precatórios - EC 136/2025",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Dashboard de Precatórios - Organização por Ente Devedor")

# 1. NOVO: Widget para o usuário carregar o arquivo
uploaded_file = st.file_uploader(
    "1. Faça o upload do seu arquivo 'Painel-Entes.csv'",
    type=['csv']
)

# Apenas continua se o usuário carregar um arquivo
if uploaded_file is not None:
    # 2. Leitura do arquivo (usando o separador que estava no seu código original)
    try:
        df = pd.read_csv(uploaded_file, delimiter=";")
    except Exception as e:
        st.error(f"Erro ao ler o arquivo. Certifique-se de que ele é um CSV e usa o ponto e vírgula (;) como separador. Erro: {e}")
        st.stop() # Para a execução se a leitura falhar
        
    # --- Continuação do seu código original (dentro do bloco if) ---

    # Conversão de tipos de dados (como no seu código original)
    try:
        df["ENTE"] = df["ENTE"].astype(str)
        df["STATUS"] = df["STATUS"].astype(str)
    except KeyError as e:
        st.error(f"O arquivo CSV não possui as colunas esperadas (ENTE ou STATUS). Verifique o cabeçalho. Erro: {e}")
        st.stop()
        
    st.sidebar.header("Filtros de Visualização")
    
    # 3. Tratamento de listas para filtros
    entes_lista = df["ENTE"].unique().tolist()
    status_lista = df["STATUS"].unique().tolist()
    
    # Filtro Multiselect
    selected_entes = st.sidebar.multiselect(
        "Selecione o(s) Ente(s) Devedor(es):", 
        options=entes_lista, default=entes_lista
    )
    
    # Filtro Selectbox
    selected_status = st.sidebar.selectbox(
        "Selecione o Status:", 
        options=["Todos"] + status_lista
    )
    
    # 4. Aplicação dos filtros
    filtro_status = df["STATUS"] == selected_status if selected_status != "Todos" else df["STATUS"].notnull()
    filtro_entes = df["ENTE"].isin(selected_entes)
    df_filtrado = df[filtro_status & filtro_entes]
    
    # Verifica se há dados após a filtragem
    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        # --- Visualização de Dados ---
        
        st.subheader("Entes Devedores Filtrados")
        
        # DataFrame de visualização
        st.dataframe(df_filtrado[
            ["ENTE", "STATUS", "ENDIVIDAMENTO TOTAL", "APORTES", "RCL 2024", "DÍVIDA EM MORA / RCL", "SALDO A PAGAR", "% TJPE", "% TRF5", "% TRT6"]
        ].sort_values(by="ENDIVIDAMENTO TOTAL", ascending=False), use_container_width=True)
        
        st.subheader("Distribuição do Endividamento Total")
        
        # Gráfico 1: Endividamento Total
        fig = px.bar(
            df_filtrado,
            x="ENTE",
            y="ENDIVIDAMENTO TOTAL",
            color="STATUS",
            labels={"ENTE": "Ente Devedor", "ENDIVIDAMENTO TOTAL": "Endividamento Total"},
            height=400,
            title="Dívida Total por Ente Devedor"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Aportes por Tribunal")
        
        # Gráfico 2: Aportes por Tribunal
        # Certifique-se de que estas colunas existem no seu CSV!
        try:
            fig_aportes = px.bar(
                df_filtrado,
                x="ENTE",
                y=["APORTES - [TJPE]", "APORTES - [TRF5]", "APORTES - [TRT6]"],
                labels={"value": "Valores de Aportes", "ENTE": "Ente Devedor", "variable": "Tribunal"},
                height=400,
                title="Aportes Realizados por Tribunal"
            )
            st.plotly_chart(fig_aportes, use_container_width=True)
        except ValueError as e:
            st.warning(f"Não foi possível gerar o gráfico de Aportes. Verifique se as colunas 'APORTES - [TJPE]', 'APORTES - [TRF5]' e 'APORTES - [TRT6]' existem no arquivo. Erro: {e}")

else:
    # Mensagem se o arquivo ainda não foi carregado
    st.info("Por favor, carregue o seu arquivo 'Painel-Entes.csv' para visualizar o dashboard.")

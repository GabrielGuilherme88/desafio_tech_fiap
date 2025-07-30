import streamlit as st
import pandas as pd
import os

#streamlit run dashboard.py

# Define o caminho relativo a partir do arquivo atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, 'exports', 'logs_monitoramento.csv')

st.title("Monitoramento de Rotas da API")

# Carrega os dados
try:
    df = pd.read_csv(LOG_FILE)
except FileNotFoundError:
    st.error(f"Arquivo não encontrado: {LOG_FILE}")
    st.stop()

# Mostra as primeiras linhas para referência (opcional)
st.subheader("Dados brutos")
st.dataframe(df)

# Agrupa por endpoint para contar chamadas e calcular tempo médio
summary = df.groupby('endpoint').agg(
    chamadas=('request_id', 'count'),
    tempo_medio_ms=('duration_ms', 'mean')
).reset_index()

# Formata o tempo médio com 2 casas decimais
summary['tempo_medio_ms'] = summary['tempo_medio_ms'].round(2)

st.subheader("Resumo por rota")
st.dataframe(summary)

# Gráfico de barras para chamadas por rota
st.subheader("Chamadas por rota")
st.bar_chart(summary.set_index('endpoint')['chamadas'])

# Gráfico de barras para tempo médio por rota
st.subheader("Tempo médio de execução por rota (ms)")
st.bar_chart(summary.set_index('endpoint')['tempo_medio_ms'])



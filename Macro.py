import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import re
from sklearn.preprocessing import StandardScaler
import scipy.cluster.hierarchy as sch
import numpy as np

st.set_page_config(page_title="Sugestão de Alocação Inteligente", layout="wide")
st.title("📊 Sugestão de Alocação Baseada em Notícias e HRP")

st.markdown("""
Este app utiliza o **Hierarchical Risk Parity (HRP)** para sugerir uma nova alocação de ativos a partir do seu cenário macroeconômico e da sua carteira atual.
Além disso, ele considera o **preço atual**, o **preço alvo** e o **preço alvo médio** dos analistas.
""")

# Função para obter preço atual, preço alvo e preço alvo médio do Yahoo Finance
def get_target_price(ticker):
    try:
        # Preço atual com yfinance
        data = yf.Ticker(ticker)
        price = data.info.get("regularMarketPrice")

        # Preço alvo com scraping
        analysis_url = f"https://finance.yahoo.com/quote/{ticker}/analysis?p={ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r2 = requests.get(analysis_url, headers=headers)
        match = re.search(r'"targetMeanPrice":(\d+\.\d+)', r2.text)
        target = float(match.group(1)) if match else None

        # Preço alvo médio
        mean_target = data.info.get("targetMeanPrice")

        return price, target, mean_target
    except:
        return None, None, None

# Notícias mais relevantes (mock com destaque atual)
def noticias_relevantes():
    return [
        "Inflação permanece acima da meta e Banco Central mantém juros elevados.",
        "Desemprego em queda estimula setores de consumo interno.",
        "Gastos públicos em alta pressionam cenário fiscal brasileiro.",
        "Estados Unidos implementam tarifas que elevam custos de importações.",
    ]

# Função HRP para reconfigurar alocação
def hrp_allocation(carteira, correl_matrix):
    """
    Função para aplicar o HRP na alocação de ativos.
    """
    # Step 1: Agrupamento Hierárquico
    # Criar a árvore hierárquica com base na matriz de correlação
    dist_matrix = np.sqrt(0.5 * (1 - correl_matrix))  # Calcular a distância de correlação
    linkage = sch.linkage(dist_matrix, 'ward')
    
    # Step 2: Aplicar a Hierarchical Risk Parity (HRP)
    clusters = sch.fcluster(linkage, t=1.15, criterion="distance")  # Define a critério de corte de clusters
    
    # Passo 3: Distribuição proporcional baseada no risco de cada cluster
    cluster_weights = []
    for cluster_id in np.unique(clusters):
        cluster_stocks = [i for i, c in enumerate(clusters) if c == cluster_id]
        cluster_weight = np.mean([carteira.iloc[i]["Peso (%)"] for i in cluster_stocks])  # Peso médio de cada grupo
        cluster_weights.append(cluster_weight)
    
    # Normalizar os pesos
    total_weight = sum(cluster_weights)
    normalized_weights = [weight / total_weight for weight in cluster_weights]
    
    # Aplicar os novos pesos aos ativos
    hrp_allocation = []
    for i, row in carteira.iterrows():
        cluster_id = clusters[i]
        cluster_weight = normalized_weights[cluster_id - 1]
        hrp_allocation.append({
            "Ticker": row["Ticker"],
            "Peso Atual (%)": row["Peso (%)"],
            "Peso Sugerido (%)": round(cluster_weight * 100, 2)
        })
    
    return pd.DataFrame(hrp_allocation)

# Upload da carteira
st.header("📁 Sua Carteira Atual")
arquivo = st.file_uploader("Envie um arquivo CSV com colunas: Ticker, Peso (%)", type=["csv"])

carteira_manual = [
    {"Ticker": "AGRO3.SA", "Peso (%)": 10},
    {"Ticker": "BBAS3.SA", "Peso (%)": 1.2},
    {"Ticker": "BBSE3.SA", "Peso (%)": 6.5},
    {"Ticker": "BPAC11.SA", "Peso (%)": 10.6},
    {"Ticker": "EGIE3.SA", "Peso (%)": 5},
    {"Ticker": "ITUB3.SA", "Peso (%)": 0.5},
    {"Ticker": "PRIO3.SA", "Peso (%)": 15},
    {"Ticker": "PSSA3.SA", "Peso (%)": 15},
    {"Ticker": "SAPR3.SA", "Peso (%)": 6.7},
    {"Ticker": "SBSP3.SA", "Peso (%)": 4},
    {"Ticker": "VIVT3.SA", "Peso (%)": 6.4},
    {"Ticker": "WEGE3.SA", "Peso (%)": 15},
    {"Ticker": "TOTS3.SA", "Peso (%)": 1},
    {"Ticker": "B3SA3.SA", "Peso (%)": 0.1},
    {"Ticker": "TAEE3.SA", "Peso (%)": 3},
]

st.markdown("### Ou adicione ativos manualmente:")
ticker_input = st.text_input("Ticker do ativo")
peso_input = st.number_input("Peso (%)", min_value=0.0, max_value=100.0, step=0.1)

if st.button("Adicionar ativo manualmente"):
    if ticker_input and peso_input:
        carteira_manual.append({"Ticker": ticker_input.upper(), "Peso (%)": peso_input})
        st.success(f"{ticker_input.upper()} adicionado com sucesso.")

carteira_csv = pd.read_csv(arquivo) if arquivo else pd.DataFrame()
carteira_manual_df = pd.DataFrame(carteira_manual)
carteira = pd.concat([carteira_csv, carteira_manual_df], ignore_index=True)

if not carteira.empty:
    st.dataframe(carteira)

    st.header("🌐 Análise de Cenário Econômico")
    noticias = noticias_relevantes()
    for n in noticias:
        st.markdown(f"- {n}")

    # Passo 1: Obter a matriz de correlação
    tickers = carteira['Ticker'].tolist()
    data = yf.download(tickers, period='1y', interval='1d')['Adj Close']
    returns = data.pct_change().dropna()
    correl_matrix = returns.corr()

    st.header("📌 Sugestão de Alocação com HRP")
    df_hrp_allocation = hrp_allocation(carteira, correl_matrix)
    st.dataframe(df_hrp_allocation)
else:
    st.info("Por favor, envie sua carteira ou insira ativos manualmente para continuar.")

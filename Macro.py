import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="Sugestão de Alocação Inteligente", layout="wide")
st.title("📊 Sugestão de Alocação Baseada em Notícias e Carteira Atual")

st.markdown("""
Este app analisa **notícias econômicas atuais** e sua **carteira** para sugerir uma **nova alocação**.
Além disso, compara os preços atuais dos ativos com os **preços alvo dos analistas**.
""")

# Função para obter preço alvo do Yahoo Finance
def get_target_price(ticker):
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/analysis?p={ticker}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")

        summary_url = f"https://finance.yahoo.com/quote/{ticker}"  # Para pegar preço atual
        r2 = requests.get(summary_url, headers=headers)
        soup2 = BeautifulSoup(r2.text, "html.parser")

        price = soup2.find("fin-streamer", {"data-symbol": ticker, "data-field": "regularMarketPrice"})
        price = float(price.text.replace(",", "")) if price else None

        # Target price médio (Price Target Mean)
        section = soup.find("section", {"data-test": "qsp-analyst"})
        if section:
            texts = section.get_text()
            start = texts.find("Average")
            if start != -1:
                value = texts[start:].split("\n")[1]
                target = float(value.replace("$", "").replace(",", ""))
                return price, target
        return price, None
    except:
        return None, None

# Notícias mais relevantes (mock com destaque atual)
def noticias_relevantes():
    return [
        "Inflação permanece acima da meta e Banco Central mantém juros elevados.",
        "Desemprego em queda estimula setores de consumo interno.",
        "Gastos públicos em alta pressionam cenário fiscal brasileiro.",
        "Estados Unidos implementam tarifas que elevam custos de importações.",
    ]

# Simulação de análise de notícias
def analisar_cenario():
    resumo = """
    **Resumo Econômico Atual:**
    - Crescimento do PIB em desaceleração.
    - Inflação persistente e juros altos.
    - Mercado de trabalho aquecido.
    - Aumento de gastos do governo gera alerta fiscal.

    **Setores Favorecidos:**
    - Consumo cíclico
    - Construção civil
    - Tecnologia nacional

    **Setores com alerta:**
    - Exportadoras (efeito câmbio e barreiras comerciais)
    - Bancos (margens pressionadas)
    - Energia (volatilidade global)
    """
    setores_favoraveis = ["consumo", "construção", "tecnologia"]
    setores_alerta = ["exportação", "bancos", "energia"]
    return resumo, setores_favoraveis, setores_alerta

# Upload da carteira
st.header("📁 Sua Carteira Atual")
arquivo = st.file_uploader("Envie um arquivo CSV com colunas: Ticker, Peso (%)", type=["csv"])

carteira_manual = [
    {"Ticker": "ITUB4.SA", "Peso (%)": 25},
    {"Ticker": "WEGE3.SA", "Peso (%)": 20},
    {"Ticker": "PETR4.SA", "Peso (%)": 15},
    {"Ticker": "VALE3.SA", "Peso (%)": 15},
    {"Ticker": "B3SA3.SA", "Peso (%)": 10},
    {"Ticker": "RENT3.SA", "Peso (%)": 15},
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

    resumo, setores_bull, setores_bear = analisar_cenario()
    st.markdown(resumo)

    st.header("📌 Sugestão de Alocação")
    sugestoes = []

    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        peso = row['Peso (%)']
        price, target = get_target_price(ticker)
        upside = round((target - price) / price * 100, 2) if price and target else None

        recomendacao = "Manter"
        if upside and upside > 15:
            recomendacao = "Aumentar"
        elif upside and upside < 0:
            recomendacao = "Reduzir"

        if any(s in ticker.lower() for s in setores_bull):
            if recomendacao == "Manter":
                recomendacao = "Aumentar"
        elif any(s in ticker.lower() for s in setores_bear):
            if recomendacao == "Manter":
                recomendacao = "Reduzir"

        sugestoes.append({
            "Ticker": ticker,
            "Peso Atual (%)": peso,
            "Preço Atual": price,
            "Preço Alvo": target,
            "Upside (%)": upside,
            "Recomendação": recomendacao
        })

    df_sugestoes = pd.DataFrame(sugestoes)
    st.dataframe(df_sugestoes)
else:
    st.info("Por favor, envie sua carteira ou insira ativos manualmente para continuar.")

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

# Simulação de análise de notícias (pode ser dinâmica com scraping)
def analisar_cenario():
    resumo = """
    **Resumo Econômico Atual:**
    - Crescimento do PIB em desaceleração.
    - Inflação acima da meta e juros elevados.
    - Desemprego em queda, impulsionando o consumo.
    - Aumento de gastos públicos gera dúvidas fiscais.

    **Setores Favorecidos:**
    - Consumo cíclico
    - Construção civil
    - Varejo
    
    **Setores com alerta:**
    - Energia
    - Exportadoras (risco externo)
    - Bancos (impacto dos juros)
    """
    setores_favoraveis = ["consumo", "construção", "varejo"]
    setores_alerta = ["energia", "exportação", "bancos"]
    return resumo, setores_favoraveis, setores_alerta

# Upload da carteira
st.header("📁 Sua Carteira Atual")
arquivo = st.file_uploader("Envie um arquivo CSV com colunas: Ticker, Peso (%)", type=["csv"])

if arquivo:
    carteira = pd.read_csv(arquivo)
    st.dataframe(carteira)

    st.header("🌐 Análise de Cenário Econômico")
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
        comentario = ""
        if upside and upside > 15:
            recomendacao = "Aumentar"
        elif upside and upside < 0:
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
    st.info("Por favor, envie sua carteira para continuar.")

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
import datetime
import json

# Função para coletar dados econômicos do Banco Central
def coletar_dados_banco_central():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/painel"
    try:
        response = requests.get(url)
        dados = response.json()
        anos = list({data['data'][:4] for data in dados})  # Filtra os anos disponíveis
        return anos
    except Exception as e:
        print(f"Erro ao coletar dados do Banco Central: {e}")
        return []

# Função para obter preço atual e preço alvo do Yahoo Finance
def get_target_price_yfinance(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"][0]
        target = stock.info.get("targetMeanPrice", None)
        return price, target
    except Exception as e:
        print(f"Erro ao buscar dados de {ticker}: {e}")
        return None, None

# Função para analisar anos semelhantes
def analise_historica_anos_similares(ticker, anos_simelhantes):
    try:
        stock = yf.Ticker(ticker)
        hoje = datetime.datetime.today().strftime('%Y-%m-%d')
        hist = stock.history(start="2017-01-01", end=hoje)["Close"]
        retornos = {}
        for ano in anos_simelhantes:
            dados_ano = hist[hist.index.year == ano]
            if not dados_ano.empty:
                retorno = dados_ano.pct_change().sum() * 100
                retornos[ano] = retorno
        media = np.mean(list(retornos.values())) if retornos else None
        return media
    except Exception as e:
        print(f"Erro ao calcular retorno histórico para {ticker}: {e}")
        return None

# Função para buscar notícias econômicas atuais
def noticias_reais(api_key):
    url = f"https://gnews.io/api/v4/search?q=economia+brasil&lang=pt&country=br&max=5&token={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        noticias = [article["title"] for article in data.get("articles", [])]
        return noticias
    except Exception as e:
        print(f"Erro ao buscar notícias: {e}")
        return []

# Função para analisar o cenário atual com base nas notícias
def analisar_cenario_com_noticias(noticias):
    setores_favoraveis = []
    setores_alerta = []
    resumo = ""

    for noticia in noticias:
        lower = noticia.lower()
        if "inflação" in lower or "juros altos" in lower:
            setores_alerta.extend(["bancos", "imobiliário"])
        if "desemprego em queda" in lower or "consumo" in lower:
            setores_favoraveis.append("consumo")
        if "gastos públicos" in lower or "governo" in lower:
            setores_favoraveis.append("construção")
        if "importação" in lower or "tarifa" in lower:
            setores_alerta.append("exportação")

    resumo += "\n".join([f"- {n}" for n in noticias])
    setores_favoraveis = list(set(setores_favoraveis))
    setores_alerta = list(set(setores_alerta))

    return resumo, setores_favoraveis, setores_alerta

# Função para ajustar a alocação de ativos
def ajustar_alocacao(carteira, setores_bull, setores_bear):
    sugestoes = []
    empresas_destaque = []

    # Cálculo do peso total
    peso_total = 0
    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        peso = row['Peso (%)']
        price, target = get_target_price_yfinance(ticker)
        upside = round((target - price) / price * 100, 2) if price and target else None

        recomendacao = "Manter"
        peso_sugerido = peso
        if upside is not None:
            if upside > 15:
                recomendacao = "Aumentar"
                peso_sugerido = min(peso * 1.2, 20)
            elif upside < 0:
                recomendacao = "Reduzir"
                peso_sugerido = max(peso * 0.8, 0)

        peso_total += peso_sugerido
        sugestoes.append({
            "Ticker": ticker,
            "Peso Atual (%)": peso,
            "Preço Atual": price,
            "Preço Alvo": target,
            "Upside (%)": upside,
            "Recomendação": recomendacao,
            "Peso Sugerido (%)": round(peso_sugerido, 2)
        })

    # Normalizar os pesos sugeridos para que o total seja 100%
    if peso_total > 0:
        fator_normalizacao = 100 / peso_total
        for sugestao in sugestoes:
            sugestao["Peso Sugerido (%)"] = round(sugestao["Peso Sugerido (%)"] * fator_normalizacao, 2)

    df_sugestoes = pd.DataFrame(sugestoes)
    return df_sugestoes

# Função para gerar um resumo das empresas em oportunidade
def gerar_resumo_empresas_oportunidade(carteira, setores_bull, setores_bear):
    empresas_destaque = []
    
    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        price, target = get_target_price_yfinance(ticker)
        retorno_medio = analise_historica_anos_similares(ticker, anos_similares)

        if "consumo" in setores_bull and "consumo" in ticker.lower():
            empresas_destaque.append({
                "Ticker": ticker,
                "Motivo": f"Setor de consumo favorecido pelas notícias econômicas atuais. Desempenho histórico positivo."
            })

        if retorno_medio and retorno_medio > 15:
            empresas_destaque.append({
                "Ticker": ticker,
                "Motivo": f"Desempenho superior ao histórico médio nos anos {', '.join(map(str, anos_similares))}."
            })

        if price and target:
            upside = round((target - price) / price * 100, 2)
            if upside and upside > 15:
                empresas_destaque.append({
                    "Ticker": ticker,
                    "Motivo": "Preço alvo sugere um alto potencial de valorização."
                })

    return empresas_destaque

# Streamlit Interface
st.set_page_config(page_title="Sugestão de Alocação Inteligente", layout="wide")
st.title("📊 Sugestão de Alocação Baseada em Notícias e Carteira Atual")

# Carregar dados de anos semelhantes (usando o Banco Central)
anos_similares = coletar_dados_banco_central()

# Exibir anos semelhantes
st.markdown(f"**Anos Semelhantes ao Cenário Atual (Baseado em Dados Econômicos):** {', '.join(anos_similares)}")

# Coletar notícias econômicas
api_key = st.secrets["GNEWS_API_KEY"] if "GNEWS_API_KEY" in st.secrets else "f81e45d8e741c24dfe4971f5403f5a32"
noticias = noticias_reais(api_key)
resumo, setores_bull, setores_bear = analisar_cenario_com_noticias(noticias)

# Exibir resumo de notícias e setores
st.markdown("**Notícias Recentes:**")
st.markdown(resumo)
st.markdown("**Setores Favorecidos:** " + ", ".join(setores_bull))
st.markdown("**Setores com Alerta:** " + ", ".join(setores_bear))

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

carteira_csv = pd.read_csv(arquivo) if arquivo else pd.DataFrame()
carteira_manual_df = pd.DataFrame(carteira_manual)
carteira = pd.concat([carteira_csv, carteira_manual_df], ignore_index=True)

if not carteira.empty:
    st.dataframe(carteira)
    
    # Ajustar alocação com base nas notícias e no cenário
    df_sugestoes = ajustar_alocacao(carteira, setores_bull, setores_bear)
    st.markdown("### Sugestões de Alocação de Ativos:")
    st.dataframe(df_sugestoes)

    # Resumo das empresas em oportunidade
    empresas_destaque = gerar_resumo_empresas_oportunidade(carteira, setores_bull, setores_bear)
    st.markdown("### Empresas com Oportunidade de Investimento:")
    for empresa in empresas_destaque:
        st.markdown(f"- **{empresa['Ticker']}**: {empresa['Motivo']}")

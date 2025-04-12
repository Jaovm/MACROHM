import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
import datetime

st.set_page_config(page_title="Sugestão de Alocação Inteligente", layout="wide")
st.title("📊 Sugestão de Alocação Baseada em Notícias e Carteira Atual")

st.markdown("""
Este app analisa **notícias econômicas atuais** e sua **carteira** para sugerir uma **nova alocação**.
Além disso, compara os preços atuais dos ativos com os **preços alvo dos analistas** e destaca empresas que performaram bem em **cenários econômicos semelhantes no passado**.
""")

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

# Função para buscar dados macroeconômicos do SGS (Bacen)
def get_macro_data_sgs(codigo_serie, data_inicio):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_serie}/dados?formato=json&dataInicial={data_inicio}"
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        df['valor'] = pd.to_numeric(df['valor'].str.replace(',', '.'), errors='coerce')
        df['data'] = pd.to_datetime(df['data'], dayfirst=True)
        return df.set_index('data')
    except Exception as e:
        print(f"Erro ao buscar série {codigo_serie}: {e}")
        return pd.DataFrame()

# Exibir dados macroeconômicos
st.subheader("📈 Indicadores Macroeconômicos Recentes")
hoje = datetime.datetime.today()
data_inicio_macro = (hoje - datetime.timedelta(days=365*5)).strftime("%d/%m/%Y")

indicadores = {
    "Inflação (IPCA) [% a.m.]": 433,
    "Taxa Selic [% a.a.]": 4189,
    "Câmbio (R$/US$)": 1,
    "PIB (variação % a.a.)": 7326
}

for nome, codigo in indicadores.items():
    df_macro = get_macro_data_sgs(codigo, data_inicio_macro)
    if not df_macro.empty:
        ultimo_valor = df_macro.iloc[-1]['valor']
        data_valor = df_macro.index[-1].strftime("%b/%Y")
        st.metric(label=nome + f" (último dado: {data_valor})", value=f"{ultimo_valor:.2f}")

# Análise de desempenho histórico durante anos semelhantes ao cenário atual
def analise_historica_anos_similares(ticker, anos_semelhantes):
    try:
        stock = yf.Ticker(ticker)
        hoje = datetime.datetime.today().strftime('%Y-%m-%d')
        hist = stock.history(start="2017-01-01", end=hoje)["Close"]
        retornos = {}
        for ano in anos_semelhantes:
            dados_ano = hist[hist.index.year == ano]
            if not dados_ano.empty:
                retorno = dados_ano.pct_change().sum() * 100
                retornos[ano] = retorno
        media = np.mean(list(retornos.values())) if retornos else None
        return media
    except Exception as e:
        print(f"Erro ao calcular retorno histórico para {ticker}: {e}")
        return None

# Busca notícias reais usando GNews API
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

# Simulação de análise de cenário com base em notícias reais
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

# Função para gerar o resumo das empresas que se destacam com base no cenário macroeconômico
def gerar_resumo_empresas_destaque_com_base_nas_noticias(carteira, setores_bull, setores_bear, anos_similares):
    empresas_destaque = []
    
    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        price, target = get_target_price_yfinance(ticker)
        retorno_medio = analise_historica_anos_similares(ticker, anos_similares)

        if "consumo" in setores_bull and "consumo" in ticker.lower():
            empresas_destaque.append({
                "Ticker": ticker,
                "Retorno Médio em Anos Similares (%)": retorno_medio,
                "Motivo": f"Setor de consumo favorecido pelas notícias econômicas atuais. Desempenho histórico positivo."
            })

        elif "construção" in setores_bull and "construção" in ticker.lower():
            empresas_destaque.append({
                "Ticker": ticker,
                "Retorno Médio em Anos Similares (%)": retorno_medio,
                "Motivo": f"Setor de construção favorecido pelas notícias econômicas atuais. Desempenho histórico positivo."
            })

        if retorno_medio is not None and retorno_medio > 15:
            empresas_destaque.append({
                "Ticker": ticker,
                "Retorno Médio em Anos Similares (%)": retorno_medio,
                "Motivo": f"Desempenho superior ao médio histórico nos anos {', '.join(map(str, anos_similares))}."
            })

        if "exportação" in setores_bear and "exportação" in ticker.lower():
            empresas_destaque.append({
                "Ticker": ticker,
                "Retorno Médio em Anos Similares (%)": retorno_medio,
                "Motivo": f"Setor de exportação em alerta devido a notícias econômicas. Desempenho histórico fraco."
            })

        if price and target:
            upside = round((target - price) / price * 100, 2)
            if upside and upside > 15:
                empresas_destaque.append({
                    "Ticker": ticker,
                    "Retorno Médio em Anos Similares (%)": retorno_medio if retorno_medio else "Não disponível",
                    "Motivo": "Preço alvo sugere um alto potencial de valorização."
                })

    return empresas_destaque

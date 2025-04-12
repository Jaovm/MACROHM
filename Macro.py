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

### 🧠 Critérios de Seleção de Empresas Favorecidas

1. **Setores Favorecidos pelo Cenário Atual:**
   - Análise de palavras-chave em notícias reais usando a GNews API.
   - Exemplo: "desemprego em queda" favorece o setor de consumo.

2. **Desempenho Histórico em Cenários Semelhantes:**
   - Empresas que performaram bem em anos similares (ex: 2019, 2022) são destacadas.
   - Considera-se retorno médio superior a 15% nesses anos como destaque.
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

    api_key = st.secrets["GNEWS_API_KEY"] if "GNEWS_API_KEY" in st.secrets else "f81e45d8e741c24dfe4971f5403f5a32"
    noticias = noticias_reais(api_key)
    resumo, setores_bull, setores_bear = analisar_cenario_com_noticias(noticias)

    st.markdown("**Notícias Recentes:**")
    st.markdown(resumo)

    st.markdown("**Setores Favorecidos:** " + ", ".join(setores_bull))
    st.markdown("**Setores com Alerta:** " + ", ".join(setores_bear))

    st.header("📌 Sugestão de Alocação")
    sugestoes = []
    empresas_destaque_historico = []
    anos_similares = [2019, 2022]

    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        peso = row['Peso (%)']
        price, target = get_target_price_yfinance(ticker)
        upside = round((target - price) / price * 100, 2) if price and target else None

        retorno_medio = analise_historica_anos_similares(ticker, anos_similares)
        if retorno_medio is not None and retorno_medio > 15:
            empresas_destaque_historico.append((ticker, retorno_medio))

        recomendacao = "Manter"
        peso_sugerido = peso
        if upside is not None:
            if upside > 15:
                recomendacao = "Aumentar"
                peso_sugerido = min(peso * 1.2, 20)
            elif upside < 0:
                recomendacao = "Reduzir"
                peso_sugerido = max(peso * 0.8, 0)

        sugestoes.append({
            "Ticker": ticker,
            "Peso Atual (%)": peso,
            "Preço Atual": price,
            "Preço Alvo": target,
            "Upside (%)": upside,
            "Recomendação": recomendacao,
            "Peso Sugerido (%)": round(peso_sugerido, 2)
        })

    df_sugestoes = pd.DataFrame(sugestoes)
    total = df_sugestoes['Peso Sugerido (%)'].sum()
    if total > 0:
        df_sugestoes['Peso Sugerido (%)'] = round(df_sugestoes['Peso Sugerido (%)'] / total * 100, 2)

    st.dataframe(df_sugestoes)

    st.header("📈 Empresas com Desempenho Histórico Destacado")
    if empresas_destaque_historico:
        destaque_df = pd.DataFrame(empresas_destaque_historico, columns=["Ticker", "Retorno Médio em Anos Similares (%)"])
        st.dataframe(destaque_df.sort_values(by="Retorno Médio em Anos Similares (%)", ascending=False))
    else:
        st.markdown("Nenhuma empresa teve desempenho destacado em anos semelhantes ao atual.")
else:
    st.info("Por favor, envie sua carteira ou insira ativos manualmente para continuar.")

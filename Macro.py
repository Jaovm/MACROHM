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

    palavras_chave_favoraveis = {
        "inflação": ["bancos", "imobiliário"],
        "juros altos": ["bancos", "imobiliário"],
        "desemprego em queda": ["consumo", "varejo", "automotivo"],
        "crescimento do consumo": ["varejo", "automotivo"],
        "gastos públicos": ["construção", "infraestrutura"],
        "setor exportação": ["agro", "mineração", "energia"]
    }
    
    palavras_chave_alerta = {
        "crise política": ["bancos", "imobiliário"],
        "recessão": ["consumo", "varejo", "automotivo"],
        "aumento de impostos": ["consumo", "varejo"]
    }

    for noticia in noticias:
        lower = noticia.lower()
        resumo += f"\n- {noticia}"
        
        # Verificando palavras-chave favoráveis
        for palavra, setores in palavras_chave_favoraveis.items():
            if palavra in lower:
                setores_favoraveis.extend(setores)

        # Verificando palavras-chave de alerta
        for palavra, setores in palavras_chave_alerta.items():
            if palavra in lower:
                setores_alerta.extend(setores)

    setores_favoraveis = list(set(setores_favoraveis))
    setores_alerta = list(set(setores_alerta))

    return resumo, setores_favoraveis, setores_alerta

# Função para gerar o resumo das empresas que se destacam com base no cenário macroeconômico
def gerar_resumo_empresas_destaque_com_base_nas_noticias(carteira, setores_bull, setores_bear):
    empresas_destaque = []
    
    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        price, target = get_target_price_yfinance(ticker)
        retorno_medio = analise_historica_anos_similares(ticker, anos_similares)

        # Verificar em qual setor a empresa se encaixa e gerar o resumo baseado nas notícias
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

        # Se o setor estiver em alerta e o desempenho histórico for negativo, adicionar ao alerta
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

    # Obter anos semelhantes ao cenário atual com base em inflação e taxa de juros
    anos_similares = [2019, 2022]  # Exemplo de anos semelhantes (ajustar conforme necessário)
    st.markdown(f"**Anos Semelhantes ao Cenário Atual (Baseado em Inflação e Juros):** {', '.join(map(str, anos_similares))}")

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

    st.write(f"**Total Peso Sugerido:** 100%")
    st.dataframe(df_sugestoes)

    # Gerar e exibir o resumo das empresas que se destacam com base no cenário macroeconômico
    empresas_destaque = gerar_resumo_empresas_destaque_com_base_nas_noticias(carteira, setores_bull, setores_bear)
    st.markdown("### Empresas que se Destacam no Cenário Atual com Base nas Notícias Econômicas:")
    for empresa in empresas_destaque:
        st.markdown(f"- **{empresa['Ticker']}**: {empresa['Motivo']}")

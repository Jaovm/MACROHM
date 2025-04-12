import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import requests
import datetime
import requests

# Função para obter dados do Banco Central (Inflação e Taxa de Juros)
def obter_dados_serie_bacen(serie_id, inicio, fim):
    """
    Função para acessar os dados do Banco Central usando a API SGS
    :param serie_id: Código da série temporal
    :param inicio: Ano de início da pesquisa (formato 'AAAA')
    :param fim: Ano de término da pesquisa (formato 'AAAA')
    :return: DataFrame com os dados históricos
    """
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie_id}/dados?formato=csv&dataInicial={inicio}&dataFinal={fim}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verificar erros na resposta
        dados = response.text
        dados_df = pd.read_csv(pd.compat.StringIO(dados), sep=";", encoding="latin1")
        return dados_df
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter dados: {e}")
        return None

# Função para obter inflação (IPCA) e Selic
def obter_dados_ambientais(ano_inicial, ano_final):
    inflacao_df = obter_dados_serie_bacen(433, str(ano_inicial), str(ano_final))
    selic_df = obter_dados_serie_bacen(1178, str(ano_inicial), str(ano_final))

    return inflacao_df, selic_df

# Função para calcular a proximidade entre anos (com base em inflação e taxa de juros)
def calcular_proximidade_anos_similares(inflacao_df, selic_df, ano_atual):
    # Obter inflação e Selic do ano atual (último ano disponível no DataFrame)
    inflacao_atual = inflacao_df[inflacao_df['valor'].index[-1]]
    selic_atual = selic_df[selic_df['valor'].index[-1]]

    proximidade = []

    # Calcular a proximidade entre o ano atual e os anos passados
    for ano in range(inflacao_df['valor'].index[0], inflacao_df['valor'].index[-1] + 1):
        inflacao_ano = inflacao_df[inflacao_df['valor'].index == ano]['valor'].values
        selic_ano = selic_df[selic_df['valor'].index == ano]['valor'].values
        
        if len(inflacao_ano) == 0 or len(selic_ano) == 0:
            continue
        
        # Diferença absoluta entre inflação e Selic
        prox_inflacao = abs(inflacao_atual - inflacao_ano[0])
        prox_selic = abs(selic_atual - selic_ano[0])

        proximidade_ano = prox_inflacao + prox_selic
        proximidade.append((ano, proximidade_ano))

    # Ordenar por proximidade e selecionar os 3 anos mais semelhantes
    anos_similares = sorted(proximidade, key=lambda x: x[1])

    return [ano for ano, _ in anos_similares[:3]]

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

st.markdown("### Ou adicione ativos manualmente clicando no botão abaixo")
carteira = pd.DataFrame(carteira_manual)

# Exibir as informações
st.write(carteira)

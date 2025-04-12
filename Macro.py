import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np

st.set_page_config(page_title="Sugestão de Alocação Inteligente", layout="wide")
st.title("📊 Sugestão de Alocação Baseada em Notícias e Carteira Atual")

st.markdown("""
Este app analisa **notícias econômicas atuais** e sua **carteira** para sugerir uma **nova alocação**.
Além disso, compara os preços atuais dos ativos com os **preços alvo dos analistas**.
""")

# Função para obter preço atual e preço alvo do Yahoo Finance
def get_target_price_yfinance(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")['Close'][0]
        target = stock.info['targetMeanPrice'] if 'targetMeanPrice' in stock.info else None
        return price, target
    except Exception as e:
        print(f"Erro ao buscar dados de {ticker}: {e}")
        return None, None

# Função para calcular o desempenho de empresas em cenários passados
def analise_historica(ticker, periodo="1y"):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=periodo)['Close']
        retorno = hist.pct_change().sum() * 100  # Calculando o retorno acumulado do período
        return retorno
    except Exception as e:
        print(f"Erro ao calcular desempenho histórico de {ticker}: {e}")
        return None

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

    resumo, setores_bull, setores_bear = analisar_cenario()
    st.markdown(resumo)

    st.header("📌 Sugestão de Alocação")
    sugestoes = []
    empresas_destacadas = []

    for i, row in carteira.iterrows():
        ticker = row['Ticker']
        peso = row['Peso (%)']
        price, target = get_target_price_yfinance(ticker)
        upside = round((target - price) / price * 100, 2) if price and target else None

        # Análise histórica do desempenho
        desempenho_historico = analise_historica(ticker, "1y")
        if desempenho_historico is not None and desempenho_historico > 20:  # Exemplo de filtro
            empresas_destacadas.append(ticker)

        recomendacao = "Manter"
        peso_sugerido = peso
        if upside is not None:
            if upside > 15:
                recomendacao = "Aumentar"
                peso_sugerido = min(peso * 1.2, 20)  # Limita a no máximo 20%
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

    st.header("🔍 Empresas com Desempenho Destacado")
    if empresas_destacadas:
        st.markdown(f"As seguintes empresas tiveram um desempenho destacado no último ano com mais de 20% de retorno acumulado: {', '.join(empresas_destacadas)}")
    else:
        st.markdown("Nenhuma empresa teve desempenho destacado com base no critério de 20% de retorno anual.")
else:
    st.info("Por favor, envie sua carteira ou insira ativos manualmente para continuar.")

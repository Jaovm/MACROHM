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

# Dados adicionais (exemplo: buscar informações do Yahoo Finance para algumas variáveis)
def get_yahoo_finance_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception as e:
        print(f"Erro ao buscar dados do Yahoo Finance para {ticker}: {e}")
        return None

# Exibindo os dados do Bacen primeiro
for nome, codigo in indicadores.items():
    df_macro = get_macro_data_sgs(codigo, data_inicio_macro)
    if not df_macro.empty:
        ultimo_valor = df_macro.iloc[-1]['valor']
        data_valor = df_macro.index[-1].strftime("%b/%Y")
        
        # Verifica se o último valor está correto (evita valores futuros ou com erro)
        if data_valor > hoje.strftime("%b/%Y"):
            data_valor = df_macro.index[-2].strftime("%b/%Y")  # Pega o valor anterior caso o atual seja inválido
            ultimo_valor = df_macro.iloc[-2]['valor']
        
        st.metric(label=nome + f" (último dado: {data_valor})", value=f"{ultimo_valor:.2f}")
    else:
        st.warning(f"Não foi possível obter dados para {nome}")

# Exemplo de adicionar um indicador do Yahoo Finance
ticker_cambio = 'BRL=X'  # Código do câmbio R$/US$
cambio_data = get_yahoo_finance_data(ticker_cambio)

if cambio_data:
    cambio_valor = cambio_data.get('regularMarketPrice', 'N/A')
    st.metric(label="Câmbio (R$/US$)", value=f"{cambio_valor}")

# Exemplo de adicionar outro indicador de ações
ticker_acao = 'PETR4.SA'  # Ticker da PETROBRAS
acao_data = get_yahoo_finance_data(ticker_acao)

if acao_data:
    acao_valor = acao_data.get('regularMarketPrice', 'N/A')
    st.metric(label="PETR4 (Preço Atual)", value=f"R${acao_valor}")

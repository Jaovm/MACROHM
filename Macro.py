import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import LedoitWolf
import streamlit as st

st.set_page_config(layout="wide")

# Lista de ações e pesos fundamentados
tickers = {
    'AGRO3.SA': 0.10, 'BBAS3.SA': 0.012, 'BBSE3.SA': 0.065, 'BPAC11.SA': 0.106,
    'EGIE3.SA': 0.05, 'ITUB3.SA': 0.005, 'PRIO3.SA': 0.15, 'PSSA3.SA': 0.15,
    'SAPR3.SA': 0.067, 'SBSP3.SA': 0.04, 'VIVT3.SA': 0.064, 'WEGE3.SA': 0.15,
    'TOTS3.SA': 0.01, 'B3SA3.SA': 0.001, 'TAEE3.SA': 0.03
}

start_date = '2017-01-01'
end_date = pd.Timestamp.today().strftime('%Y-%m-%d')

@st.cache_data
def baixar_dados(tickers, start, end):
    try:
        df = yf.download(list(tickers.keys()), start=start, end=end, group_by='ticker', auto_adjust=True)
        df = df.stack(level=0).rename_axis(index=['Date', 'Ticker']).reset_index()
        df = df.pivot(index='Date', columns='Ticker', values='Close')
        return df.dropna(axis=1, how='any')  # Remove ativos com dados ausentes
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def calcular_retorno_cov(dados):
    retornos = dados.pct_change().dropna()
    retorno_medio = retornos.mean() * 252
    cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252
    return retorno_medio, cov_matrix

def simular_carteiras(retorno_medio, cov_matrix, num_portfolios=50000, rf=0.0):
    n = len(retorno_medio)
    resultados = []
    pesos_lista = []
    for _ in range(num_portfolios):
        pesos = np.random.dirichlet(np.ones(n), size=1)[0]
        retorno = np.dot(pesos, retorno_medio)
        risco = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))
        sharpe = (retorno - rf) / risco if risco != 0 else 0
        resultados.append([retorno, risco, sharpe])
        pesos_lista.append(pesos)

    resultados = np.array(resultados)
    melhor_idx = np.argmax(resultados[:, 2])
    maior_ret_idx = np.argmax(resultados[:, 0])

    melhor_sharpe = {
        'retorno': resultados[melhor_idx, 0],
        'risco': resultados[melhor_idx, 1],
        'sharpe': resultados[melhor_idx, 2],
        'pesos': pesos_lista[melhor_idx]
    }

    maior_retorno = {
        'retorno': resultados[maior_ret_idx, 0],
        'risco': resultados[maior_ret_idx, 1],
        'sharpe': resultados[maior_ret_idx, 2],
        'pesos': pesos_lista[maior_ret_idx]
    }

    return resultados, pesos_lista, melhor_sharpe, maior_retorno

def plotar_grafico(resultados):
    plt.figure(figsize=(12, 6))
    plt.scatter(resultados[:, 1], resultados[:, 0], c=resultados[:, 2], cmap='viridis', s=3)
    plt.xlabel('Risco (Volatilidade)')
    plt.ylabel('Retorno Esperado')
    plt.title('Fronteira Eficiente - Simulação de Monte Carlo')
    st.pyplot(plt.gcf())

def exibir_resultados(dados, pesos_informados):
    retorno_medio, cov_matrix = calcular_retorno_cov(dados)
    ativos_validos = dados.columns.intersection(pesos_informados.keys())
    if len(ativos_validos) == 0:
        st.error("Nenhum ativo com dados válidos para análise.")
        return

    retorno_medio = retorno_medio[ativos_validos]
    cov_matrix_df = pd.DataFrame(cov_matrix, index=dados.columns, columns=dados.columns)
    cov_matrix = cov_matrix_df.loc[ativos_validos, ativos_validos].values
    pesos_informados_arr = np.array([pesos_informados[tic] for tic in ativos_validos])
    pesos_informados_arr /= pesos_informados_arr.sum()

    ret_informado = np.dot(pesos_informados_arr, retorno_medio)
    risco_informado = np.sqrt(np.dot(pesos_informados_arr.T, np.dot(cov_matrix, pesos_informados_arr)))

    st.subheader("Carteira Informada")
    st.write(f"Retorno esperado anualizado: {ret_informado:.2%}")
    st.write(f"Volatilidade anualizada: {risco_informado:.2%}")

    resultados, pesos, melhor_sharpe, maior_retorno = simular_carteiras(retorno_medio, cov_matrix)

    st.subheader("Carteira com Melhor Índice de Sharpe")
    st.write(f"Retorno: {melhor_sharpe['retorno']:.2%}")
    st.write(f"Risco: {melhor_sharpe['risco']:.2%}")
    st.write(f"Sharpe: {melhor_sharpe['sharpe']:.2f}")
    st.dataframe(pd.DataFrame({'Ticker': ativos_validos, 'Peso': melhor_sharpe['pesos']}))

    st.subheader("Carteira com Maior Retorno Esperado")
    st.write(f"Retorno: {maior_retorno['retorno']:.2%}")
    st.write(f"Risco: {maior_retorno['risco']:.2%}")
    st.write(f"Sharpe: {maior_retorno['sharpe']:.2f}")
    st.dataframe(pd.DataFrame({'Ticker': ativos_validos, 'Peso': maior_retorno['pesos']}))

    plotar_grafico(resultados)

def rodar_analise(tickers, start, end, pesos):
    dados = baixar_dados(tickers, start, end)
    if not dados.empty:
        exibir_resultados(dados, pesos)
    else:
        st.error("Erro ao carregar os dados. Verifique os tickers ou a conexão.")

rodar_analise(tickers, start_date, end_date, tickers)

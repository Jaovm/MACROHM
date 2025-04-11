import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date
from sklearn.covariance import LedoitWolf
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize

# Estilo
sns.set(style="whitegrid")

st.set_page_config(layout="wide")
st.title("Otimização de Carteira com Fronteira Eficiente")

# Ativos e pesos fundamentalistas
tickers = ['AGRO3.SA', 'BBAS3.SA', 'BBSE3.SA', 'BPAC11.SA', 'EGIE3.SA',
           'ITUB3.SA', 'PRIO3.SA', 'PSSA3.SA', 'SAPR3.SA', 'SBSP3.SA',
           'VIVT3.SA', 'WEGE3.SA', 'TOTS3.SA', 'B3SA3.SA', 'TAEE3.SA']

pesos_fundamentalistas = np.array([0.10, 0.012, 0.065, 0.106, 0.05,
                                   0.005, 0.15, 0.15, 0.067, 0.04,
                                   0.064, 0.15, 0.01, 0.001, 0.03])

data_inicio = st.date_input("Data de Início", date(2018, 1, 1))
data_fim = st.date_input("Data de Fim", date.today())

def get_price_data(tickers, start, end):
    df = yf.download(tickers, start=start, end=end, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        if 'Adj Close' in df.columns.levels[0]:
            return df['Adj Close'].dropna(axis=1, how='any')
        else:
            st.error("Erro: 'Adj Close' não encontrado nos dados.")
            return pd.DataFrame()
    else:
        if 'Adj Close' in df.columns:
            return df[['Adj Close']].dropna()
        else:
            st.error("Erro: Dados inválidos retornados pelo yfinance.")
            return pd.DataFrame()

@st.cache_data
def get_returns(tickers, start, end):
    prices = get_price_data(tickers, start, end)
    if prices.empty:
        return pd.DataFrame()
    return prices.pct_change().dropna()

def portfolio_performance(weights, mean_returns, cov_matrix):
    returns = np.dot(weights, mean_returns)
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = returns / std if std != 0 else 0
    return returns, std, sharpe

def optimize_portfolio(mean_returns, cov_matrix, bounds, constraint_sum):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)

    def neg_sharpe(weights, mean_returns, cov_matrix):
        return -portfolio_performance(weights, mean_returns, cov_matrix)[2]

    result = minimize(neg_sharpe, num_assets * [1. / num_assets],
                      args=args, method='SLSQP',
                      bounds=bounds, constraints=constraint_sum)

    return result

def simulate_random_portfolios(num_portfolios, mean_returns, cov_matrix):
    results = np.zeros((3, num_portfolios))
    weights_record = []
    for i in range(num_portfolios):
        weights = np.random.dirichlet(np.ones(len(mean_returns)), size=1).flatten()
        weights_record.append(weights)
        portfolio_return, portfolio_std, portfolio_sharpe = portfolio_performance(weights, mean_returns, cov_matrix)
        results[0,i] = portfolio_return
        results[1,i] = portfolio_std
        results[2,i] = portfolio_sharpe
    return results, weights_record

if st.button("Rodar Otimização"):
    returns = get_returns(tickers, data_inicio, data_fim)
    if returns.empty:
        st.stop()

    lw = LedoitWolf()
    cov_matrix = lw.fit(returns).covariance_
    mean_returns = returns.mean()

    num_assets = len(tickers)
    bounds = tuple((0, 1) for _ in range(num_assets))
    constraint = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

    result = optimize_portfolio(mean_returns, cov_matrix, bounds, constraint)

    max_sharpe_weights = result.x
    max_sharpe_ret, max_sharpe_vol, _ = portfolio_performance(max_sharpe_weights, mean_returns, cov_matrix)

    fundamentalista_ret, fundamentalista_vol, fundamentalista_sharpe = portfolio_performance(
        pesos_fundamentalistas, mean_returns, cov_matrix)

    # Encontrar carteira com maior retorno esperado
    def neg_return(weights, mean_returns, cov_matrix):
        return -portfolio_performance(weights, mean_returns, cov_matrix)[0]

    result_max_ret = minimize(neg_return, num_assets * [1. / num_assets],
                              args=(mean_returns, cov_matrix),
                              method='SLSQP', bounds=bounds, constraints=[constraint])
    max_return_weights = result_max_ret.x
    max_return_ret, max_return_vol, _ = portfolio_performance(max_return_weights, mean_returns, cov_matrix)

    # Simulação de Monte Carlo
    results, weights = simulate_random_portfolios(5000, mean_returns, cov_matrix)
    max_sharpe_idx = np.argmax(results[2])
    max_return_idx = np.argmax(results[0])

    plt.figure(figsize=(12, 6))
    plt.scatter(results[1, :], results[0, :], c=results[2, :], cmap='viridis', alpha=0.3)
    plt.colorbar(label='Sharpe Ratio')
    plt.scatter(max_sharpe_vol, max_sharpe_ret, marker='*', color='r', s=200, label='Máx Sharpe')
    plt.scatter(fundamentalista_vol, fundamentalista_ret, marker='X', color='orange', s=200, label='Fundamentalista')
    plt.scatter(max_return_vol, max_return_ret, marker='^', color='green', s=200, label='Máx Retorno')
    plt.xlabel('Risco (Volatilidade)')
    plt.ylabel('Retorno Esperado')
    plt.legend()
    st.pyplot(plt.gcf())

    st.subheader("Resultados das Carteiras")
    st.markdown("**Carteira com Maior Sharpe**")
    st.dataframe(pd.DataFrame({
        'Ticker': tickers,
        'Peso': np.round(max_sharpe_weights * 100, 2)
    }))

    st.markdown("**Carteira Fundamentalista**")
    st.dataframe(pd.DataFrame({
        'Ticker': tickers,
        'Peso': np.round(pesos_fundamentalistas * 100, 2)
    }))

    st.markdown("**Carteira com Maior Retorno Esperado**")
    st.dataframe(pd.DataFrame({
        'Ticker': tickers,
        'Peso': np.round(max_return_weights * 100, 2)
    }))

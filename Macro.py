import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize

st.set_page_config(layout='wide')

st.title("Otimização de Carteira com Fronteira Eficiente")

# Função robusta para baixar dados
def download_prices(tickers, start, end):
    data = yf.download(tickers, start=start, end=end, group_by='ticker', auto_adjust=False, threads=True)
    adj_close = pd.DataFrame()

    for ticker in tickers:
        try:
            if 'Adj Close' in data.columns:
                adj_close[ticker] = data['Adj Close'][ticker]
            elif isinstance(data[ticker], pd.DataFrame) and 'Adj Close' in data[ticker].columns:
                adj_close[ticker] = data[ticker]['Adj Close']
            else:
                st.warning(f"'Adj Close' ausente para {ticker}. Ignorando.")
        except Exception as e:
            st.warning(f"Erro com {ticker}: {e}")

    adj_close.dropna(axis=1, how='all', inplace=True)

    if adj_close.empty:
        st.error("Nenhum dado válido foi carregado.")
        st.stop()

    return adj_close

# Inputs
tickers_input = st.text_area("Tickers (separados por vírgula)", "AGRO3.SA, BBAS3.SA, BBSE3.SA, BPAC11.SA, EGIE3.SA, ITUB3.SA, PRIO3.SA, PSSA3.SA, SAPR3.SA, SBSP3.SA, VIVT3.SA, WEGE3.SA, TOTS3.SA, B3SA3.SA, TAEE3.SA")
tickers = [x.strip() for x in tickers_input.split(",")]
start_date = st.date_input("Data de início", pd.to_datetime("2018-01-01"))
end_date = st.date_input("Data final", pd.to_datetime("today"))

# Pesos personalizados
custom_weights = {}
st.subheader("Pesos personalizados (opcional)")
for ticker in tickers:
    peso = st.number_input(f"Peso {ticker} (%)", min_value=0.0, max_value=100.0, value=0.0)
    custom_weights[ticker] = peso / 100

# Botão para rodar
if st.button("Otimizar Carteira"):
    prices = download_prices(tickers, start=start_date, end=end_date)
    returns = prices.pct_change().dropna()
    mean_returns = returns.mean() * 252

    cov_matrix = LedoitWolf().fit(returns).covariance_
    num_assets = len(returns.columns)

    # Funções de otimização
    def portfolio_perf(weights):
        ret = np.dot(weights, mean_returns)
        vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        return ret, vol, ret / vol

    def negative_sharpe(weights):
        return -portfolio_perf(weights)[2]

    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    bounds = tuple((0, 1) for _ in range(num_assets))
    initial = num_assets * [1. / num_assets]

    # Otimização
    result = minimize(negative_sharpe, initial, method='SLSQP', bounds=bounds, constraints=constraints)
    weights_sharpe = result.x
    ret_sharpe, vol_sharpe, sharpe_sharpe = portfolio_perf(weights_sharpe)

    # Carteira de maior retorno
    def negative_return(weights):
        return -np.dot(weights, mean_returns)

    result_ret = minimize(negative_return, initial, method='SLSQP', bounds=bounds, constraints=constraints)
    weights_ret = result_ret.x
    ret_ret, vol_ret, sharpe_ret = portfolio_perf(weights_ret)

    # Carteira personalizada (se pesos somam 1)
    weights_custom = np.array([custom_weights[ticker] for ticker in returns.columns])
    if np.isclose(weights_custom.sum(), 1):
        ret_custom, vol_custom, sharpe_custom = portfolio_perf(weights_custom)
    else:
        weights_custom = None

    # Fronteira eficiente
    target_returns = np.linspace(mean_returns.min(), mean_returns.max(), 50)
    frontier_vol = []

    for target in target_returns:
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.dot(x, mean_returns) - target}]
        result = minimize(lambda x: np.sqrt(np.dot(x.T, np.dot(cov_matrix, x))),
                          initial, method='SLSQP', bounds=bounds, constraints=cons)
        frontier_vol.append(result.fun)

    # Gráfico
    plt.figure(figsize=(10, 6))
    plt.plot(frontier_vol, target_returns, label='Fronteira Eficiente', color='blue')
    plt.scatter(vol_sharpe, ret_sharpe, marker='*', color='green', s=200, label='Máximo Sharpe')
    plt.scatter(vol_ret, ret_ret, marker='X', color='orange', s=150, label='Maior Retorno')

    if weights_custom is not None:
        plt.scatter(vol_custom, ret_custom, marker='D', color='purple', s=100, label='Carteira Informada')

    plt.xlabel('Volatilidade')
    plt.ylabel('Retorno Esperado')
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

    # Mostrar resultados
    st.subheader("Carteira Máximo Sharpe")
    st.dataframe(pd.DataFrame({'Peso (%)': weights_sharpe * 100}, index=returns.columns).round(2))
    st.markdown(f"**Retorno:** {ret_sharpe:.2%} | **Volatilidade:** {vol_sharpe:.2%} | **Sharpe:** {sharpe_sharpe:.2f}")

    st.subheader("Carteira Maior Retorno")
    st.dataframe(pd.DataFrame({'Peso (%)': weights_ret * 100}, index=returns.columns).round(2))
    st.markdown(f"**Retorno:** {ret_ret:.2%} | **Volatilidade:** {vol_ret:.2%} | **Sharpe:** {sharpe_ret:.2f}")

    if weights_custom is not None:
        st.subheader("Carteira Informada")
        st.dataframe(pd.DataFrame({'Peso (%)': weights_custom * 100}, index=returns.columns).round(2))
        st.markdown(f"**Retorno:** {ret_custom:.2%} | **Volatilidade:** {vol_custom:.2%} | **Sharpe:** {sharpe_custom:.2f}")
    else:
        st.warning("Pesos informados não somam 100%. Carteira informada não exibida.")
               

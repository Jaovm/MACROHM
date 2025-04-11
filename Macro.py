import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
from sklearn.covariance import LedoitWolf
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("Otimização de Carteira com Markowitz + Simulação Monte Carlo")

# Entrada de dados
tickers_input = st.text_input("Tickers separados por vírgula", "AGRO3.SA,BBAS3.SA,BBSE3.SA,BPAC11.SA,EGIE3.SA,ITUB3.SA,PRIO3.SA,PSSA3.SA,SAPR3.SA,SBSP3.SA,VIVT3.SA,WEGE3.SA,TOTS3.SA,B3SA3.SA,TAEE3.SA")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

start_date = st.date_input("Data de início", datetime.today() - timedelta(days=365 * 7))
end_date = st.date_input("Data de fim", datetime.today())

custom_weights_input = st.text_input("Pesos informados separados por vírgula (opcional)")
weights_custom = None
if custom_weights_input:
    try:
        weights_custom = [float(w.strip()) for w in custom_weights_input.split(",")]
        if not np.isclose(sum(weights_custom), 1.0):
            st.warning("A soma dos pesos informados deve ser 1.0")
            weights_custom = None
    except:
        st.warning("Pesos inválidos")

# Download de dados
def load_data(tickers):
    try:
        df = yf.download(tickers, start=start_date, end=end_date)["Adj Close"]
        if isinstance(df, pd.Series):
            df = df.to_frame()
        df = df.dropna()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

data = load_data(tickers)

if data is not None and not data.empty:
    returns = data.pct_change().dropna()
    mean_returns = returns.mean() * 252
    lw_cov = LedoitWolf().fit(returns)
    cov_matrix = lw_cov.covariance_
    num_assets = len(tickers)

    def portfolio_perf(weights):
        ret = np.dot(weights, mean_returns)
        vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = ret / vol
        return ret, vol, sharpe

    # Fronteira eficiente
    target_returns = np.linspace(mean_returns.min(), mean_returns.max(), 100)
    frontier_vol = []
    for r in target_returns:
        try:
            from scipy.optimize import minimize

            constraints = (
                {"type": "eq", "fun": lambda w: np.sum(w) - 1},
                {"type": "eq", "fun": lambda w: np.dot(w, mean_returns) - r}
            )
            bounds = tuple((0, 1) for _ in range(num_assets))
            result = minimize(lambda w: np.sqrt(np.dot(w.T, np.dot(cov_matrix, w))),
                              x0=np.ones(num_assets) / num_assets,
                              method='SLSQP', bounds=bounds, constraints=constraints)
            frontier_vol.append(result.fun)
        except:
            frontier_vol.append(np.nan)

    # Simulação Monte Carlo
    num_portfolios = 10_000
    results = np.zeros((3, num_portfolios))
    weights_record = []

    for i in range(num_portfolios):
        weights = np.random.random(num_assets)
        weights /= np.sum(weights)
        weights_record.append(weights)
        ret, vol, sharpe = portfolio_perf(weights)
        results[0, i] = ret
        results[1, i] = vol
        results[2, i] = sharpe

    # Máximo Sharpe
    max_sharpe_idx = np.argmax(results[2])
    ret_sharpe = results[0, max_sharpe_idx]
    vol_sharpe = results[1, max_sharpe_idx]
    weights_sharpe = weights_record[max_sharpe_idx]

    # Maior retorno
    max_ret_idx = np.argmax(results[0])
    ret_ret = results[0, max_ret_idx]
    vol_ret = results[1, max_ret_idx]
    weights_ret = weights_record[max_ret_idx]

    # Carteira informada
    if weights_custom is not None and len(weights_custom) == num_assets:
        ret_custom, vol_custom, sharpe_custom = portfolio_perf(weights_custom)
    else:
        ret_custom = vol_custom = sharpe_custom = None

    # Gráfico
    plt.figure(figsize=(10, 6))
    plt.scatter(results[1], results[0], c=results[2], cmap='viridis', alpha=0.3, label="Carteiras Aleatórias")
    plt.plot(frontier_vol, target_returns, color='blue', label="Fronteira Eficiente")
    plt.scatter(vol_sharpe, ret_sharpe, marker='*', color='green', s=200, label="Máximo Sharpe")
    plt.scatter(vol_ret, ret_ret, marker='X', color='orange', s=150, label="Maior Retorno")

    if weights_custom is not None:
        plt.scatter(vol_custom, ret_custom, marker='D', color='purple', s=100, label="Carteira Informada")

    plt.xlabel("Volatilidade")
    plt.ylabel("Retorno Esperado")
    plt.colorbar(label="Índice de Sharpe")
    plt.legend()
    plt.grid(True)
    st.pyplot(plt)

    # Exibir pesos
    st.subheader("Pesos Ótimos")
    st.write("Carteira de Máximo Sharpe:")
    st.dataframe(pd.DataFrame({"Ticker": tickers, "Peso": weights_sharpe}))

    st.write("Carteira de Maior Retorno:")
    st.dataframe(pd.DataFrame({"Ticker": tickers, "Peso": weights_ret}))

    if weights_custom is not None:
        st.write("Carteira Informada:")
        st.dataframe(pd.DataFrame({"Ticker": tickers, "Peso": weights_custom}))
else:
    st.warning("Erro ao carregar os dados. Verifique os tickers ou a conexão.")

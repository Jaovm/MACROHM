import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize

st.set_page_config(layout="wide")
st.title("Otimização de Carteira com Fronteira Eficiente")

# Entradas
tickers_input = st.text_input("Tickers (separados por vírgula):", "AGRO3.SA,BBAS3.SA,BBSE3.SA,BPAC11.SA,EGIE3.SA,ITUB3.SA,PRIO3.SA,PSSA3.SA,SAPR3.SA,SBSP3.SA,VIVT3.SA,WEGE3.SA,TOTS3.SA,B3SA3.SA,TAEE3.SA")
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip() != ""]

start_date = st.date_input("Data de início", pd.to_datetime("2018-01-01"))
end_date = st.date_input("Data de fim", pd.to_datetime("today"))

# Função de carregamento com tratamento robusto
def load_data(tickers):
    try:
        raw = yf.download(tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=True)

        if len(tickers) == 1:
            df = raw.copy()
        elif isinstance(raw.columns, pd.MultiIndex):
            df = pd.concat([raw[t]['Close'].rename(t) for t in tickers if t in raw.columns.levels[0]], axis=1)
        else:
            df = raw['Adj Close']

        df = df.dropna()
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# Otimização da carteira
def portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate=0.0):
    returns = np.dot(weights, mean_returns)
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sharpe = (returns - risk_free_rate) / std
    return returns, std, sharpe

def negative_sharpe(weights, mean_returns, cov_matrix, risk_free_rate=0.0):
    return -portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)[2]

def optimize_portfolio(mean_returns, cov_matrix, bounds, constraints):
    num_assets = len(mean_returns)
    init_guess = num_assets * [1. / num_assets]
    return minimize(negative_sharpe, init_guess, args=(mean_returns, cov_matrix),
                    method='SLSQP', bounds=bounds, constraints=constraints)

def simulate_portfolios(mean_returns, cov_matrix, num_simulations=10000, risk_free_rate=0.0):
    num_assets = len(mean_returns)
    results = np.zeros((num_simulations, 3 + num_assets))
    for i in range(num_simulations):
        weights = np.random.dirichlet(np.ones(num_assets))
        ret, std, sharpe = portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)
        results[i, 0] = ret
        results[i, 1] = std
        results[i, 2] = sharpe
        results[i, 3:] = weights
    return results

# Carregar dados e processar
df = load_data(tickers)

if df is not None and not df.empty:
    returns = df.pct_change().dropna()
    mean_returns = returns.mean()
    cov_matrix = LedoitWolf().fit(returns).covariance_

    num_assets = len(tickers)
    bounds = tuple((0, 1) for _ in range(num_assets))
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

    # Otimização
    opt = optimize_portfolio(mean_returns, cov_matrix, bounds, constraints)
    opt_weights = opt.x
    opt_ret, opt_vol, opt_sharpe = portfolio_performance(opt_weights, mean_returns, cov_matrix)

    # Simulação
    sim = simulate_portfolios(mean_returns, cov_matrix)
    sim_df = pd.DataFrame(sim, columns=['Retorno', 'Volatilidade', 'Sharpe'] + tickers)

    # Gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(sim_df['Volatilidade'], sim_df['Retorno'], c=sim_df['Sharpe'], cmap='viridis', alpha=0.4)
    ax.scatter(opt_vol, opt_ret, c='red', marker='*', s=200, label='Melhor Sharpe')
    ax.set_title("Fronteira Eficiente - Simulações de Carteira")
    ax.set_xlabel("Volatilidade")
    ax.set_ylabel("Retorno Esperado")
    ax.legend()
    fig.colorbar(scatter, label='Sharpe')
    st.pyplot(fig)

    # Exibir carteira otimizada
    st.subheader("Carteira Otimizada (Melhor Sharpe)")
    result_df = pd.DataFrame({'Ticker': tickers, 'Peso (%)': np.round(opt_weights * 100, 2)})
    st.dataframe(result_df.set_index('Ticker'))

    st.markdown(f"""
        **Retorno Esperado:** {opt_ret:.2%}  
        **Volatilidade Esperada:** {opt_vol:.2%}  
        **Índice de Sharpe:** {opt_sharpe:.2f}
    """)
else:
    st.error("Erro ao carregar os dados. Verifique os tickers ou a conexão.")

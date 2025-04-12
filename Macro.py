import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize

plt.style.use('seaborn-v0_8-darkgrid')

# Carteira com tickers e pesos baseados na análise fundamentalista
tickers = {
    'AGRO3.SA': 0.10, 'BBAS3.SA': 0.012, 'BBSE3.SA': 0.065, 'BPAC11.SA': 0.106,
    'EGIE3.SA': 0.05, 'ITUB3.SA': 0.005, 'PRIO3.SA': 0.15, 'PSSA3.SA': 0.15,
    'SAPR3.SA': 0.067, 'SBSP3.SA': 0.04, 'VIVT3.SA': 0.064, 'WEGE3.SA': 0.15,
    'TOTS3.SA': 0.01, 'B3SA3.SA': 0.001, 'TAEE3.SA': 0.03
}

start_date = "2018-01-01"
end_date = "2025-01-01"

def baixar_dados(tickers, start, end):
    try:
        df = yf.download(list(tickers.keys()), start=start, end=end, group_by='ticker', auto_adjust=True, progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df = pd.concat({tic: df[tic]['Close'] for tic in tickers}, axis=1)
        elif 'Adj Close' in df.columns:
            df = df['Adj Close']
        elif 'Close' in df.columns:
            df = df['Close']
        else:
            raise ValueError("Coluna 'Adj Close' ou 'Close' não encontrada.")
        df.dropna(axis=1, how='any', inplace=True)
        return df
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar dados: {e}")

def calcular_retorno_cov(dados):
    retornos = np.log(dados / dados.shift(1)).dropna()
    retornos = retornos.replace([np.inf, -np.inf], np.nan).dropna()
    media_retorno = retornos.mean() * 252
    cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252
    return media_retorno, cov_matrix

def simular_portfolios(n_simulacoes, retorno_medio, cov_matrix, retorno_min=None):
    n_ativos = len(retorno_medio)
    resultados = []
    pesos_lista = []

    for _ in range(n_simulacoes):
        pesos = np.random.dirichlet(np.ones(n_ativos), size=1).flatten()
        retorno = np.dot(pesos, retorno_medio)
        risco = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))
        sharpe = retorno / risco if risco > 0 else 0
        if retorno_min is None or retorno >= retorno_min:
            resultados.append([retorno, risco, sharpe])
            pesos_lista.append(pesos)
    return np.array(resultados), pesos_lista

def otimizar_portfolio(retorno_medio, cov_matrix, objetivo='sharpe', retorno_alvo=None):
    n = len(retorno_medio)
    def risco(pesos): return np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))
    def sharpe(pesos): return -np.dot(pesos, retorno_medio) / risco(pesos)

    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
    bounds = tuple((0, 1) for _ in range(n))
    init = np.ones(n) / n

    if objetivo == 'sharpe':
        result = minimize(sharpe, init, method='SLSQP', bounds=bounds, constraints=constraints)
    elif objetivo == 'retorno':
        constraints = (
            constraints,
            {'type': 'ineq', 'fun': lambda x: np.dot(x, retorno_medio) - retorno_alvo}
        )
        result = minimize(risco, init, method='SLSQP', bounds=bounds, constraints=constraints)

    return result.x if result.success else init

def exibir_resultados(dados, pesos_informados):
    retorno_medio, cov_matrix = calcular_retorno_cov(dados)

    resultados, pesos_lista = simular_portfolios(10000, retorno_medio, cov_matrix)
    retornos, riscos, sharpes = resultados[:, 0], resultados[:, 1], resultados[:, 2]

    idx_max_sharpe = np.argmax(sharpes)
    idx_max_retorno = np.argmax(retornos)

    pesos_sharpe = pesos_lista[idx_max_sharpe]
    pesos_max_retorno = pesos_lista[idx_max_retorno]

    pesos_informados_arr = np.array(list(pesos_informados.values()))
    ret_informado = np.dot(pesos_informados_arr, retorno_medio)
    risco_informado = np.sqrt(np.dot(pesos_informados_arr.T, np.dot(cov_matrix, pesos_informados_arr)))
    sharpe_informado = ret_informado / risco_informado

    print("Carteira Informada:", dict(zip(pesos_informados.keys(), np.round(pesos_informados_arr, 3))))
    print("Carteira Sharpe Máximo:", dict(zip(pesos_informados.keys(), np.round(pesos_sharpe, 3))))
    print("Carteira Maior Retorno Esperado:", dict(zip(pesos_informados.keys(), np.round(pesos_max_retorno, 3))))

    plt.figure(figsize=(12, 8))
    plt.scatter(riscos, retornos, c=sharpes, cmap='viridis', alpha=0.5)
    plt.colorbar(label='Sharpe Ratio')
    plt.scatter(risco_informado, ret_informado, c='red', marker='*', s=200, label='Carteira Informada')
    plt.scatter(resultados[idx_max_sharpe, 1], resultados[idx_max_sharpe, 0], c='gold', marker='*', s=200, label='Máx Sharpe')
    plt.scatter(resultados[idx_max_retorno, 1], resultados[idx_max_retorno, 0], c='blue', marker='*', s=200, label='Maior Retorno')
    plt.xlabel('Risco (Volatilidade)')
    plt.ylabel('Retorno Esperado')
    plt.legend()
    plt.title('Fronteira Eficiente com Carteiras')
    plt.show()

def rodar_analise(tickers, start, end, pesos_informados):
    dados = baixar_dados(tickers, start, end)
    exibir_resultados(dados, pesos_informados)

# Executar
rodar_analise(tickers, start_date, end_date, tickers)

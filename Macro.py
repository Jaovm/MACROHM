import yfinance as yf import pandas as pd import numpy as np import matplotlib.pyplot as plt import seaborn as sns from sklearn.covariance import LedoitWolf from scipy.optimize import minimize

Lista de tickers e pesos informados

tickers = { 'AGRO3.SA': 0.10, 'BBAS3.SA': 0.012, 'BBSE3.SA': 0.065, 'BPAC11.SA': 0.106, 'EGIE3.SA': 0.05, 'ITUB3.SA': 0.005, 'PRIO3.SA': 0.15, 'PSSA3.SA': 0.15, 'SAPR3.SA': 0.067, 'SBSP3.SA': 0.04, 'VIVT3.SA': 0.064, 'WEGE3.SA': 0.15, 'TOTS3.SA': 0.01, 'B3SA3.SA': 0.001, 'TAEE3.SA': 0.03 }

start_date = '2017-01-01' end_date = '2024-12-31'

Função para baixar os dados

def baixar_dados(tickers, start, end): df = yf.download(list(tickers.keys()), start=start, end=end)['Adj Close'] df = df.dropna(axis=1, how='all') return df

Função para calcular retorno e covariância

def calcular_retorno_cov(df): retornos = df.pct_change().dropna() retornos = retornos.replace([np.inf, -np.inf], np.nan).dropna() mean_returns = retornos.mean() * 252 cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252 return mean_returns, cov_matrix

Função para calcular métricas da carteira

def calcular_metricas(pesos, mean_returns, cov_matrix): retorno = np.dot(pesos, mean_returns) risco = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos))) sharpe = retorno / risco return retorno, risco, sharpe

Restrição: soma dos pesos = 1

def constraint_soma_pesos(pesos): return np.sum(pesos) - 1

Otimização da carteira

def otimizar_carteira(mean_returns, cov_matrix): num_assets = len(mean_returns) args = (mean_returns, cov_matrix) constraints = ({'type': 'eq', 'fun': constraint_soma_pesos}) bounds = tuple((0, 1) for _ in range(num_assets))

# Máximo Sharpe
resultado = minimize(lambda x: -calcular_metricas(x, *args)[2],
                     num_assets*[1./num_assets], args=args,
                     method='SLSQP', bounds=bounds, constraints=constraints)
# Máximo Retorno
resultado_retorno = minimize(lambda x: -calcular_metricas(x, *args)[0],
                             num_assets*[1./num_assets], args=args,
                             method='SLSQP', bounds=bounds, constraints=constraints)

return resultado.x, resultado_retorno.x

Rodar análise

def rodar_analise(tickers, start, end, pesos_informados): dados = baixar_dados(tickers, start, end) mean_returns, cov_matrix = calcular_retorno_cov(dados)

pesos_sharpe, pesos_retorno = otimizar_carteira(mean_returns, cov_matrix)

ret_info = {
    'Carteira Informada': calcular_metricas(np.array(list(pesos_informados.values())), mean_returns, cov_matrix),
    'Máximo Sharpe': calcular_metricas(pesos_sharpe, mean_returns, cov_matrix),
    'Máximo Retorno': calcular_metricas(pesos_retorno, mean_returns, cov_matrix)
}

for nome, (ret, risco, sharpe) in ret_info.items():
    print(f"{nome}: Retorno esperado: {ret:.2%}, Risco: {risco:.2%}, Sharpe: {sharpe:.2f}")

Executar

rodar_analise(tickers, start_date, end_date, tickers)


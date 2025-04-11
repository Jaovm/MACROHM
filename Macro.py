import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize

# Tickers e alocações fornecidos
tickers = [
    "AGRO3.SA", "BBAS3.SA", "BBSE3.SA", "BPAC11.SA", "EGIE3.SA",
    "ITUB3.SA", "PRIO3.SA", "PSSA3.SA", "SAPR3.SA", "SBSP3.SA",
    "VIVT3.SA", "WEGE3.SA", "TOTS3.SA", "B3SA3.SA", "TAEE3.SA"
]

pesos_informados = np.array([
    0.10, 0.012, 0.065, 0.106, 0.05,
    0.005, 0.15, 0.15, 0.067, 0.04,
    0.064, 0.15, 0.01, 0.001, 0.03
])

# Baixando os dados ajustados
def carregar_dados(tickers, anos=7):
    try:
        dados = yf.download(tickers, period=f"{anos}y", interval="1d", auto_adjust=True, progress=False)
        if 'Adj Close' in dados.columns:
            return dados['Adj Close'].dropna(how='all')
        elif isinstance(dados, pd.DataFrame):
            return dados.dropna(how='all')
        else:
            raise ValueError("Erro: 'Adj Close' não encontrado nos dados.")
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar dados: {e}")

# Estatísticas
def calcular_retorno_cov(dados):
    retornos = np.log(dados / dados.shift(1)).dropna()
    retorno_medio_anual = retornos.mean() * 252
    cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252
    return retorno_medio_anual, cov_matrix

# Funções de otimização
def port_return(weights, mean_returns):
    return np.dot(weights, mean_returns)

def port_volatility(weights, cov_matrix):
    return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate=0.0):
    p_ret = port_return(weights, mean_returns)
    p_vol = port_volatility(weights, cov_matrix)
    return -(p_ret - risk_free_rate) / p_vol

def optimize_portfolio(mean_returns, cov_matrix, return_min=None):
    num_assets = len(mean_returns)
    args = (mean_returns, cov_matrix)
    bounds = tuple((0, 1) for _ in range(num_assets))
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
    if return_min is not None:
        constraints.append({'type': 'ineq', 'fun': lambda x: port_return(x, mean_returns) - return_min})

    result_sharpe = minimize(neg_sharpe_ratio, num_assets * [1. / num_assets],
                              args=args, method='SLSQP', bounds=bounds, constraints=constraints)
    
    result_retmax = minimize(lambda x: -port_return(x, mean_returns),
                             num_assets * [1. / num_assets], method='SLSQP',
                             bounds=bounds, constraints=constraints)

    return result_sharpe.x, result_retmax.x

# Fronteira eficiente
def simular_portfolios(mean_returns, cov_matrix, n_sim=5000):
    num_assets = len(mean_returns)
    results = np.zeros((3, n_sim))
    weights_list = []
    
    for i in range(n_sim):
        weights = np.random.dirichlet(np.ones(num_assets), size=1)[0]
        ret = port_return(weights, mean_returns)
        vol = port_volatility(weights, cov_matrix)
        sharpe = (ret - 0) / vol
        results[0,i] = vol
        results[1,i] = ret
        results[2,i] = sharpe
        weights_list.append(weights)
    
    return results, weights_list

# Execução principal
dados = carregar_dados(tickers)
mean_returns, cov_matrix = calcular_retorno_cov(dados)

# Retorno mínimo desejado (ex: IPCA + prêmio = 6% a.a.)
retorno_minimo = 0.06

# Otimizações
w_sharpe, w_retmax = optimize_portfolio(mean_returns, cov_matrix, return_min=retorno_minimo)

# Simulações
results, weights_simulados = simular_portfolios(mean_returns, cov_matrix)

# Carteira informada
ret_inf = port_return(pesos_informados, mean_returns)
vol_inf = port_volatility(pesos_informados, cov_matrix)
sharpe_inf = (ret_inf - 0) / vol_inf

# Carteira de Sharpe
ret_sharpe = port_return(w_sharpe, mean_returns)
vol_sharpe = port_volatility(w_sharpe, cov_matrix)
sharpe_sharpe = (ret_sharpe - 0) / vol_sharpe

# Carteira de retorno máximo
ret_max = port_return(w_retmax, mean_returns)
vol_max = port_volatility(w_retmax, cov_matrix)
sharpe_max = (ret_max - 0) / vol_max

# Visualização
plt.figure(figsize=(10, 6))
plt.scatter(results[0,:], results[1,:], c=results[2,:], cmap='viridis', marker='o', alpha=0.3)
plt.colorbar(label='Sharpe Ratio')
plt.scatter(vol_inf, ret_inf, color='red', marker='X', s=100, label='Carteira Informada')
plt.scatter(vol_sharpe, ret_sharpe, color='blue', marker='X', s=100, label='Maior Sharpe')
plt.scatter(vol_max, ret_max, color='green', marker='X', s=100, label='Maior Retorno')
plt.xlabel('Volatilidade')
plt.ylabel('Retorno Esperado')
plt.title('Fronteira Eficiente - Carteiras')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import LedoitWolf

# Função para carregar os dados históricos
def carregar_dados(tickers, start_date, end_date):
    try:
        dados = yf.download(tickers, start=start_date, end=end_date)['Adj Close']
        return dados
    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        return None

# Função para calcular retorno médio e matriz de covariância
def calcular_retorno_cov(dados):
    # Calcular retornos logarítmicos diários
    retornos = np.log(dados / dados.shift(1)).dropna(how='all')

    # Remover colunas com valores NaN após o cálculo de retornos
    retornos = retornos.dropna(axis=1, how='any')

    # Verificar se existem valores inválidos (NaN ou Infinitos) nos dados de retornos
    if retornos.isnull().values.any() or not np.isfinite(retornos.values).all():
        print("Erro: Dados de retornos contêm valores inválidos.")
        return None, None
    
    # Calcular o retorno médio anualizado e a matriz de covariância anualizada
    retorno_medio_anual = retornos.mean() * 252  # 252 dias úteis no ano
    
    try:
        cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252  # Estimativa de covariância
    except ValueError as e:
        print(f"Erro ao calcular a matriz de covariância: {e}")
        return None, None
    
    return retorno_medio_anual, cov_matrix

# Função para simulação de Monte Carlo
def simulacao_monte_carlo(retorno_medio, cov_matrix, num_simulacoes=10000):
    np.random.seed(42)
    num_ativos = len(retorno_medio)
    resultados = np.zeros((3, num_simulacoes))
    
    for i in range(num_simulacoes):
        pesos = np.random.random(num_ativos)
        pesos /= np.sum(pesos)
        
        retorno_portfolio = np.sum(pesos * retorno_medio)
        risco_portfolio = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))
        
        resultados[0,i] = retorno_portfolio
        resultados[1,i] = risco_portfolio
        resultados[2,i] = retorno_portfolio / risco_portfolio  # Sharpe Ratio
    
    return resultados

# Função para gerar a fronteira eficiente
def fronteira_eficiente(retorno_medio, cov_matrix, num_simulacoes=10000):
    resultados = simulacao_monte_carlo(retorno_medio, cov_matrix, num_simulacoes)
    retorno_medio_simulado = resultados[0]
    risco_simulado = resultados[1]
    
    # Identificar a fronteira eficiente
    fronteira = pd.DataFrame({
        'Retorno': retorno_medio_simulado,
        'Risco': risco_simulado
    })
    
    # Ordenar pela maior relação retorno/risco
    fronteira = fronteira.sort_values(by='Risco')
    
    return fronteira

# Função para rodar a análise completa
def rodar_analise(tickers, start_date, end_date, pesos_informados=None):
    dados = carregar_dados(tickers, start_date, end_date)
    
    if dados is None:
        return
    
    retorno_medio, cov_matrix = calcular_retorno_cov(dados)
    
    if retorno_medio is None or cov_matrix is None:
        return
    
    # Simulação de Monte Carlo
    resultados_simulacao = simulacao_monte_carlo(retorno_medio, cov_matrix)
    
    # Fronteira eficiente
    fronteira = fronteira_eficiente(retorno_medio, cov_matrix)
    
    # Encontrar a carteira de maior retorno esperado
    maior_retorno_idx = np.argmax(resultados_simulacao[0])
    maior_retorno = resultados_simulacao[0][maior_retorno_idx]
    maior_risco = resultados_simulacao[1][maior_retorno_idx]
    
    print(f"Carteira de Maior Retorno Esperado: {maior_retorno:.4f} com Risco: {maior_risco:.4f}")
    
    # Plotar Fronteira Eficiente
    plt.figure(figsize=(10, 6))
    plt.scatter(resultados_simulacao[1], resultados_simulacao[0], c=resultados_simulacao[2], cmap='viridis', marker='o')
    plt.colorbar(label='Sharpe Ratio')
    plt.plot(fronteira['Risco'], fronteira['Retorno'], color='red', label='Fronteira Eficiente', linewidth=2)
    plt.title('Fronteira Eficiente - Simulação de Monte Carlo')
    plt.xlabel('Risco (Desvio Padrão)')
    plt.ylabel('Retorno Esperado')
    plt.legend()
    plt.show()

# Parâmetros
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']  # Exemplo de tickers
start_date = '2020-01-01'
end_date = '2023-01-01'

# Rodar a análise
rodar_analise(tickers, start_date, end_date)

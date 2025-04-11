import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import LedoitWolf

# Função para carregar os dados
def carregar_dados(tickers, start_date, end_date):
    dados = yf.download(tickers, start=start_date, end=end_date)
    
    if 'Adj Close' not in dados.columns:
        print("Erro: 'Adj Close' não encontrado nos dados.")
        return None
    dados = dados['Adj Close']
    
    # Limpeza de dados: remover colunas com todos os valores ausentes
    dados = dados.dropna(axis=1, how='all')
    
    # Preencher valores ausentes (NaN) com o método forward fill
    dados = dados.fillna(method='ffill').dropna()
    
    return dados

# Função para calcular retorno médio e matriz de covariância
def calcular_retorno_cov(dados):
    # Calcular retornos logarítmicos diários
    retornos = np.log(dados / dados.shift(1)).dropna(how='all')

    # Remover colunas com valores NaN após o cálculo de retornos
    retornos = retornos.dropna(axis=1, how='any')
    
    # Calcular o retorno médio anualizado e a matriz de covariância anualizada
    retorno_medio_anual = retornos.mean() * 252  # 252 dias úteis no ano
    cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252  # Estimativa de covariância
    
    return retorno_medio_anual, cov_matrix

# Função para otimizar a carteira usando a Teoria de Markowitz
def otimizar_carteira(retorno_medio, cov_matrix, n_portfolios=10000):
    resultados = np.zeros((3, n_portfolios))  # Armazenar resultados: [retorno, risco, Sharpe]
    for i in range(n_portfolios):
        pesos = np.random.random(len(retorno_medio))
        pesos /= np.sum(pesos)  # Normalizar os pesos
        
        retorno_portfolio = np.sum(pesos * retorno_medio)  # Retorno esperado
        risco_portfolio = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))  # Risco (volatilidade)
        sharpe_ratio = retorno_portfolio / risco_portfolio  # Índice de Sharpe

        resultados[0, i] = retorno_portfolio
        resultados[1, i] = risco_portfolio
        resultados[2, i] = sharpe_ratio

    return resultados

# Função para plotar os resultados
def plotar_resultados(resultados, retorno_medio, cov_matrix):
    plt.figure(figsize=(10, 6))

    # Plotando a Fronteira Eficiente
    plt.scatter(resultados[1, :], resultados[0, :], c=resultados[2, :], cmap='YlGnBu', marker='o')
    plt.title('Fronteira Eficiente (Teoria de Markowitz)')
    plt.xlabel('Risco (Volatilidade)')
    plt.ylabel('Retorno Esperado')
    plt.colorbar(label='Índice de Sharpe')

    # Melhor carteira (maior Sharpe)
    melhor_sharpe_idx = np.argmax(resultados[2])
    melhor_retorno = resultados[0, melhor_sharpe_idx]
    melhor_risco = resultados[1, melhor_sharpe_idx]
    plt.scatter(melhor_risco, melhor_retorno, color='red', marker='*', s=200, label="Melhor Sharpe")

    plt.legend(loc='upper left')
    plt.show()

# Função para exibir a carteira de maior retorno
def carteira_maior_retorno(retorno_medio, cov_matrix):
    resultados = otimizar_carteira(retorno_medio, cov_matrix)
    
    # Encontrando a carteira com maior retorno esperado
    maior_retorno_idx = np.argmax(resultados[0, :])
    maior_retorno = resultados[0, maior_retorno_idx]
    maior_risco = resultados[1, maior_retorno_idx]
    
    print(f"Carteira de maior retorno esperado: \nRetorno: {maior_retorno:.4f}, Risco: {maior_risco:.4f}")
    
    return maior_retorno, maior_risco

# Função para exibir a carteira informada
def carteira_informada(pesos_informados, retorno_medio, cov_matrix):
    retorno_informado = np.sum(pesos_informados * retorno_medio)
    risco_informado = np.sqrt(np.dot(pesos_informados.T, np.dot(cov_matrix, pesos_informados)))
    
    print(f"Carteira Informada: \nRetorno: {retorno_informado:.4f}, Risco: {risco_informado:.4f}")
    
    return retorno_informado, risco_informado

# Função para rodar a análise
def rodar_analise(tickers, start_date, end_date, pesos_informados=None):
    dados = carregar_dados(tickers, start_date, end_date)
    if dados is None:
        return
    
    retorno_medio, cov_matrix = calcular_retorno_cov(dados)
    
    # Otimizar a carteira com a Teoria de Markowitz
    resultados = otimizar_carteira(retorno_medio, cov_matrix)

    # Plotar a Fronteira Eficiente
    plotar_resultados(resultados, retorno_medio, cov_matrix)
    
    # Exibir a carteira com maior retorno esperado
    carteira_maior_retorno(retorno_medio, cov_matrix)
    
    # Exibir a carteira informada (se fornecida)
    if pesos_informados is not None:
        carteira_informada(pesos_informados, retorno_medio, cov_matrix)

# Exemplo de uso
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB']  # Exemplos de tickers
start_date = '2015-01-01'
end_date = '2023-01-01'

# Peso da carteira informada (opcional)
pesos_informados = np.array([0.2, 0.2, 0.2, 0.2, 0.2])

rodar_analise(tickers, start_date, end_date, pesos_informados)

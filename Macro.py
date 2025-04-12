import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.covariance import LedoitWolf
import streamlit as st

st.set_page_config(layout="wide")

# Interface: entrada e configuração dos ativos
st.sidebar.title("Configuração da Carteira")

# Estado inicial padrão
default_tickers = {
    'AGRO3.SA': 0.10, 'BBAS3.SA': 0.012, 'BBSE3.SA': 0.065, 'BPAC11.SA': 0.106,
    'EGIE3.SA': 0.05, 'ITUB3.SA': 0.005, 'PRIO3.SA': 0.15, 'PSSA3.SA': 0.15,
    'SAPR3.SA': 0.067, 'SBSP3.SA': 0.04, 'VIVT3.SA': 0.064, 'WEGE3.SA': 0.15,
    'TOTS3.SA': 0.01, 'B3SA3.SA': 0.001, 'TAEE3.SA': 0.03
}

# Sessão para armazenar estado entre execuções
if 'tickers_dict' not in st.session_state:
    st.session_state.tickers_dict = default_tickers.copy()

# Campo para adicionar novo ticker
novo_ticker = st.sidebar.text_input("Adicionar ticker (ex: PETR4.SA)")
peso_novo = st.sidebar.number_input("Peso do novo ticker", min_value=0.0, max_value=1.0, step=0.01)

if st.sidebar.button("Adicionar Ticker"):
    if novo_ticker and novo_ticker not in st.session_state.tickers_dict:
        st.session_state.tickers_dict[novo_ticker] = peso_novo
    elif novo_ticker in st.session_state.tickers_dict:
        st.sidebar.warning("Ticker já incluído.")
    else:
        st.sidebar.warning("Digite um ticker válido.")

# Lista de tickers para remoção
tickers_para_remover = st.sidebar.multiselect("Remover Ticker(s)", list(st.session_state.tickers_dict.keys()))
if st.sidebar.button("Remover Selecionados"):
    for t in tickers_para_remover:
        st.session_state.tickers_dict.pop(t, None)

# Limites de alocação
st.sidebar.markdown("### Restrições de Alocação")
alocacao_min = st.sidebar.slider("Peso mínimo (%)", min_value=0, max_value=100, value=0) / 100
alocacao_max = st.sidebar.slider("Peso máximo (%)", min_value=1, max_value=100, value=25) / 100

start_date = '2017-01-01'
end_date = pd.Timestamp.today().strftime('%Y-%m-%d')

@st.cache_data
def baixar_dados(tickers, start, end, limite_faltas=0.1):
    try:
        df_raw = yf.download(list(tickers.keys()), start=start, end=end, group_by='ticker', auto_adjust=True)

        if isinstance(df_raw.columns, pd.MultiIndex):
            ativos_baixados = df_raw.columns.levels[0]
        else:
            ativos_baixados = df_raw.columns.tolist()

        ativos_esperados = list(tickers.keys())
        ativos_faltando = set(ativos_esperados) - set(ativos_baixados)

        if ativos_faltando:
            st.warning(f"Não foi possível baixar dados para: {', '.join(ativos_faltando)}")

        df = df_raw.stack(level=0).rename_axis(index=['Date', 'Ticker']).reset_index()
        df = df.pivot(index='Date', columns='Ticker', values='Close')

        df = df.loc[:, df.isnull().mean() < limite_faltas]
        df = df.fillna(method='ffill').fillna(method='bfill')
        df = df.dropna()

        if df.empty:
            st.error("Nenhum dado válido foi carregado após o tratamento.")
        else:
            st.success(f"{len(df.columns)} ativos carregados com sucesso.")

        return df

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

def calcular_retorno_cov(dados):
    retornos = dados.pct_change().dropna()
    retorno_medio = retornos.mean() * 252
    cov_matrix = LedoitWolf().fit(retornos).covariance_ * 252
    return retorno_medio, cov_matrix

def simular_carteiras(retorno_medio, cov_matrix, num_portfolios=500000, rf=0.0):
    n = len(retorno_medio)
    resultados = []
    pesos_lista = []
    for _ in range(num_portfolios):
        pesos = np.random.dirichlet(np.ones(n), size=1)[0]
        if np.any(pesos < alocacao_min) or np.any(pesos > alocacao_max):
            continue  # respeita limites
        retorno = np.dot(pesos, retorno_medio)
        risco = np.sqrt(np.dot(pesos.T, np.dot(cov_matrix, pesos)))
        sharpe = (retorno - rf) / risco if risco != 0 else 0
        resultados.append([retorno, risco, sharpe])
        pesos_lista.append(pesos)

    resultados = np.array(resultados)
    if resultados.size == 0:
        return None, None, None, None

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

    if resultados is None:
        st.error("Nenhuma carteira foi gerada com os limites de alocação definidos.")
        return

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

# Executar
rodar_analise(st.session_state.tickers_dict, start_date, end_date, st.session_state.tickers_dict)

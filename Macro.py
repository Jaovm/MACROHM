import streamlit as st
import pandas as pd
import numpy as np

def selecionar_cenario():
    st.header("1. Seleção do Cenário Macroeconômico")
    cenario = st.selectbox("Selecione o cenário macroeconômico:", [
        "Juros altos e inflação controlada",
        "Juros baixos e crescimento econômico",
        "Inflação alta e instabilidade política",
        "Estagflação",
        "Crescimento global acelerado"
    ])
    return cenario

def recomendar_setores(cenario):
    st.subheader("Setores recomendados")
    mapa = {
        "Juros altos e inflação controlada": ["Utilities", "Financeiro", "Consumo básico"],
        "Juros baixos e crescimento econômico": ["Tecnologia", "Consumo discricionário", "Indústria"],
        "Inflação alta e instabilidade política": ["Commodities", "Energia", "Utilities"],
        "Estagflação": ["Saúde", "Utilities"],
        "Crescimento global acelerado": ["Tecnologia", "Exportadoras"]
    }
    setores = mapa.get(cenario, [])
    st.write(", ".join(setores))
    return setores

def checklist_fundamentalista():
    st.header("2. Checklist Fundamentalista")
    st.write("Selecione os critérios mínimos desejados:")
    roic_min = st.slider("ROIC mínimo (%)", 0, 30, 10)
    roe_min = st.slider("ROE mínimo (%)", 0, 30, 10)
    margem_liquida_min = st.slider("Margem líquida mínima (%)", 0, 50, 10)
    divida_ebitda_max = st.slider("Dívida/EBITDA máxima", 0.0, 5.0, 2.0)
    return {
        "roic_min": roic_min,
        "roe_min": roe_min,
        "margem_liquida_min": margem_liquida_min,
        "divida_ebitda_max": divida_ebitda_max
    }

def simulador_otimizacao():
    st.header("3. Otimização da Carteira")
    st.write("Você pode inserir os tickers manualmente ou carregar por planilha.")
    tickers = st.text_input("Tickers separados por vírgula", "WEGE3.SA,EGIE3.SA,PRIO3.SA")
    aloc_min = st.slider("Alocação mínima por ativo (%)", 0, 10, 0)
    aloc_max = st.slider("Alocação máxima por ativo (%)", 10, 50, 20)
    num_simulacoes = st.number_input("Número de simulações Monte Carlo", min_value=1000, max_value=1000000, value=100000)
    st.write("Botões e execução da otimização serão implementados aqui.")

def resultados():
    st.header("4. Resultados da Carteira")
    st.write("Aqui serão exibidos:")
    st.markdown("- Retorno Esperado (%)")
    st.markdown("- Volatilidade Anual (%)")
    st.markdown("- Índice de Sharpe")
    st.markdown("- CAGR")
    st.markdown("- Composição da Carteira Otimizada")
    st.markdown("- Comparação com a Carteira Informada")

# Execução do app
st.title("Analisador Inteligente de Carteira")
cenario = selecionar_cenario()
setores = recomendar_setores(cenario)
criterios = checklist_fundamentalista()
simulador_otimizacao()
resultados()


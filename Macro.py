import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import euclidean_distances

# Exemplo de dados econômicos históricos (isso precisaria ser coletado de fontes como IBGE, Banco Central, etc.)
# Dados hipotéticos
economicos = {
    'Periodo': ['2019', '2020', '2021', '2022'],
    'Inflacao': [3.5, 3.2, 7.0, 9.0],
    'Taxa_juros': [6.5, 2.0, 3.5, 12.0],
    'PIB': [1.2, -3.5, 5.0, 1.8],
    'Desemprego': [11.9, 14.0, 13.0, 9.5],
}

df_economicos = pd.DataFrame(economicos)

# Cenário atual (dados hipotéticos)
cenario_atual = {
    'Inflacao': 8.0,
    'Taxa_juros': 10.0,
    'PIB': 1.5,
    'Desemprego': 10.0,
}

# Normalizar os dados econômicos
scaler = StandardScaler()
df_economicos_scaled = scaler.fit_transform(df_economicos[['Inflacao', 'Taxa_juros', 'PIB', 'Desemprego']])
cenario_atual_scaled = scaler.transform([[cenario_atual['Inflacao'], cenario_atual['Taxa_juros'], cenario_atual['PIB'], cenario_atual['Desemprego']]])

# Calcular a distância euclidiana entre o cenário atual e os cenários passados
distancias = euclidean_distances(df_economicos_scaled, cenario_atual_scaled)

# Encontrar o cenário mais semelhante
indice_mais_semelhante = np.argmin(distancias)

# Exibir o período mais semelhante
periodo_semelhante = df_economicos['Periodo'][indice_mais_semelhante]
st.write(f'O cenário atual é mais semelhante ao ano de {periodo_semelhante}')

# Agora, você pode usar essa informação para buscar os ativos ou setores que tiveram bom desempenho nesse período
# Aqui vamos apenas ilustrar com uma simples análise dos setores em cada ano (de forma simplificada)
ativos_recomendados = {
    '2019': ['WEGE3.SA', 'BBSE3.SA', 'TOTS3.SA'],
    '2020': ['PRIO3.SA', 'B3SA3.SA', 'VIVT3.SA'],
    '2021': ['TAEE3.SA', 'EGIE3.SA', 'ITUB3.SA'],
    '2022': ['VIVT3.SA', 'SAPR3.SA', 'PSSA3.SA'],
}

# Sugestão de ativos com base no cenário mais semelhante
ativos_sugeridos = ativos_recomendados[periodo_semelhante]

st.write(f'Com base no cenário econômico mais semelhante, recomendamos os seguintes ativos: {ativos_sugeridos}')

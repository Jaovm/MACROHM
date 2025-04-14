import streamlit as st
import pandas as pd
import requests
import datetime
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy

# Carregar o modelo do spaCy para processamento de texto
nlp = spacy.load("pt_core_news_sm")

# Função para buscar as notícias
def noticias_reais(api_key):
    url = f"https://gnews.io/api/v4/search?q=economia+brasil&lang=pt&country=br&max=5&token={api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        noticias = [article["title"] for article in data.get("articles", [])]
        return noticias
    except Exception as e:
        print(f"Erro ao buscar notícias: {e}")
        return []

# Função para realizar análise de sentimento nas notícias
def analisar_sentimentos(noticias):
    analyzer = SentimentIntensityAnalyzer()
    sentimentos = []
    for noticia in noticias:
        # Análise de sentimento com VADER
        sentimento = analyzer.polarity_scores(noticia)
        sentimentos.append({
            "noticia": noticia,
            "sentimento_negativo": sentimento["neg"],
            "sentimento_neutro": sentimento["neu"],
            "sentimento_positivo": sentimento["pos"],
            "sentimento_completo": sentimento["compound"]
        })
    return sentimentos

# Função para extrair tópicos de interesse das notícias
def extrair_topicos(noticias):
    topicos = {
        "inflação": ["inflação", "preços altos", "aumento de preços"],
        "taxas de juros": ["juros", "taxa de juros", "cobrança de juros", "aumento de juros"],
        "crescimento econômico": ["PIB", "crescimento", "expansão", "economia"],
        "desemprego": ["desemprego", "taxa de desemprego", "mercado de trabalho"],
        "setores em destaque": ["tecnologia", "energia", "imobiliário", "bancos", "consumo"]
    }

    resumo = {
        "inflação": [],
        "taxas de juros": [],
        "crescimento econômico": [],
        "desemprego": [],
        "setores em destaque": []
    }

    for noticia in noticias:
        for topico, palavras in topicos.items():
            if any(palavra in noticia.lower() for palavra in palavras):
                resumo[topico].append(noticia)

    return resumo

# Função para gerar o resumo macroeconômico
def gerar_resumo_macroeconomico(sentimentos, resumo_topicos):
    # Gerar resumo com base no sentimento geral e tópicos encontrados
    sentimento_geral = "Positivo" if sum([s["sentimento_completo"] for s in sentimentos]) > 0 else "Negativo"
    
    resumo = f"**Cenário Macroeconômico Atual:**\n"
    resumo += f"- **Sentimento geral das notícias**: {sentimento_geral}\n\n"
    
    for topico, noticias in resumo_topicos.items():
        if noticias:
            resumo += f"- **{topico.capitalize()}**:\n"
            for noticia in noticias:
                resumo += f"  - {noticia}\n"
    
    return resumo

# Função para obter preço atual e preço alvo do Yahoo Finance
def get_target_price_yfinance(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.history(period="1d")["Close"][0]
        target = stock.info.get("targetMeanPrice", None)
        return price, target
    except Exception as e:
        print(f"Erro ao buscar dados de {ticker}: {e}")
        return None, None

# Análise de desempenho histórico durante anos semelhantes ao cenário atual
def analise_historica_anos_similares(ticker, anos_semelhantes):
    try:
        stock = yf.Ticker(ticker)
        hoje = datetime.datetime.today().strftime('%Y-%m-%d')
        hist = stock.history(start="2017-01-01", end=hoje)["Close"]
        retornos = {}
        for ano in anos_semelhantes:
            dados_ano = hist[hist.index.year == ano]
            if not dados_ano.empty:
                retorno = dados_ano.pct_change().sum() * 100
                retornos[ano] = retorno
        media = np.mean(list(retornos.values())) if retornos else None
        return media
    except Exception as e:
        print(f"Erro ao calcular retorno histórico para {ticker}: {e}")
        return None

# Função para identificar anos semelhantes com base em dados econômicos
@st.cache_data
def obter_anos_similares():
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados?formato=json"
    url_selic = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.4189/dados?formato=json"

    def carregar_serie(url):
        r = requests.get(url)
        df = pd.DataFrame(r.json())
        df['data'] = pd.to_datetime(df['data'], dayfirst=True)
        df['ano'] = df['data'].dt.year
        df['valor'] = pd.to_numeric(df['valor'].str.replace(',', '.'), errors='coerce')
        return df.groupby('ano')['valor'].mean().dropna()

    ipca = carregar_serie(url)
    selic = carregar_serie(url_selic)
    df = pd.DataFrame({'ipca': ipca, 'selic': selic}).dropna()

    dados_atuais = df.iloc[-1].values.reshape(1, -1)
    historico = df.iloc[:-1]

    scaler = StandardScaler()
    dados_normalizados = scaler.fit_transform(df)
    atual_normalizado = dados_normalizados[-1].reshape(1, -1)
    historico_normalizado = dados_normalizados[:-1]

    similaridades = cosine_similarity(atual_normalizado, historico_normalizado)[0]
    anos_ordenados = historico.index[np.argsort(similaridades)[-2:][::-1]].tolist()
    return anos_ordenados

# Função principal para integração com o Streamlit
def main():
    st.set_page_config(page_title="Análise de Cenário Macroeconômico", layout="wide")
    st.title("📊 Análise de Cenário Macroeconômico Atual")

    st.markdown("""
    Este app analisa notícias econômicas recentes e gera um resumo do cenário macroeconômico atual.
    A análise inclui a identificação de tópicos como inflação, taxas de juros, PIB, desemprego e setores em destaque.
    """)

    # Obter notícias
    api_key = st.secrets["GNEWS_API_KEY"] if "GNEWS_API_KEY" in st.secrets else "f81e45d8e741c24dfe4971f5403f5a32"
    noticias = noticias_reais(api_key)

    if noticias:
        st.markdown("**Notícias Recentes:**")
        for noticia in noticias:
            st.markdown(f"- {noticia}")

        # Analisar sentimentos das notícias
        sentimentos = analisar_sentimentos(noticias)

        # Extrair tópicos relevantes das notícias
        resumo_topicos = extrair_topicos(noticias)

        # Gerar o resumo macroeconômico
        resumo_macroeconomico = gerar_resumo_macroeconomico(sentimentos, resumo_topicos)

        st.markdown("**Resumo do Cenário Macroeconômico Atual:**")
        st.markdown(resumo_macroeconomico)
    else:
        st.write("Nenhuma notícia encontrada.")

    # O restante do seu código original continua aqui...
    # Incluindo a análise de alocação de ativos e o upload da carteira.

# Rodar o app
if __name__ == "__main__":
    main()

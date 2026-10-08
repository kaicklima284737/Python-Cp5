import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")
TIPOS = {"Todos": None, "Filmes": "filme", "Séries": "serie"}
MIN_VOTOS = 50

st.set_page_config(page_title="Filmes e Séries - TMDB", layout="wide")


def chamar_api(caminho, params=None):
    try:
        resposta = requests.get(f"{API_URL}{caminho}", params=params, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
    except requests.RequestException:
        st.error(f"Não foi possível acessar a API em {API_URL}. Ela está rodando?")
        st.stop()


def carregar_registros(caminho, params):
    registros = []
    for pagina in range(1, 6):  # até 500 registros
        dados = chamar_api(caminho, {**params, "pagina": pagina, "limite": 100})
        registros += dados["resultados"]
        if len(registros) >= dados["total"]:
            break
    return registros


st.title("🎬 Filmes e Séries Populares (TMDB)")

# ---------- Filtros ----------
st.sidebar.header("Filtros")
busca = st.sidebar.text_input("Pesquisar título ou sinopse")
tipo_nome = st.sidebar.selectbox("Tipo", list(TIPOS))
genero = st.sidebar.selectbox("Gênero", ["Todos"] + chamar_api("/generos"))
nota_min = st.sidebar.slider("Nota mínima", 0.0, 10.0, 0.0, 0.5)

filtros = {}
if TIPOS[tipo_nome]:
    filtros["tipo"] = TIPOS[tipo_nome]
if genero != "Todos":
    filtros["genero"] = genero
if nota_min > 0:
    filtros["nota_min"] = nota_min

# ---------- Indicadores ----------
stats = chamar_api("/estatisticas", filtros)
if stats["total_registros"] == 0:
    st.info("Nenhum registro encontrado. Execute o crawler ou ajuste os filtros.")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de registros", stats["total_registros"])
col2.metric("Média das avaliações", stats["media_notas"])
if stats["mais_popular"]:
    col3.metric("Mais popular", stats["mais_popular"]["titulo"])
if stats["maior_nota"]:
    col4.metric(
        "Maior avaliação",
        stats["maior_nota"]["titulo"],
        f"nota {stats['maior_nota']['nota_media']}",
        delta_color="off",
    )

# ---------- Dados filtrados ----------
if busca:
    registros = carregar_registros("/buscar", {**filtros, "q": busca})
else:
    registros = carregar_registros("/filmes", filtros)

if not registros:
    st.info("Nenhum resultado para a pesquisa.")
    st.stop()

df = pd.DataFrame(registros)

# ---------- Gráficos ----------
graf1, graf2 = st.columns(2)

top_pop = df.nlargest(10, "popularidade")
fig = px.bar(top_pop, x="popularidade", y="titulo", orientation="h", title="Top 10 por popularidade")
fig.update_layout(yaxis={"categoryorder": "total ascending", "title": ""})
graf1.plotly_chart(fig)

top_notas = df[df["total_votos"] >= MIN_VOTOS].nlargest(10, "nota_media")
fig = px.bar(
    top_notas,
    x="nota_media",
    y="titulo",
    orientation="h",
    title=f"Top 10 por avaliação (mín. {MIN_VOTOS} votos)",
)
fig.update_layout(yaxis={"categoryorder": "total ascending", "title": ""})
graf2.plotly_chart(fig)

generos_df = pd.DataFrame(list(stats["por_genero"].items()), columns=["genero", "quantidade"])
fig = px.bar(generos_df.head(15), x="genero", y="quantidade", title="Distribuição por gênero")
st.plotly_chart(fig)

# ---------- Tabela ----------
st.subheader(f"Registros ({len(df)})")
tabela = df.assign(generos=df["generos"].apply(", ".join))[
    ["poster_url", "titulo", "tipo", "data_lancamento", "nota_media", "total_votos", "popularidade", "generos"]
].rename(
    columns={
        "poster_url": "Pôster",
        "titulo": "Título",
        "tipo": "Tipo",
        "data_lancamento": "Lançamento",
        "nota_media": "Nota",
        "total_votos": "Votos",
        "popularidade": "Popularidade",
        "generos": "Gêneros",
    }
)
st.dataframe(tabela, column_config={"Pôster": st.column_config.ImageColumn("Pôster")}, hide_index=True)

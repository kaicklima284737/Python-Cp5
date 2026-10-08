import html
import os

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from busca import buscar_titulo, quicksort
from dotenv import load_dotenv

# O arquivo de streamlit parece grande, mas em sua maioria,
# É organização visual. aprox. 140 linhas são estilização.
load_dotenv()
API_URL = os.getenv("API_URL", "http://localhost:8000")
TIPOS = {"Todos": None, "Filmes": "filme", "Séries": "serie"}
MIN_VOTOS = 50

FONTE = "Poppins, sans-serif"
ESCALA = ["#80DEEA", "#26C6DA", "#00838F", "#006064"]  # degradê dos gráficos

st.set_page_config(page_title="Filmes e Séries - TMDB", page_icon="🎬", layout="wide")

ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

/* ---------- Animações ---------- */
@keyframes subir { from { opacity: 0; transform: translateY(18px); } to { opacity: 1; transform: translateY(0); } }
@keyframes descer { from { opacity: 0; transform: translateY(-18px); } to { opacity: 1; transform: translateY(0); } }
@keyframes brilho { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

/* ---------- Fundo ---------- */
.stApp {
    background: linear-gradient(135deg, #4DD0E1 0%, #26C6DA 55%, #80DEEA 100%);
    background-attachment: fixed;
}
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
.block-container { padding-top: 2rem; max-width: 1300px; }

/* ---------- Texto: tudo em preto ---------- */
.stApp, .stApp * { color: #000000; }
h1, h2, h3, h4, h5, h6, p, label, li, button, input, textarea,
.hero, [data-testid="stMetric"] * { font-family: 'Poppins', sans-serif; }
h3 { font-weight: 700; }
input, textarea, [data-baseweb="select"] * { color: #000000 !important; }

/* Remove o indicador "Running..." padrão */
[data-testid="stStatusWidget"] { display: none; }

/* ---------- Cabeçalho ---------- */
.hero {
    background: linear-gradient(120deg, #FFFFFF, #E0F7FA, #FFFFFF);
    background-size: 200% 200%;
    border-left: 8px solid #006064;
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 10px 30px rgba(0, 96, 100, 0.25);
    animation: descer .7s ease both, brilho 8s ease infinite;
}
.hero h1 { margin: 0; font-size: 2.1rem; font-weight: 700; }
.hero p { margin: .3rem 0 0; font-size: .95rem; opacity: .75; }

/* ---------- Barra lateral ---------- */
[data-testid="stSidebar"] {
    background: #FFFFFF;
    border-right: 5px solid #006064;
    box-shadow: 4px 0 20px rgba(0, 96, 100, 0.2);
}
[data-baseweb="input"], [data-baseweb="select"] > div { border-radius: 12px !important; }

/* ---------- Seções (radio vira botões) ---------- */
div[role="radiogroup"] { gap: .6rem; flex-wrap: wrap; }
div[role="radiogroup"] > label {
    background: rgba(255, 255, 255, 0.45);
    padding: .55rem 1.3rem;
    border-radius: 999px;
    border: 2px solid transparent;
    cursor: pointer;
    transition: all .25s ease;
}
div[role="radiogroup"] > label:hover { background: rgba(255, 255, 255, 0.85); transform: translateY(-2px); }
div[role="radiogroup"] > label > div:first-child { display: none; }
div[role="radiogroup"] > label:has(input:checked) {
    background: #FFFFFF;
    border-color: #006064;
    font-weight: 700;
    box-shadow: 0 6px 16px rgba(0, 96, 100, 0.3);
}

/* ---------- Indicadores ---------- */
[data-testid="stMetric"] {
    background: #FFFFFF;
    padding: 16px 20px;
    border-radius: 16px;
    border-left: 6px solid #006064;
    box-shadow: 0 6px 18px rgba(0, 96, 100, 0.18);
    transition: transform .25s ease, box-shadow .25s ease;
    animation: subir .6s ease both;
}
[data-testid="stMetric"]:hover { transform: translateY(-5px); box-shadow: 0 14px 28px rgba(0, 96, 100, 0.3); }
[data-testid="stMetricLabel"] * { font-weight: 600; opacity: .75; }
[data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
    font-size: 1.6rem !important;
    font-weight: 700;
    line-height: 1.2;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}
[data-testid="stColumn"]:nth-child(2) [data-testid="stMetric"],
[data-testid="column"]:nth-child(2) [data-testid="stMetric"] { animation-delay: .1s; }
[data-testid="stColumn"]:nth-child(3) [data-testid="stMetric"],
[data-testid="column"]:nth-child(3) [data-testid="stMetric"] { animation-delay: .2s; }
[data-testid="stColumn"]:nth-child(4) [data-testid="stMetric"],
[data-testid="column"]:nth-child(4) [data-testid="stMetric"] { animation-delay: .3s; }

/* ---------- Gráficos, tabelas e imagens ---------- */
[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border-radius: 18px;
    padding: 10px;
    box-shadow: 0 8px 24px rgba(0, 96, 100, 0.18);
    transition: transform .25s ease, box-shadow .25s ease;
    animation: subir .7s ease both;
}
[data-testid="stPlotlyChart"]:hover { transform: translateY(-4px); box-shadow: 0 16px 32px rgba(0, 96, 100, 0.28); }
[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0, 96, 100, 0.18);
    animation: subir .8s ease both;
}
[data-testid="stImage"] img {
    border-radius: 16px;
    box-shadow: 0 10px 26px rgba(0, 96, 100, 0.35);
    transition: transform .35s ease;
}
[data-testid="stImage"] img:hover { transform: scale(1.04); }
[data-testid="stAlert"] { border-radius: 14px; box-shadow: 0 4px 14px rgba(0, 96, 100, 0.15); }

/* ---------- Etiquetas de gênero ---------- */
.chip {
    display: inline-block;
    background: #FFFFFF;
    border: 2px solid #00ACC1;
    padding: .2rem .85rem;
    margin: 0 .4rem .5rem 0;
    border-radius: 999px;
    font-size: .85rem;
    font-weight: 500;
    transition: all .2s ease;
}
.chip:hover { background: #B2EBF2; transform: translateY(-2px); }
</style>
"""
st.markdown(ESTILO, unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def _get_json(caminho, params_tuple):
    resposta = requests.get(f"{API_URL}{caminho}", params=dict(params_tuple), timeout=10)
    resposta.raise_for_status()
    return resposta.json()


def chamar_api(caminho, params=None):
    try:
        return _get_json(caminho, tuple(sorted((params or {}).items())))
    except requests.RequestException:
        st.error(f"Não foi possível acessar a API em {API_URL}. Ela está rodando?")
        st.stop()


def carregar_registros(caminho, params, maximo):
    limite = min(maximo, 500)
    registros = []
    for pagina in range(1, -(-maximo // limite) + 1):
        dados = chamar_api(caminho, {**params, "pagina": pagina, "limite": limite})
        registros += dados["resultados"]
        if len(registros) >= dados["total"]:
            break
    return registros[:maximo]


def formatar_dolar(valor):
    return f"US$ {valor:,.0f}".replace(",", ".")


def formatar_data(valor):
    return str(valor)[:16].replace("T", " ") if valor else "-"


def estilizar(fig):
    fig.update_layout(
        font_family=FONTE,
        font_color="#000000",
        title_font_size=18,
        title_font_color="#000000",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=30, t=60, b=10),
        coloraxis_showscale=False,
        hoverlabel=dict(bgcolor="#FFFFFF", font_color="#000000", font_family=FONTE),
    )
    fig.update_xaxes(gridcolor="rgba(0,96,100,0.12)", zeroline=False)
    fig.update_yaxes(gridcolor="rgba(0,96,100,0.12)", zeroline=False)
    try:
        fig.update_layout(barcornerradius=8)  # barras arredondadas (Plotly recente)
    except ValueError:
        pass
    return fig


def mostrar_grafico(fig):
    st.plotly_chart(fig, theme=None)


def barras_horizontais(df, x, titulo, formato=None):
    fig = px.bar(
        df, x=x, y="titulo", orientation="h", title=titulo,
        color=x, color_continuous_scale=ESCALA,
        template="plotly_white", text_auto=formato or False,
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending", "title": ""}, xaxis_title=None)
    if formato:
        fig.update_traces(textposition="outside", cliponaxis=False)
    return estilizar(fig)


# ---------- Aba 1: visão geral ----------
def mostrar_visao_geral(stats, df):
    if stats["total_registros"] == 0:
        st.info("Nenhum registro encontrado. Execute o crawler ou ajuste os filtros.")
        return

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

    if df.empty:
        st.info("Nenhum resultado para a pesquisa.")
        return

    st.write("")
    graf1, graf2 = st.columns(2)
    with graf1:
        mostrar_grafico(
            barras_horizontais(df.nlargest(10, "popularidade"), "popularidade", "Top 10 por popularidade", ".0f")
        )
    with graf2:
        top_notas = df[df["total_votos"] >= MIN_VOTOS].nlargest(10, "nota_media")
        mostrar_grafico(
            barras_horizontais(top_notas, "nota_media", f"Top 10 por avaliação (mín. {MIN_VOTOS} votos)", ".1f")
        )

    st.write("")
    generos_df = pd.DataFrame(list(stats["por_genero"].items()), columns=["genero", "quantidade"])
    fig = px.bar(
        generos_df.head(15), x="genero", y="quantidade", title="Distribuição por gênero",
        color="quantidade", color_continuous_scale=ESCALA,
        template="plotly_white", text_auto=True,
    )
    fig.update_layout(xaxis_title=None, yaxis_title=None, xaxis_tickangle=-35)
    fig.update_traces(textposition="outside", cliponaxis=False)
    mostrar_grafico(estilizar(fig))

    st.write("")
    st.subheader(f"Registros exibidos: {len(df)} (ordenados por popularidade)")
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


@st.cache_data(ttl=300, show_spinner=False)
def ordenar_por_titulo(registros):
    return quicksort(list(registros), lambda r: r["titulo"].lower())


# ---------- Aba 2: detalhes de um filme/série ----------
def mostrar_detalhes(df):
    if df.empty:
        st.info("Nenhum registro para exibir. Ajuste os filtros.")
        return

    # Quicksort por título (sem diferenciar maiúsculas)
    ordenados = ordenar_por_titulo(df.to_dict("records"))

    termo = st.text_input("Pesquisar filme ou série", key="busca_detalhes")
    resultados = ordenados
    if termo:
        resultados = buscar_titulo(ordenados, termo)  # busca binária
        if resultados:
            st.caption("Título exato encontrado por busca binária.")
        else:
            parte = termo.strip().lower()
            resultados = [r for r in ordenados if parte in r["titulo"].lower()]
            st.caption("Sem título exato. Mostrando títulos que contêm o texto.")

    if not resultados:
        st.info("Nenhum título encontrado para essa pesquisa.")
        return

    # O ID fica só nas chaves internas. O usuário vê título, ano e tipo.
    nomes = {
        (r["tmdb_id"], r["tipo"]): f"{r['titulo']} ({str(r['data_lancamento'] or '-')[:4]}) · {r['tipo']}"
        for r in resultados
    }
    tmdb_id, tipo = st.selectbox(
        "Escolha um filme ou série",
        list(nomes),
        format_func=lambda chave: nomes[chave],
    )
    with st.spinner("Carregando detalhes..."):
        item = chamar_api(f"/filmes/{tmdb_id}", {"tipo": tipo})

    st.write("")
    col_poster, col_info = st.columns([1, 2])
    if item["poster_url"]:
        col_poster.image(item["poster_url"])
    else:
        col_poster.caption("Sem pôster")

    col_info.header(item["titulo"])
    col_info.caption(f"{item['tipo'].capitalize()} · Lançamento: {item['data_lancamento'] or '-'}")

    chips = "".join(f'<span class="chip">{html.escape(g)}</span>' for g in item["generos"])
    col_info.markdown(chips or "-", unsafe_allow_html=True)

    m1, m2, m3 = col_info.columns(3)
    m1.metric("Nota média", item["nota_media"])
    m2.metric("Votos", item["total_votos"])
    m3.metric("Popularidade", item["popularidade"])

    col_info.subheader("Sinopse")
    col_info.write(item["sinopse"] or "Sem sinopse.")

    col_info.subheader("Dados do registro")
    col_info.write(f"**Tipo:** {item['tipo']}")
    col_info.write(f"**Idioma original:** {item['idioma_original'] or '-'}")
    col_info.write(f"**URL do pôster:** {item['poster_url'] or '-'}")
    col_info.write(f"**Primeira coleta:** {formatar_data(item.get('primeira_coleta'))}")
    col_info.write(f"**Última coleta:** {formatar_data(item['data_coleta'])}")
    col_info.write(f"**Origem:** {item['origem']}")


# ---------- Aba 3: bilheterias ----------
def mostrar_bilheterias():
    st.subheader("Top 10 maiores bilheterias")
    with st.spinner("Carregando bilheterias..."):
        dados = chamar_api("/bilheterias", {"limite": 10})
    if not dados:
        st.info("Sem dados de bilheteria. Execute o crawler.")
        return

    df = pd.DataFrame(dados)
    mostrar_grafico(barras_horizontais(df, "receita", "Receita mundial (US$)"))

    st.write("")
    tabela = pd.DataFrame(
        {
            "Pôster": df["poster_url"],
            "Título": df["titulo"],
            "Lançamento": df["data_lancamento"],
            "Receita": df["receita"].apply(formatar_dolar),
            "Orçamento": df["orcamento"].apply(formatar_dolar),
            "Lucro": df["lucro"].apply(formatar_dolar),
            "Nota": df["nota_media"],
        }
    )
    st.dataframe(tabela, column_config={"Pôster": st.column_config.ImageColumn("Pôster")}, hide_index=True)
    st.caption("Valores em dólares, informados pelo TMDB. Podem estar incompletos.")


# ---------- Página ----------
st.markdown(
    '<div class="hero"><h1>🎬 Filmes e Séries Populares</h1>'
    "<p>Dados do TMDB coletados, armazenados no MongoDB e servidos pela FastAPI</p></div>",
    unsafe_allow_html=True,
)

st.sidebar.header("Filtros")
busca = st.sidebar.text_input("Pesquisar título ou sinopse")
tipo_nome = st.sidebar.selectbox("Tipo", list(TIPOS))
genero = st.sidebar.selectbox("Gênero", ["Todos"] + chamar_api("/generos"))
nota_min = st.sidebar.slider("Nota mínima", 0.0, 10.0, 0.0, 0.5)
maximo = st.sidebar.selectbox("Máx. registros na tabela e gráficos", [100, 500, 1000, 2000, 5000], index=1)

filtros = {}
if TIPOS[tipo_nome]:
    filtros["tipo"] = TIPOS[tipo_nome]
if genero != "Todos":
    filtros["genero"] = genero
if nota_min > 0:
    filtros["nota_min"] = nota_min

aba = st.radio(
    "Seção",
    ["📊 Visão geral", "🎞️ Detalhes do filme", "💰 Bilheterias"],
    horizontal=True,
    label_visibility="collapsed",
)

if aba == "💰 Bilheterias":
    mostrar_bilheterias()
else:
    with st.spinner("Carregando dados..."):
        stats = chamar_api("/estatisticas", filtros)
        if busca:
            registros = carregar_registros("/buscar", {**filtros, "q": busca}, maximo)
        else:
            registros = carregar_registros("/filmes", filtros, maximo)
        df = pd.DataFrame(registros)

    if aba == "📊 Visão geral":
        mostrar_visao_geral(stats, df)
    else:
        mostrar_detalhes(df)

st.caption("This product uses the TMDB API but is not endorsed or certified by TMDB.")
import re
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

from database.mongodb import get_bilheterias, get_titulos
from models.schemas import Bilheteria, Estatisticas, ListaTitulos, Titulo

MIN_VOTOS_MAIOR_NOTA = 50  # evita que títulos com poucos votos dominem o ranking

app = FastAPI(
    title="API de Filmes e Séries (TMDB)",
    description="Dados coletados do TMDB e armazenados no MongoDB.",
    version="1.0.0",
)

Tipo = Literal["filme", "serie"]
CampoOrdem = Literal["popularidade", "nota_media", "total_votos", "titulo", "data_lancamento"]


@app.exception_handler(PyMongoError)
def erro_mongo(request, erro):
    return JSONResponse(status_code=503, content={"detail": "Erro ao acessar o banco de dados"})


def montar_filtro(tipo=None, genero=None, nota_min=None, ano=None):
    filtro = {}
    if tipo:
        filtro["tipo"] = tipo
    if genero:
        filtro["generos"] = genero
    if nota_min is not None:
        filtro["nota_media"] = {"$gte": nota_min}
    if ano:
        filtro["data_lancamento"] = {"$regex": f"^{ano}"}
    return filtro


def consultar(filtro, ordenar_por, ordem, pagina, limite):
    colecao = get_titulos()
    total = colecao.count_documents(filtro)
    direcao = ASCENDING if ordem == "asc" else DESCENDING
    cursor = (
        colecao.find(filtro, {"_id": 0})
        .sort([(ordenar_por, direcao), ("tmdb_id", ASCENDING)])
        .skip((pagina - 1) * limite)
        .limit(limite)
    )
    return {"total": total, "pagina": pagina, "limite": limite, "resultados": list(cursor)}


@app.get("/", include_in_schema=False)
def inicio():
    return RedirectResponse("/docs")


@app.get("/filmes", response_model=ListaTitulos, summary="Lista filmes e séries")
def listar(
    tipo: Optional[Tipo] = None,
    genero: Optional[str] = None,
    nota_min: Optional[float] = Query(None, ge=0, le=10),
    ano: Optional[int] = Query(None, ge=1888, le=2100),
    ordenar_por: CampoOrdem = "popularidade",
    ordem: Literal["asc", "desc"] = "desc",
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=500),
):
    filtro = montar_filtro(tipo, genero, nota_min, ano)
    return consultar(filtro, ordenar_por, ordem, pagina, limite)


@app.get("/filmes/{tmdb_id}", response_model=Titulo, summary="Consulta um registro pelo ID do TMDB")
def detalhe(tmdb_id: int, tipo: Optional[Tipo] = None):
    filtro = {"tmdb_id": tmdb_id}
    if tipo:
        filtro["tipo"] = tipo
    registro = get_titulos().find_one(filtro, {"_id": 0})
    if not registro:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    return registro


@app.get("/buscar", response_model=ListaTitulos, summary="Busca por texto no título e na sinopse")
def buscar(
    q: str = Query(..., min_length=1),
    tipo: Optional[Tipo] = None,
    genero: Optional[str] = None,
    nota_min: Optional[float] = Query(None, ge=0, le=10),
    ano: Optional[int] = Query(None, ge=1888, le=2100),
    ordenar_por: CampoOrdem = "popularidade",
    ordem: Literal["asc", "desc"] = "desc",
    pagina: int = Query(1, ge=1),
    limite: int = Query(20, ge=1, le=500),
):
    filtro = montar_filtro(tipo, genero, nota_min, ano)
    texto = {"$regex": re.escape(q), "$options": "i"}
    filtro["$or"] = [{"titulo": texto}, {"sinopse": texto}]
    return consultar(filtro, ordenar_por, ordem, pagina, limite)


@app.get("/generos", response_model=list[str], summary="Lista os gêneros disponíveis")
def generos():
    return sorted(g for g in get_titulos().distinct("generos") if g)


def media_das_notas(filtro):
    # Só considera títulos que têm votos
    pipeline = [
        {"$match": {**filtro, "total_votos": {"$gt": 0}}},
        {"$group": {"_id": None, "media": {"$avg": "$nota_media"}}},
    ]
    resultado = list(get_titulos().aggregate(pipeline))
    return round(resultado[0]["media"], 2) if resultado else 0.0


@app.get("/estatisticas", response_model=Estatisticas, summary="Estatísticas gerais")
def estatisticas(
    tipo: Optional[Tipo] = None,
    genero: Optional[str] = None,
    nota_min: Optional[float] = Query(None, ge=0, le=10),
):
    colecao = get_titulos()
    filtro = montar_filtro(tipo, genero, nota_min)

    por_tipo = colecao.aggregate(
        [{"$match": filtro}, {"$group": {"_id": "$tipo", "qtd": {"$sum": 1}}}]
    )
    por_genero = colecao.aggregate(
        [
            {"$match": filtro},
            {"$unwind": "$generos"},
            {"$match": {"generos": {"$ne": None}}},
            {"$group": {"_id": "$generos", "qtd": {"$sum": 1}}},
            {"$sort": {"qtd": -1}},
        ]
    )

    return {
        "total_registros": colecao.count_documents(filtro),
        "media_notas": media_das_notas(filtro),
        "mais_popular": colecao.find_one(filtro, {"_id": 0}, sort=[("popularidade", DESCENDING)]),
        "maior_nota": colecao.find_one(
            {**filtro, "total_votos": {"$gte": MIN_VOTOS_MAIOR_NOTA}},
            {"_id": 0},
            sort=[("nota_media", DESCENDING), ("total_votos", DESCENDING)],
        ),
        "por_tipo": {item["_id"]: item["qtd"] for item in por_tipo if item["_id"]},
        "por_genero": {item["_id"]: item["qtd"] for item in por_genero},
    }


@app.get("/bilheterias", response_model=list[Bilheteria], summary="Maiores bilheterias")
def bilheterias(limite: int = Query(10, ge=1, le=50)):
    cursor = get_bilheterias().find({}, {"_id": 0}).sort("receita", DESCENDING).limit(limite)
    return list(cursor)
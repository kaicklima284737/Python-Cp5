import argparse
import sys
import time
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from pymongo.errors import PyMongoError

from config import TMDB_IMAGE_URL
from crawler import tmdb
from database import mongodb

ORIGEM = "TMDB API (https://api.themoviedb.org/3)"
LIMITE_PAGINAS_TMDB = 500  


def limpar_texto(texto):
    """Remove HTML e espaços extras."""
    if not texto:
        return ""
    texto = BeautifulSoup(texto, "html.parser").get_text(" ")
    return " ".join(texto.split())


def tratar_item(item, tipo, generos, agora):
    """Converte um item bruto do TMDB no documento que vai ao MongoDB."""
    campo_titulo = "title" if tipo == "filme" else "name"
    campo_data = "release_date" if tipo == "filme" else "first_air_date"

    titulo = limpar_texto(item.get(campo_titulo))
    if not item.get("id") or not titulo:
        return None

    poster = item.get("poster_path")
    return {
        "tmdb_id": item["id"],
        "titulo": titulo,
        "tipo": tipo,
        "sinopse": limpar_texto(item.get("overview")),
        "data_lancamento": item.get(campo_data) or None,
        "nota_media": round(float(item.get("vote_average") or 0), 1),
        "total_votos": int(item.get("vote_count") or 0),
        "popularidade": round(float(item.get("popularity") or 0), 2),
        "idioma_original": item.get("original_language"),
        "generos": [generos[g] for g in item.get("genre_ids", []) if g in generos],
        "poster_url": f"{TMDB_IMAGE_URL}{poster}" if poster else None,
        "data_coleta": agora,
        "origem": ORIGEM,
    }

def tratar_bilheteria(detalhes, agora):
    receita = int(detalhes.get("revenue") or 0)
    orcamento = int(detalhes.get("budget") or 0)
    poster = detalhes.get("poster_path")
    return {
        "tmdb_id": detalhes["id"],
        "titulo": limpar_texto(detalhes.get("title")),
        "data_lancamento": detalhes.get("release_date") or None,
        "receita": receita,
        "orcamento": orcamento,
        "lucro": receita - orcamento,
        "nota_media": round(float(detalhes.get("vote_average") or 0), 1),
        "poster_url": f"{TMDB_IMAGE_URL}{poster}" if poster else None,
        "data_coleta": agora,
        "origem": ORIGEM,
    }


def coletar_bilheterias(agora, quantidade=20):
    salvos = 0
    for bruto in tmdb.buscar_maiores_bilheterias()[:quantidade]:
        try:
            detalhes = tmdb.buscar_detalhes_filme(bruto["id"])
        except tmdb.TmdbErro:
            continue
        doc = tratar_bilheteria(detalhes, agora)
        if doc["receita"] > 0:
            mongodb.salvar_bilheteria(doc)
            salvos += 1
        time.sleep(0.05)
    return salvos


def coletar_tipo(tipo, paginas, agora):
    """Coleta página por página e salva cada página na hora. paginas=0 -> todas."""
    generos = tmdb.buscar_generos(tipo)
    vistos = set()  # evita duplicados dentro da mesma coleta
    total = novos = 0
    pagina = 1
    ultima = paginas

    while True:
        dados = tmdb.buscar_populares(tipo, pagina)
        if pagina == 1:
            disponiveis = min(dados["total_pages"], LIMITE_PAGINAS_TMDB)
            ultima = min(paginas, disponiveis) if paginas else disponiveis

        itens = []
        for bruto in dados["results"]:
            item = tratar_item(bruto, tipo, generos, agora)
            if item and item["tmdb_id"] not in vistos:
                vistos.add(item["tmdb_id"])
                itens.append(item)

        novos += mongodb.salvar_lote(itens)
        total += len(itens)

        if pagina % 25 == 0 or pagina == ultima:
            print(f"{tipo}: página {pagina}/{ultima} ({total} registros)")
        if pagina >= ultima:
            return total, novos
        pagina += 1
        time.sleep(0.05)  # respeita o limite de requisições do TMDB


def main():
    parser = argparse.ArgumentParser(description="Coleta filmes e séries populares do TMDB")
    parser.add_argument(
        "--paginas",
        type=int,
        default=0,
        help="páginas por tipo (20 itens cada). 0 = todas (máx. 500)",
    )
    args = parser.parse_args()
    if args.paginas < 0:
        parser.error("--paginas não pode ser negativo")

    try:
        mongodb.testar_conexao()
        mongodb.criar_indices()
    except PyMongoError:
        print("Erro: não foi possível conectar ao MongoDB.")
        sys.exit(1)

    agora = datetime.now(timezone.utc)
    houve_erro = False

    for tipo in ("filme", "serie"):
        try:
            total, novos = coletar_tipo(tipo, args.paginas, agora)
        except tmdb.TmdbErro as erro:
            print(f"Erro ao coletar {tipo}: {erro}")
            houve_erro = True
            continue
        except PyMongoError:
            print("Erro ao salvar no MongoDB.")
            sys.exit(1)
        print(f"{tipo}: {total} coletados, {novos} novos, {total - novos} atualizados")

    try:
        print(f"bilheterias: {coletar_bilheterias(agora)} salvas")
    except tmdb.TmdbErro as erro:
        print(f"Erro ao coletar bilheterias: {erro}")
        houve_erro = True
    except PyMongoError:
        print("Erro ao salvar bilheterias no MongoDB.")
        sys.exit(1)

    if houve_erro:
        sys.exit(1)


if __name__ == "__main__":
    main()
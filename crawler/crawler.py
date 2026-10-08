import argparse
import sys
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from pymongo.errors import PyMongoError

from config import TMDB_IMAGE_URL
from crawler import tmdb
from database import mongodb

ORIGEM = "TMDB API (https://api.themoviedb.org/3)"


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


def coletar_tipo(tipo, paginas, agora):
    generos = tmdb.buscar_generos(tipo)
    itens = {}  # chave = id, evita duplicados dentro da mesma coleta
    for pagina in range(1, paginas + 1):
        for bruto in tmdb.buscar_populares(tipo, pagina):
            item = tratar_item(bruto, tipo, generos, agora)
            if item:
                itens[item["tmdb_id"]] = item
    return list(itens.values())


def main():
    parser = argparse.ArgumentParser(description="Coleta filmes e séries populares do TMDB")
    parser.add_argument("--paginas", type=int, default=3, help="páginas por tipo (20 itens cada)")
    args = parser.parse_args()
    if args.paginas < 1:
        parser.error("--paginas deve ser maior que 0")

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
            itens = coletar_tipo(tipo, args.paginas, agora)
            novos = sum(1 for item in itens if mongodb.salvar_titulo(item))
        except tmdb.TmdbErro as erro:
            print(f"Erro ao coletar {tipo}: {erro}")
            houve_erro = True
            continue
        except PyMongoError:
            print("Erro ao salvar no MongoDB.")
            sys.exit(1)
        print(f"{tipo}: {len(itens)} coletados, {novos} novos, {len(itens) - novos} atualizados")

    if houve_erro:
        sys.exit(1)


if __name__ == "__main__":
    main()

import time

import requests

from config import IDIOMA, TMDB_API_KEY, TMDB_BASE_URL

CAMINHOS = {"filme": "movie", "serie": "tv"}


class TmdbErro(Exception):
    pass


def _get(caminho, params=None):
    if not TMDB_API_KEY:
        raise TmdbErro("TMDB_API_KEY não definida no .env")

    params = {"api_key": TMDB_API_KEY, "language": IDIOMA, **(params or {})}
    try:
        for _ in range(3):
            resposta = requests.get(f"{TMDB_BASE_URL}{caminho}", params=params, timeout=10)
            if resposta.status_code == 429:  # limite de requisições: espera e tenta de novo
                time.sleep(min(int(resposta.headers.get("Retry-After", 2)), 10))
                continue
            resposta.raise_for_status()
            return resposta.json()
        raise TmdbErro("Limite de requisições do TMDB excedido")
    except requests.HTTPError as erro:
        # Não imprime o erro original: a URL contém a chave da API
        raise TmdbErro(f"TMDB retornou status {erro.response.status_code}")
    except requests.RequestException:
        raise TmdbErro("Falha de conexão com o TMDB")
    except ValueError:
        raise TmdbErro("Resposta do TMDB não é um JSON válido")


def buscar_generos(tipo):
    """Retorna {id_do_genero: nome} para filmes ou séries."""
    dados = _get(f"/genre/{CAMINHOS[tipo]}/list")
    if "genres" not in dados:
        raise TmdbErro("Resposta de gêneros inválida")
    return {genero["id"]: genero["name"] for genero in dados["genres"]}


def buscar_populares(tipo, pagina=1):
    """Retorna {'results': [...], 'total_pages': n} de uma página."""
    dados = _get(f"/{CAMINHOS[tipo]}/popular", {"page": pagina})
    if "results" not in dados:
        raise TmdbErro("Resposta de populares inválida")
    return {"results": dados["results"], "total_pages": dados.get("total_pages", 1)}

def buscar_maiores_bilheterias(pagina=1):
    """Filmes ordenados por receita (a receita em si vem nos detalhes)."""
    dados = _get("/discover/movie", {"sort_by": "revenue.desc", "page": pagina})
    if "results" not in dados:
        raise TmdbErro("Resposta de bilheterias inválida")
    return dados["results"]


def buscar_detalhes_filme(tmdb_id):
    dados = _get(f"/movie/{tmdb_id}")
    if "id" not in dados:
        raise TmdbErro("Detalhes do filme inválidos")
    return dados
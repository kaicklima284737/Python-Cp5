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
        resposta = requests.get(f"{TMDB_BASE_URL}{caminho}", params=params, timeout=10)
        resposta.raise_for_status()
        return resposta.json()
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
    """Retorna a lista de itens populares de uma página."""
    dados = _get(f"/{CAMINHOS[tipo]}/popular", {"page": pagina})
    if "results" not in dados:
        raise TmdbErro("Resposta de populares inválida")
    return dados["results"]

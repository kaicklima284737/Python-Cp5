from pymongo import MongoClient

from config import MONGODB_DB, MONGODB_URI

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000, tz_aware=True)
    return _client[MONGODB_DB]


def get_titulos():
    """Versão mais recente de cada filme/série."""
    return get_db()["titulos"]


def get_historico():
    """Uma cópia de cada registro a cada coleta (nunca é apagada)."""
    return get_db()["historico"]


def testar_conexao():
    get_db().client.admin.command("ping")


def criar_indices():
    get_titulos().create_index([("tmdb_id", 1), ("tipo", 1)], unique=True)
    get_historico().create_index([("tmdb_id", 1), ("tipo", 1), ("data_coleta", -1)])


def salvar_titulo(doc):
    """Insere ou atualiza o título e guarda o histórico. Retorna True se for novo."""
    resultado = get_titulos().update_one(
        {"tmdb_id": doc["tmdb_id"], "tipo": doc["tipo"]},
        {"$set": doc, "$setOnInsert": {"primeira_coleta": doc["data_coleta"]}},
        upsert=True,
    )
    get_historico().insert_one(dict(doc))
    return resultado.upserted_id is not None

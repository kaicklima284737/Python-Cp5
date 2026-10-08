from pymongo import MongoClient, UpdateOne

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


def salvar_lote(docs):
    """Insere ou atualiza vários títulos e guarda o histórico. Retorna quantos são novos."""
    if not docs:
        return 0

    operacoes = [
        UpdateOne(
            {"tmdb_id": doc["tmdb_id"], "tipo": doc["tipo"]},
            {"$set": doc, "$setOnInsert": {"primeira_coleta": doc["data_coleta"]}},
            upsert=True,
        )
        for doc in docs
    ]
    resultado = get_titulos().bulk_write(operacoes, ordered=False)
    get_historico().insert_many([dict(doc) for doc in docs])
    return resultado.upserted_count

def get_bilheterias():
    return get_db()["bilheterias"]


def criar_indices():
    get_titulos().create_index([("tmdb_id", 1), ("tipo", 1)], unique=True)
    get_titulos().create_index("popularidade")
    get_titulos().create_index("nota_media")
    get_titulos().create_index("generos")
    get_historico().create_index([("tmdb_id", 1), ("tipo", 1), ("data_coleta", -1)])
    get_bilheterias().create_index("tmdb_id", unique=True)
    


def salvar_bilheteria(doc):
    get_bilheterias().update_one(
        {"tmdb_id": doc["tmdb_id"]},
        {"$set": doc, "$setOnInsert": {"primeira_coleta": doc["data_coleta"]}},
        upsert=True,
    )
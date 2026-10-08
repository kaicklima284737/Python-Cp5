from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class Titulo(BaseModel):
    tmdb_id: int
    titulo: str
    tipo: str
    sinopse: str = ""
    data_lancamento: Optional[str] = None
    nota_media: float = 0
    total_votos: int = 0
    popularidade: float = 0
    idioma_original: Optional[str] = None
    generos: List[str] = []
    poster_url: Optional[str] = None
    data_coleta: datetime
    primeira_coleta: Optional[datetime] = None
    origem: str


class ListaTitulos(BaseModel):
    total: int
    pagina: int
    limite: int
    resultados: List[Titulo]


class Estatisticas(BaseModel):
    total_registros: int
    media_notas: float
    mais_popular: Optional[Titulo] = None
    maior_nota: Optional[Titulo] = None
    por_tipo: Dict[str, int]
    por_genero: Dict[str, int]


class Bilheteria(BaseModel):
    tmdb_id: int
    titulo: str
    data_lancamento: Optional[str] = None
    receita: int = 0
    orcamento: int = 0
    lucro: int = 0
    nota_media: float = 0
    poster_url: Optional[str] = None
    data_coleta: datetime
    primeira_coleta: Optional[datetime] = None
    origem: str

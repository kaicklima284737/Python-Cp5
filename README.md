# Plataforma de Filmes e Séries — Crawler, API e Dashboard

Fluxo: **TMDB API → Crawler → MongoDB → FastAPI → Dashboard**

Fonte de dados: API pública do [TMDB](https://www.themoviedb.org/) (sem scraping do site).
Uso educacional. Nenhum dado pessoal é coletado.

## Arquitetura

| Pasta | Responsabilidade |
|---|---|
| `crawler/tmdb.py` | Chamadas à API do TMDB (requests) e validação das respostas |
| `crawler/crawler.py` | Tratamento (BeautifulSoup limpa HTML da sinopse), deduplicação e gravação |
| `database/mongodb.py` | Conexão, índices e gravação no MongoDB |
| `models/schemas.py` | Modelos Pydantic das respostas da API |
| `api/main.py` | Endpoints FastAPI |
| `dashboard/app.py` | Dashboard Streamlit (usa somente a API) |
| `config.py` | Lê variáveis do `.env` |

O crawler roda sozinho, sem a API. O dashboard só fala com a API.

## Estrutura

```
project/
├── crawler/{tmdb.py, crawler.py}
├── database/mongodb.py
├── api/main.py
├── dashboard/app.py
├── models/schemas.py
├── config.py
├── .env.example
├── requirements.txt
└── README.md
```

## Instalação

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
```

### Configurar o TMDB
1. Crie uma conta em https://www.themoviedb.org/signup
2. Acesse Configurações → API → solicite uma chave (uso pessoal/educacional).
3. Copie a **API Key (v3 auth)** para `TMDB_API_KEY` no `.env`.

### Configurar o MongoDB
- **Local:** instale o MongoDB Community e inicie o serviço. Use `MONGODB_URI=mongodb://localhost:27017`.
- **Docker:** `docker run -d --name mongo -p 27017:27017 mongo:7`
- **Atlas (nuvem):** crie um cluster gratuito, libere seu IP e copie a connection string para `MONGODB_URI`.

O banco (`tmdb_dashboard`) e as coleções são criados automaticamente.

## Execução

Execute cada comando na pasta `project/`, com o ambiente virtual ativo.

```bash
# 1. Crawler (3 páginas por tipo = 60 filmes + 60 séries)
python -m crawler.crawler --paginas 3
# ou python -m crawler.crawler para carregar todos os filmes e páginas. 500 páginas ao todo de filmes

# 2. API (docs automáticas em http://localhost:8000/docs)
uvicorn api.main:app --reload

# 3. Dashboard (em outro terminal) -> http://localhost:8501
streamlit run dashboard/app.py
```

Rode o crawler quantas vezes quiser. Registros existentes são atualizados e o histórico é preservado.

## Banco de dados

Banco: `tmdb_dashboard`

### Coleção `titulos` (versão mais recente)
Índice único: `(tmdb_id, tipo)` — evita duplicados.

| Campo | Tipo | Descrição |
|---|---|---|
| `tmdb_id` | int | ID no TMDB |
| `titulo` | string | Título |
| `tipo` | string | `filme` ou `serie` |
| `sinopse` | string | Sinopse sem HTML |
| `data_lancamento` | string | `AAAA-MM-DD` (ou null) |
| `nota_media` | float | 0 a 10 |
| `total_votos` | int | Quantidade de votos |
| `popularidade` | float | Índice do TMDB |
| `idioma_original` | string | Ex.: `en`, `ja` |
| `generos` | array[string] | Nomes dos gêneros |
| `poster_url` | string | URL do pôster |
| `data_coleta` | datetime | Última coleta (UTC) |
| `primeira_coleta` | datetime | Primeira vez que apareceu |
| `origem` | string | Origem dos dados |

### Coleção `historico`
Uma cópia do documento a cada coleta. Nunca é apagada.
Permite acompanhar a evolução de nota, votos e popularidade.

Exemplo:
```json
{
  "tmdb_id": 550,
  "titulo": "Clube da Luta",
  "tipo": "filme",
  "sinopse": "Um homem deprimido...",
  "data_lancamento": "1999-10-15",
  "nota_media": 8.4,
  "total_votos": 30000,
  "popularidade": 45.12,
  "idioma_original": "en",
  "generos": ["Drama", "Thriller"],
  "poster_url": "https://image.tmdb.org/t/p/w500/abc.jpg",
  "data_coleta": "2026-10-08T12:00:00Z",
  "primeira_coleta": "2026-10-08T12:00:00Z",
  "origem": "TMDB API (https://api.themoviedb.org/3)"
}
```

## Endpoints

Documentação interativa: http://localhost:8000/docs

| Método | Rota | Descrição |
|---|---|---|
| GET | `/filmes` | Lista com filtros, ordenação e paginação |
| GET | `/filmes/{id}` | Um registro pelo ID TMDB (`?tipo=` opcional) |
| GET | `/buscar` | Busca por texto no título e na sinopse |
| GET | `/estatisticas` | Total, média, mais popular, maior nota, contagens |
| GET | `/generos` | Gêneros disponíveis |

Filtros de `/filmes` e `/buscar`: `tipo` (`filme`/`serie`), `genero`, `nota_min`, `ano`,
`ordenar_por` (`popularidade`, `nota_media`, `total_votos`, `titulo`, `data_lancamento`),
`ordem` (`asc`/`desc`), `pagina`, `limite` (máx. 100).
`/estatisticas` aceita `tipo`, `genero` e `nota_min`.

Em `/estatisticas`, a média ignora títulos sem votos. A "maior nota" exige ao menos 50 votos.

### Exemplos

```bash
curl "http://localhost:8000/filmes?limite=5"
curl "http://localhost:8000/filmes?tipo=serie&genero=Drama&nota_min=7.5&ordenar_por=nota_media"
curl "http://localhost:8000/filmes/550?tipo=filme"
curl "http://localhost:8000/buscar?q=guerra&tipo=filme"
curl "http://localhost:8000/estatisticas"
curl "http://localhost:8000/generos"
```

Resposta de `/filmes`:
```json
{
  "total": 120,
  "pagina": 1,
  "limite": 5,
  "resultados": [ { "tmdb_id": 550, "titulo": "...", "...": "..." } ]
}
```

## Dashboard

- Indicadores: total, média das avaliações, mais popular, maior avaliação.
- Gráficos: top 10 popularidade, top 10 avaliação, distribuição por gênero.
- Pesquisa por texto, filtros de tipo, gênero e nota mínima.
- Tabela com pôster e dados.

## Demonstração

1. `python -m crawler.crawler --paginas 3` — mostra quantos itens foram coletados.
2. Abra o MongoDB Compass (ou `mongosh`) e mostre as coleções `titulos` e `historico`.
   Com `mongosh`: `use tmdb_dashboard` e `db.titulos.countDocuments()`.
3. Abra `/docs` e execute `/filmes` e `/estatisticas`.
4. Abra o dashboard e use busca e filtros.
5. Rode o crawler de novo: `titulos` mantém a contagem e `historico` cresce.

## Problemas comuns

- **`TMDB_API_KEY não definida`**: confira o `.env` na pasta `project/`.
- **`status 401`**: chave inválida.
- **`não foi possível conectar ao MongoDB`**: serviço desligado ou URI errada.
- **Dashboard sem acesso à API**: inicie o uvicorn antes. Mude `API_URL` no `.env` se usar outra porta.
- **Dashboard vazio**: rode o crawler primeiro.

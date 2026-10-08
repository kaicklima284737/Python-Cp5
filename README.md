# Plataforma de Filmes e Séries: Crawler, API e Dashboard

Fluxo: **TMDB API → Crawler → MongoDB → FastAPI → Dashboard**

Projeto educacional de coleta e análise de dados. O sistema coleta filmes e séries populares do TMDB, guarda no MongoDB, serve por uma API FastAPI e mostra tudo em um dashboard web.

> This product uses the TMDB API but is not endorsed or certified by TMDB.

## Site escolhido

[TMDB (The Movie Database)](https://www.themoviedb.org/) é um catálogo público de filmes e séries.

- A fonte é exclusivamente a **API oficial** do TMDB. Não há scraping do site.
- O uso é educacional.
- Nenhum dado pessoal é coletado.
- A chave da API fica no `.env` e nunca é versionada.

## Dados coletados

**Filmes e séries populares** (até 500 páginas por tipo, o limite da API):

| Campo | Descrição |
|---|---|
| `tmdb_id` | ID no TMDB |
| `titulo` | Título |
| `tipo` | `filme` ou `serie` |
| `sinopse` | Sinopse, sem HTML |
| `data_lancamento` | Data de lançamento ou de estreia |
| `nota_media` | Nota de 0 a 10 |
| `total_votos` | Quantidade de votos |
| `popularidade` | Índice de popularidade do TMDB |
| `idioma_original` | Ex.: `en`, `ja`, `pt` |
| `generos` | Lista com os nomes dos gêneros |
| `poster_url` | URL do pôster |
| `data_coleta` | Data e hora da coleta (UTC) |
| `origem` | De onde o dado veio |

**Maiores bilheterias** (filmes ordenados por receita): `receita`, `orcamento` e `lucro`, em dólares, além do título, da data de lançamento, da nota e do pôster.

### Tratamento dos dados
- O BeautifulSoup remove tags HTML das sinopses. Espaços repetidos também são removidos.
- Os ids de gênero viram nomes.
- Números são convertidos e arredondados.
- A URL do pôster é montada por completo.
- Itens sem id ou sem título são descartados.
- Duplicados na mesma coleta são ignorados.

## Arquitetura

| Arquivo | Responsabilidade |
|---|---|
| `config.py` | Lê as variáveis do `.env` |
| `crawler/tmdb.py` | Chamadas à API do TMDB, validação das respostas e novas tentativas |
| `crawler/crawler.py` | Coleta, tratamento e gravação |
| `database/mongodb.py` | Conexão, índices e gravação no MongoDB |
| `models/schemas.py` | Modelos Pydantic das respostas da API |
| `api/main.py` | Endpoints FastAPI |
| `dashboard/app.py` | Interface Streamlit, que consome só a API |
| `dashboard/busca.py` | Quicksort e busca binária usados na aba de detalhes |
| `.streamlit/config.toml` | Tema do dashboard |

O crawler roda sozinho, sem a API. O dashboard só fala com a API: não acessa o MongoDB nem o TMDB. Os pôsteres são imagens carregadas pelo navegador a partir do servidor de imagens do TMDB.

## Estrutura de pastas

```
project/
├── .streamlit/config.toml
├── crawler/{tmdb.py, crawler.py}
├── database/mongodb.py
├── api/main.py
├── dashboard/{app.py, busca.py}
├── models/schemas.py
├── config.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Instalação

```bash
python -m venv venv
venv\Scripts\activate           # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Linux/Mac: cp .env.example .env
```

### Configurar o TMDB
1. Crie uma conta em https://www.themoviedb.org/signup
2. Acesse Configurações → API e solicite uma chave (uso pessoal/educacional).
3. Copie a **API Key (v3 auth)** para `TMDB_API_KEY` no `.env`.

### Configurar o MongoDB
- **Local:** instale o MongoDB Community e inicie o serviço. Use `MONGODB_URI=mongodb://localhost:27017`.
- **Docker:** `docker run -d --name mongo -p 27017:27017 mongo:7`
- **Atlas (nuvem):** crie um cluster gratuito, libere seu IP e copie a connection string para `MONGODB_URI`.

O banco (`tmdb_dashboard`), as coleções e os índices são criados automaticamente.

### Variáveis do `.env`

| Variável | Obrigatória | Descrição |
|---|---|---|
| `TMDB_API_KEY` | Sim | Chave da API do TMDB |
| `MONGODB_URI` | Sim | Endereço do MongoDB |
| `MONGODB_DB` | Não | Nome do banco (padrão `tmdb_dashboard`) |
| `API_URL` | Não | Endereço da API (padrão `http://localhost:8000`) |

## Execução

Use um terminal para cada processo, na pasta do projeto e com o venv ativo.

```bash
# 1. Crawler: todas as páginas disponíveis (até 500 por tipo)
python -m crawler.crawler

# Teste rápido: 3 páginas por tipo (60 filmes + 60 séries)
python -m crawler.crawler --paginas 3

# 2. API (documentação em http://localhost:8000/docs)
uvicorn api.main:app

# 3. Dashboard (http://localhost:8501)
streamlit run dashboard/app.py
```

A coleta completa faz cerca de 1.000 requisições e leva alguns minutos. Cada página é salva assim que é coletada. Se der erro no meio, o que já foi salvo permanece.

O crawler pode rodar quantas vezes quiser. Registros existentes são atualizados e o histórico é preservado.

## Banco de dados

Banco: `tmdb_dashboard`

### Coleção `titulos` (versão mais recente de cada filme/série)
Índice único em `(tmdb_id, tipo)`. Isso impede duplicados.
Índices extras em `popularidade`, `nota_media` e `generos`.

Os campos são os da tabela "Dados coletados". Além deles, o documento guarda `primeira_coleta`, a data da primeira vez que o registro apareceu.

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

### Coleção `historico`
Uma cópia do documento a cada coleta. **Nunca é apagada.**
Permite acompanhar a evolução de nota, votos e popularidade ao longo do tempo.

### Coleção `bilheterias`
Índice único em `tmdb_id`. Guarda a versão mais recente de cada filme do ranking.

```json
{
  "tmdb_id": 19995,
  "titulo": "Avatar",
  "data_lancamento": "2009-12-15",
  "receita": 2923706026,
  "orcamento": 237000000,
  "lucro": 2686706026,
  "nota_media": 7.6,
  "poster_url": "https://image.tmdb.org/t/p/w500/abc.jpg",
  "data_coleta": "2026-10-08T12:00:00Z",
  "primeira_coleta": "2026-10-08T12:00:00Z",
  "origem": "TMDB API (https://api.themoviedb.org/3)"
}
```

## Endpoints da API

Documentação interativa: http://localhost:8000/docs

| Método | Rota | Descrição |
|---|---|---|
| GET | `/filmes` | Lista com filtros, ordenação e paginação |
| GET | `/filmes/{id}` | Um registro pelo ID do TMDB (`?tipo=` opcional) |
| GET | `/buscar` | Busca por texto no título e na sinopse |
| GET | `/estatisticas` | Total, média, mais popular, maior nota e contagens |
| GET | `/generos` | Gêneros disponíveis |
| GET | `/bilheterias` | Maiores bilheterias (`?limite=`, de 1 a 50) |

**Parâmetros de `/filmes` e `/buscar`**

| Parâmetro | Descrição |
|---|---|
| `q` | Texto da busca (só em `/buscar`, obrigatório) |
| `tipo` | `filme` ou `serie` |
| `genero` | Nome do gênero |
| `nota_min` | Nota mínima (0 a 10) |
| `ano` | Ano de lançamento |
| `ordenar_por` | `popularidade`, `nota_media`, `total_votos`, `titulo`, `data_lancamento` |
| `ordem` | `asc` ou `desc` |
| `pagina` | Número da página (começa em 1) |
| `limite` | Itens por página (1 a 500) |

`/estatisticas` aceita `tipo`, `genero` e `nota_min`.

Observações sobre as estatísticas:
- A média das notas ignora títulos sem votos.
- A "maior nota" exige pelo menos 50 votos.

**Códigos de resposta:** `200` sucesso, `404` registro não encontrado, `422` parâmetro inválido, `503` banco indisponível.

### Exemplos

```bash
curl "http://localhost:8000/filmes?limite=5"
curl "http://localhost:8000/filmes?tipo=serie&genero=Drama&nota_min=7.5&ordenar_por=nota_media"
curl "http://localhost:8000/filmes/550?tipo=filme"
curl "http://localhost:8000/buscar?q=guerra&tipo=filme"
curl "http://localhost:8000/estatisticas"
curl "http://localhost:8000/generos"
curl "http://localhost:8000/bilheterias?limite=10"
```

Resposta de `/filmes`:
```json
{
  "total": 20000,
  "pagina": 1,
  "limite": 5,
  "resultados": [ { "tmdb_id": 550, "titulo": "...", "...": "..." } ]
}
```

## Dashboard

Três seções, escolhidas por botões no topo:

1. **Visão geral**
   - Indicadores: total de registros, média das avaliações, mais popular e maior avaliação.
   - Gráficos: top 10 por popularidade, top 10 por avaliação e distribuição por gênero.
   - Tabela com pôster, título, tipo, lançamento, nota, votos, popularidade e gêneros.
2. **Detalhes do filme**
   - Página individual de cada título, com pôster, métricas, sinopse, gêneros e dados da coleta.
   - Barra de pesquisa. O título é ordenado com **quicksort**. A pesquisa por título exato usa **busca binária**. Sem correspondência exata, mostra os títulos que contêm o texto.
3. **Bilheterias**
   - Top 10 por receita, em gráfico e tabela com receita, orçamento e lucro.

**Filtros da barra lateral:** pesquisa por texto, tipo, gênero, nota mínima e quantidade máxima de registros carregados (100 a 5000).

**Desempenho:** as respostas da API ficam em cache por 5 minutos. Para ver dados novos antes disso, aperte `C` no navegador e limpe o cache.

**Tema:** definido em `.streamlit/config.toml` e no CSS do `app.py`. Fundo ciano, elementos brancos e letras pretas.

## Demonstração

1. Rodar o crawler: `python -m crawler.crawler --paginas 3`
2. Abrir o MongoDB Compass (ou o `mongosh`) e mostrar as coleções `titulos`, `historico` e `bilheterias`.
3. Abrir `/docs` e executar `/filmes`, `/buscar` e `/estatisticas`.
4. Abrir o dashboard e percorrer as três seções, usando filtros e pesquisa.
5. Rodar o crawler de novo. `titulos` mantém a contagem e `historico` cresce.

## Problemas comuns

| Problema | Solução |
|---|---|
| `ModuleNotFoundError` | Ative o venv e rode `pip install -r requirements.txt` |
| `TMDB_API_KEY não definida` | Confira o `.env` na pasta do projeto |
| `TMDB retornou status 401` | Chave da API inválida |
| `não foi possível conectar ao MongoDB` | Serviço desligado ou `MONGODB_URI` errada |
| Dashboard: "Não foi possível acessar a API" | Inicie o uvicorn antes. Teste `http://localhost:8000/generos` |
| API retorna `503` | MongoDB indisponível |
| Dashboard vazio | Rode o crawler primeiro |
| Aba Bilheterias vazia | Rode o crawler. Ele coleta as bilheterias no final |
| Tema não muda | A pasta `.streamlit` deve ficar onde você roda o `streamlit run`. Reinicie o Streamlit |

## Créditos

Dados fornecidos pelo [TMDB](https://www.themoviedb.org/).
This product uses the TMDB API but is not endorsed or certified by TMDB.
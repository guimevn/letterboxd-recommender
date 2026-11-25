# Letterboxd Recommender

Sistema de recomendação de filmes baseado no perfil público do Letterboxd (favoritos, histórico completo de filmes assistidos, notas, reviews e watchlist), enriquecido com metadados e disponibilidade de streaming no Brasil via TMDB API. 100% gratuito.

## Funcionalidades

- **Entrada simples por username:** basta digitar o `@` do Letterboxd para sincronizar favoritos, filmes assistidos, notas, reviews e watchlist em cache local (SQLite).
- **4 opções por vez com trava:** exibe exatamente 4 filmes inéditos por rodada, com ações de **Gostei** (fixa o filme e direciona as próximas buscas para aquela vibe), **Não gostei** (substitui na hora e evita aquele estilo), **Já vi** (substitui e reforça o perfil) e **Pular** (substitui e evita no momento).
- **Análise completa do perfil:** lê 100% dos filmes assistidos e das reviews escritas pelo usuário, cruzando diretores, gêneros, temas, elenco, décadas e idioma.
- **Filtros de contexto:** Mood (Leve, Tenso, Reflexivo, Épico), Origem (Mundo todo ou Watchlist), Nível de descoberta (Popular, Equilibrado, Cult) e Duração máxima.
- **Apenas filmes:** não recomenda séries nem minisséries; documentários só entram quando o histórico do usuário demonstra afinidade.
- **Notas e streaming:** exibe a nota oficial do Letterboxd e os streamings disponíveis no Brasil.

## Como executar localmente

### 1. Pré-requisitos
- Python 3.10+ (recomendado Python 3.12)
- Chave gratuita da API do [TMDB](https://www.themoviedb.org/settings/api)

### 2. Instalação
```bash
git clone https://github.com/guimevn/letterboxd-recommender.git
cd letterboxd-recommender

python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Variáveis de ambiente
Copie `.env.example` para `.env` e preencha sua chave gratuita do TMDB:
```env
TMDB_READ_ACCESS_TOKEN=seu_token_aqui
TMDB_API_KEY=sua_api_key_aqui
```
O arquivo `.env` está listado no `.gitignore` e nunca deve ser enviado ao repositório.

### 4. Executar
```bash
uvicorn main:app --reload
```
Abra `http://127.0.0.1:8000` no navegador.

## Estrutura do projeto

```
letterboxd-recommender/
├── app/
│   ├── db.py           # Cache SQLite local
│   ├── letterboxd.py   # Coleta assíncrona do perfil, favoritos, watchlist e reviews
│   ├── tmdb.py         # Cliente TMDB e notas do Letterboxd
│   └── recommender.py  # Motor de perfil de gosto e recomendações
├── frontend/
│   ├── index.html      # Interface mobile-first centralizada
│   └── app.js          # Lógica de 4 opções, trava e feedback na sessão
├── tests/
│   └── test_smoke.py   # Teste ponta a ponta
├── main.py             # API FastAPI + servidor do frontend
├── requirements.txt
└── .env.example
```

## Licença

MIT. Veja o arquivo [LICENSE](LICENSE).

# Letterboxd Recommender

**Live App:** https://letterboxd-recommender.guimevn.workers.dev

A free, mobile-first movie recommender powered by your public Letterboxd profile (ratings, reviews, favorites, and watchlist) and the TMDB API. Enter any Letterboxd username and get 4 tailored movie picks at a time.

## Features

- **Username-only entry:** type any public Letterboxd `@username` to get recommendations immediately, plus an optional `.zip` import for 100% history and watchlist analysis in cloud deployments.
- **4 picks at a time with live feedback:** lock movies you **Like** so the next refresh follows that vibe, or click **Dislike**, **Seen**, or **Skip** to replace a card instantly and steer the session.
- **Context filters:** Mood (Light, Intense, Thoughtful, Epic), Source (Worldwide or Watchlist), Discovery level (Popular, Balanced, Cult), and Max runtime.
- **Movies only:** excludes TV shows and miniseries; documentaries only appear when your profile shows affinity for them; superhero movies are limited unless you clearly love them.
- **Multi-language and regional streaming:** auto-detects browser language and region (`PT`, `EN`, `ES`, `FR`) and displays local streaming availability via TMDB alongside Letterboxd ratings.

## Run Locally

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Free [TMDB API](https://www.themoviedb.org/settings/api) Read Access Token

### 2. Setup
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

### 3. Environment Variables
Copy `.env.example` to `.env` and add your TMDB token:
```env
TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token_here
```

### 4. Start the Server
```bash
uvicorn main:app --reload
```
Open `http://127.0.0.1:8000` in your browser.

## Architecture

- **Frontend:** HTML, Tailwind CSS, and modular JavaScript hosted on **Cloudflare Workers** (`wrangler.jsonc`).
- **Backend:** Python, FastAPI, Uvicorn, SQLite, `httpx`, and `curl_cffi` hosted on **Render** (`render.yaml`).
- **Data:** Letterboxd (full HTML scrape locally, automatic official RSS fallback in cloud + optional `.zip` export import) and TMDB API.

## License

MIT. See [LICENSE](LICENSE).

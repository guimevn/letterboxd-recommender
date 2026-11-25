import asyncio
import os
import re
from typing import Any, Optional
import httpx
from dotenv import load_dotenv
from app import db

try:
    from curl_cffi.requests import AsyncSession as CffiAsyncSession
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

load_dotenv()

TMDB_BASE = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p"


def _get_headers() -> dict[str, str]:
    token = os.getenv("TMDB_READ_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "TMDB_READ_ACCESS_TOKEN não configurado. Adicione sua chave no arquivo .env."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


class TMDBClient:
    def __init__(self) -> None:
        self._sem = asyncio.Semaphore(15)

    async def _get(self, client: httpx.AsyncClient, path: str, params: Optional[dict] = None) -> Optional[dict]:
        async with self._sem:
            try:
                resp = await client.get(
                    f"{TMDB_BASE}{path}",
                    headers=_get_headers(),
                    params=params or {},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return resp.json()
                return None
            except Exception:
                return None

    async def search_movie_id(
        self, client: httpx.AsyncClient, title: str, year: Optional[int] = None
    ) -> Optional[int]:
        params: dict[str, Any] = {"query": title, "include_adult": "false", "language": "en-US"}
        if year:
            params["year"] = year

        data = await self._get(client, "/search/movie", params)
        results = (data or {}).get("results", [])

        if not results and year:
            params.pop("year", None)
            data = await self._get(client, "/search/movie", params)
            results = (data or {}).get("results", [])

        if not results:
            return None

        # Prefer exact year match if available, otherwise highest popularity among top 3
        if year:
            for r in results[:5]:
                rd = r.get("release_date") or ""
                if rd.startswith(str(year)):
                    return r["id"]
        return results[0]["id"]

    async def resolve_slug_to_tmdb(
        self, client: httpx.AsyncClient, slug: str, title: str, year: Optional[int]
    ) -> Optional[int]:
        cached = db.get_slug_mapping([slug])
        if slug in cached:
            tmdb_id, is_movie = cached[slug]
            return tmdb_id if is_movie else None

        tmdb_id = await self.search_movie_id(client, title, year)
        db.save_slug_mapping(slug, tmdb_id, is_movie=1 if tmdb_id else 0)
        return tmdb_id

    async def get_movie_details(
        self, client: httpx.AsyncClient, tmdb_id: int
    ) -> Optional[dict[str, Any]]:
        cached = db.get_tmdb_movies([tmdb_id])
        if tmdb_id in cached:
            return cached[tmdb_id]

        data = await self._get(
            client,
            f"/movie/{tmdb_id}",
            {
                "language": "pt-BR",
                "append_to_response": "credits,keywords,watch/providers",
            },
        )
        if not data:
            return None

        overview = (data.get("overview") or "").strip()
        if not overview:
            en_data = await self._get(client, f"/movie/{tmdb_id}", {"language": "en-US"})
            if en_data:
                overview = (en_data.get("overview") or "").strip()

        release_date = data.get("release_date") or ""
        year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None

        credits = data.get("credits") or {}
        directors = [
            {"id": c["id"], "name": c["name"]}
            for c in credits.get("crew", [])
            if c.get("job") == "Director"
        ]
        cast = [c["name"] for c in credits.get("cast", [])[:5]]
        keywords = [k["name"] for k in (data.get("keywords") or {}).get("keywords", [])[:15]]
        genres = [{"id": g["id"], "name": g["name"]} for g in data.get("genres", [])]
        countries = [c["iso_3166_1"] for c in data.get("production_countries", [])]

        providers_results = (data.get("watch/providers") or {}).get("results", {})
        providers_by_region: dict[str, list[dict[str, Any]]] = {}
        for rc in ("BR", "US", "ES", "FR", "PT", "MX", "GB", "CA", "AR"):
            flat = (providers_results.get(rc) or {}).get("flatrate", [])
            if flat:
                providers_by_region[rc] = [
                    {
                        "name": p["provider_name"],
                        "logo_path": f"{IMG_BASE}/w92{p['logo_path']}" if p.get("logo_path") else None,
                    }
                    for p in flat[:5]
                ]
        providers_br = providers_by_region.get("BR", [])

        movie = {
            "tmdb_id": data["id"],
            "imdb_id": data.get("imdb_id"),
            "title": data.get("title") or data.get("original_title"),
            "original_title": data.get("original_title"),
            "original_language": data.get("original_language") or "en",
            "year": year,
            "overview": overview,
            "poster_path": f"{IMG_BASE}/w500{data['poster_path']}" if data.get("poster_path") else None,
            "backdrop_path": f"{IMG_BASE}/w1280{data['backdrop_path']}" if data.get("backdrop_path") else None,
            "runtime": data.get("runtime") or 0,
            "vote_average": round(float(data.get("vote_average") or 0.0), 1),
            "vote_count": int(data.get("vote_count") or 0),
            "popularity": float(data.get("popularity") or 0.0),
            "genres": genres,
            "keywords": keywords,
            "directors": directors,
            "cast": cast,
            "countries": countries,
            "providers_br": providers_br,
            "providers_by_region": providers_by_region,
        }
        db.save_tmdb_movie(movie)
        return movie

    async def get_recommendations(self, client: httpx.AsyncClient, tmdb_id: int) -> list[dict[str, Any]]:
        data = await self._get(client, f"/movie/{tmdb_id}/recommendations", {"language": "pt-BR", "page": 1})
        return (data or {}).get("results", [])

    async def discover_movies(
        self, client: httpx.AsyncClient, params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        base_params = {
            "include_adult": "false",
            "include_video": "false",
            "language": "pt-BR",
            "sort_by": "vote_average.desc",
            "page": 1,
        }
        base_params.update(params)
        data = await self._get(client, "/discover/movie", base_params)
        return (data or {}).get("results", [])

    async def enrich_external_ratings(self, movies: list[dict[str, Any]]) -> None:
        """Fetch and cache real Letterboxd (0-5) ratings for the final 4 movies."""
        lb_re = re.compile(r'twitter:data2"\s+content="([0-9.]+)\s+out of 5')

        async def _fetch_one(session: Any, m: dict[str, Any]) -> None:
            tid = m["tmdb_id"]
            lb_rating = m.get("letterboxd_rating")
            if lb_rating is not None:
                return
            try:
                r = await session.get(
                    f"https://letterboxd.com/tmdb/{tid}/",
                    timeout=6,
                    allow_redirects=True,
                )
                if r.status_code == 200:
                    match = lb_re.search(r.text)
                    if match:
                        lb_rating = round(float(match.group(1)), 1)
                        db.update_movie_external_ratings(tid, None, lb_rating)
                        m["letterboxd_rating"] = lb_rating
            except Exception:
                pass

        needs_fetch = [m for m in movies if m.get("letterboxd_rating") is None]
        if not needs_fetch:
            return

        if HAS_CURL_CFFI:
            async with CffiAsyncSession(impersonate="chrome") as session:
                await asyncio.gather(*(_fetch_one(session, m) for m in needs_fetch))
        else:
            async with httpx.AsyncClient(follow_redirects=True) as session:
                await asyncio.gather(*(_fetch_one(session, m) for m in needs_fetch))

    async def localize_movies(self, movies: list[dict[str, Any]], lang: str) -> None:
        """Translate title and genre names of the final 4 movies when lang is not pt."""
        lang_map = {"en": "en-US", "es": "es-ES", "fr": "fr-FR"}
        tmdb_lang = lang_map.get(lang)
        if not tmdb_lang or not movies:
            return

        async with httpx.AsyncClient() as client:
            async def _loc_one(m: dict[str, Any]) -> None:
                d = await self._get(client, f"/movie/{m['tmdb_id']}", {"language": tmdb_lang})
                if not d:
                    return
                if d.get("title"):
                    m["title"] = d["title"]
                if d.get("genres"):
                    m["genres"] = [{"id": g["id"], "name": g["name"]} for g in d["genres"]]

            await asyncio.gather(*(_loc_one(m) for m in movies))

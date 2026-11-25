import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "recommender.db")


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                display_name TEXT,
                avatar_url TEXT,
                synced_at REAL,
                total_watched INTEGER DEFAULT 0,
                total_watchlist INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS user_films (
                username TEXT NOT NULL,
                slug TEXT NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                rating REAL,
                liked INTEGER DEFAULT 0,
                is_favorite INTEGER DEFAULT 0,
                in_watched INTEGER DEFAULT 0,
                in_watchlist INTEGER DEFAULT 0,
                tmdb_id INTEGER,
                review_text TEXT,
                PRIMARY KEY (username, slug)
            );

            CREATE INDEX IF NOT EXISTS idx_user_films_user ON user_films(username);

            CREATE TABLE IF NOT EXISTS slug_to_tmdb (
                slug TEXT PRIMARY KEY,
                tmdb_id INTEGER,
                is_movie INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS tmdb_movies (
                tmdb_id INTEGER PRIMARY KEY,
                title TEXT,
                original_title TEXT,
                original_language TEXT,
                year INTEGER,
                overview TEXT,
                poster_path TEXT,
                backdrop_path TEXT,
                runtime INTEGER,
                vote_average REAL,
                vote_count INTEGER,
                popularity REAL,
                genres_json TEXT,
                keywords_json TEXT,
                directors_json TEXT,
                cast_json TEXT,
                countries_json TEXT,
                providers_br_json TEXT,
                updated_at REAL
            );

            CREATE TABLE IF NOT EXISTS dismissed (
                username TEXT NOT NULL,
                tmdb_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at REAL NOT NULL,
                PRIMARY KEY (username, tmdb_id)
            );
            """
        )
        # Safe migrations for existing local DBs
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(user_films)").fetchall()}
        if "review_text" not in cols:
            conn.execute("ALTER TABLE user_films ADD COLUMN review_text TEXT")

        m_cols = {r["name"] for r in conn.execute("PRAGMA table_info(tmdb_movies)").fetchall()}
        if "imdb_id" not in m_cols:
            conn.execute("ALTER TABLE tmdb_movies ADD COLUMN imdb_id TEXT")
        if "imdb_rating" not in m_cols:
            conn.execute("ALTER TABLE tmdb_movies ADD COLUMN imdb_rating REAL")
        if "letterboxd_rating" not in m_cols:
            conn.execute("ALTER TABLE tmdb_movies ADD COLUMN letterboxd_rating REAL")
        if "providers_by_region_json" not in m_cols:
            conn.execute("ALTER TABLE tmdb_movies ADD COLUMN providers_by_region_json TEXT")


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_user(username: str) -> Optional[dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username.lower(),)).fetchone()
        return dict(row) if row else None


def save_user_profile(
    username: str,
    display_name: str,
    avatar_url: Optional[str],
    films: list[dict[str, Any]],
) -> None:
    uname = username.lower()
    total_watched = sum(1 for f in films if f.get("in_watched"))
    total_watchlist = sum(1 for f in films if f.get("in_watchlist"))

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (username, display_name, avatar_url, synced_at, total_watched, total_watchlist)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                display_name = excluded.display_name,
                avatar_url = excluded.avatar_url,
                synced_at = excluded.synced_at,
                total_watched = excluded.total_watched,
                total_watchlist = excluded.total_watchlist
            """,
            (uname, display_name, avatar_url, time.time(), total_watched, total_watchlist),
        )
        conn.execute("DELETE FROM user_films WHERE username = ?", (uname,))
        conn.executemany(
            """
            INSERT INTO user_films (
                username, slug, title, year, rating, liked, is_favorite, in_watched, in_watchlist, tmdb_id, review_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    uname,
                    f["slug"],
                    f["title"],
                    f.get("year"),
                    f.get("rating"),
                    1 if f.get("liked") else 0,
                    1 if f.get("is_favorite") else 0,
                    1 if f.get("in_watched") else 0,
                    1 if f.get("in_watchlist") else 0,
                    f.get("tmdb_id"),
                    f.get("review_text"),
                )
                for f in films
            ],
        )


def get_user_films(username: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT uf.*, COALESCE(uf.tmdb_id, st.tmdb_id) AS resolved_tmdb_id
            FROM user_films uf
            LEFT JOIN slug_to_tmdb st ON st.slug = uf.slug
            WHERE uf.username = ?
            """,
            (username.lower(),),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["tmdb_id"] = d.pop("resolved_tmdb_id")
            result.append(d)
        return result


def get_slug_mapping(slugs: list[str]) -> dict[str, tuple[Optional[int], int]]:
    if not slugs:
        return {}
    with get_conn() as conn:
        placeholders = ",".join("?" for _ in slugs)
        rows = conn.execute(
            f"SELECT slug, tmdb_id, is_movie FROM slug_to_tmdb WHERE slug IN ({placeholders})",
            slugs,
        ).fetchall()
        return {r["slug"]: (r["tmdb_id"], r["is_movie"]) for r in rows}


def save_slug_mapping(slug: str, tmdb_id: Optional[int], is_movie: int = 1) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO slug_to_tmdb (slug, tmdb_id, is_movie)
            VALUES (?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET tmdb_id = excluded.tmdb_id, is_movie = excluded.is_movie
            """,
            (slug, tmdb_id, is_movie),
        )


def get_tmdb_movies(tmdb_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not tmdb_ids:
        return {}
    with get_conn() as conn:
        placeholders = ",".join("?" for _ in tmdb_ids)
        rows = conn.execute(
            f"SELECT * FROM tmdb_movies WHERE tmdb_id IN ({placeholders})",
            tmdb_ids,
        ).fetchall()
        return {r["tmdb_id"]: _deserialize_movie(dict(r)) for r in rows}


def save_tmdb_movie(movie: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tmdb_movies (
                tmdb_id, imdb_id, title, original_title, original_language, year, overview,
                poster_path, backdrop_path, runtime, vote_average, vote_count, popularity,
                genres_json, keywords_json, directors_json, cast_json, countries_json,
                providers_br_json, providers_by_region_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tmdb_id) DO UPDATE SET
                imdb_id = COALESCE(excluded.imdb_id, tmdb_movies.imdb_id),
                title = excluded.title,
                original_title = excluded.original_title,
                original_language = excluded.original_language,
                year = excluded.year,
                overview = excluded.overview,
                poster_path = excluded.poster_path,
                backdrop_path = excluded.backdrop_path,
                runtime = excluded.runtime,
                vote_average = excluded.vote_average,
                vote_count = excluded.vote_count,
                popularity = excluded.popularity,
                genres_json = excluded.genres_json,
                keywords_json = excluded.keywords_json,
                directors_json = excluded.directors_json,
                cast_json = excluded.cast_json,
                countries_json = excluded.countries_json,
                providers_br_json = excluded.providers_br_json,
                providers_by_region_json = COALESCE(excluded.providers_by_region_json, tmdb_movies.providers_by_region_json),
                updated_at = excluded.updated_at
            """,
            (
                movie["tmdb_id"],
                movie.get("imdb_id"),
                movie.get("title"),
                movie.get("original_title"),
                movie.get("original_language"),
                movie.get("year"),
                movie.get("overview"),
                movie.get("poster_path"),
                movie.get("backdrop_path"),
                movie.get("runtime"),
                movie.get("vote_average"),
                movie.get("vote_count"),
                movie.get("popularity"),
                json.dumps(movie.get("genres", []), ensure_ascii=False),
                json.dumps(movie.get("keywords", []), ensure_ascii=False),
                json.dumps(movie.get("directors", []), ensure_ascii=False),
                json.dumps(movie.get("cast", []), ensure_ascii=False),
                json.dumps(movie.get("countries", []), ensure_ascii=False),
                json.dumps(movie.get("providers_br", []), ensure_ascii=False),
                json.dumps(movie.get("providers_by_region", {}), ensure_ascii=False),
                time.time(),
            ),
        )


def _deserialize_movie(row: dict[str, Any]) -> dict[str, Any]:
    row["genres"] = json.loads(row.pop("genres_json") or "[]")
    row["keywords"] = json.loads(row.pop("keywords_json") or "[]")
    row["directors"] = json.loads(row.pop("directors_json") or "[]")
    row["cast"] = json.loads(row.pop("cast_json") or "[]")
    row["countries"] = json.loads(row.pop("countries_json") or "[]")
    row["providers_br"] = json.loads(row.pop("providers_br_json") or "[]")
    row["providers_by_region"] = json.loads(row.pop("providers_by_region_json") or "{}")
    return row


def update_movie_external_ratings(
    tmdb_id: int, imdb_rating: Optional[float], letterboxd_rating: Optional[float]
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tmdb_movies
            SET imdb_rating = COALESCE(?, imdb_rating),
                letterboxd_rating = COALESCE(?, letterboxd_rating)
            WHERE tmdb_id = ?
            """,
            (imdb_rating, letterboxd_rating, tmdb_id),
        )


def dismiss_movie(username: str, tmdb_id: int, reason: str = "not_interested") -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO dismissed (username, tmdb_id, reason, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username, tmdb_id) DO UPDATE SET reason = excluded.reason, created_at = excluded.created_at
            """,
            (username.lower(), tmdb_id, reason, time.time()),
        )


def get_dismissed_ids(username: str) -> set[int]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT tmdb_id FROM dismissed WHERE username = ?", (username.lower(),)
        ).fetchall()
        return {r["tmdb_id"] for r in rows}

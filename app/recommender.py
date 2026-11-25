import asyncio
import math
import re
from collections import defaultdict
from typing import Any, Optional
import httpx
from app import db
from app.tmdb import TMDBClient

DOCUMENTARY_GENRE_ID = 99

SUPERHERO_KEYWORDS = {
    "superhero", "superhero team", "marvel cinematic universe", "dc extended universe",
    "based on comic", "superpower", "mutant", "avengers", "x-men", "batman", "spider-man",
    "superman", "justice league", "marvel comics", "dc comics",
}


def _is_superhero_movie(movie: dict[str, Any]) -> bool:
    kws = {k.lower() for k in movie.get("keywords", [])}
    return bool(kws & SUPERHERO_KEYWORDS)

MOOD_CONFIG: dict[str, dict[str, set[int]]] = {
    "light": {
        "include": {35, 16, 10751, 10749, 10402},
        "exclude": {27, 53, 80, 10752},
    },
    "intense": {
        "include": {53, 80, 27, 28, 10752},
        "exclude": {35, 10751, 16, 10749},
    },
    "thoughtful": {
        "include": {18, 878, 9648, 36},
        "exclude": {28, 10751, 35, 27},
    },
    "epic": {
        "include": {12, 14, 878, 28, 10752},
        "exclude": {10749, 35, 10751},
    },
}


def _norm_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def _decade(year: Optional[int]) -> Optional[int]:
    return (year // 10) * 10 if year else None


POSITIVE_REVIEW_TERMS = {
    "obra-prima", "perfeito", "incrivel", "incrível", "maravilhoso", "genial",
    "emocionante", "amei", "lindo", "fantastico", "fantástico", "brilhante",
    "absurdo", "sensacional", "favorito", "masterpiece", "brilliant", "amazing",
    "incredible", "beautiful", "loved", "perfect", "stunning", "phenomenal",
    "cinematografia", "fotografia", "roteiro", "trilha", "impecavel", "impecável",
}

NEGATIVE_REVIEW_TERMS = {
    "chato", "tedioso", "horrivel", "horrível", "odiei", "fraco", "ruim",
    "decepcao", "decepção", "arrastado", "pessimo", "péssimo", "bobo",
    "boring", "awful", "terrible", "horrible", "worst", "waste", "weak",
    "disappointing", "dull", "slow", "pretentious", "overrated",
}


def _review_sentiment_delta(review_text: Optional[str]) -> float:
    if not review_text:
        return 0.0
    words = set(re.findall(r"[a-zA-ZÀ-ÿ-]+", review_text.lower()))
    pos = len(words & POSITIVE_REVIEW_TERMS)
    neg = len(words & NEGATIVE_REVIEW_TERMS)
    delta = (pos - neg) * 0.35
    return max(min(delta, 1.2), -1.2)


def _rating_signal(film: dict[str, Any]) -> float:
    rating = film.get("rating")
    is_fav = bool(film.get("is_favorite"))
    liked = bool(film.get("liked"))
    rev_delta = _review_sentiment_delta(film.get("review_text"))

    if is_fav:
        base = 4.0
    elif rating is not None:
        if rating >= 5.0:
            base = 3.0
        elif rating >= 4.5:
            base = 2.4
        elif rating >= 4.0:
            base = 1.5
        elif rating >= 3.5:
            base = 0.6
        elif rating <= 1.5:
            base = -2.2
        elif rating <= 2.0:
            base = -1.6
        elif rating <= 2.5:
            base = -0.7
        else:
            base = 0.0
    else:
        base = 0.8 if liked else 0.1

    return base + rev_delta


async def _enrich_films(
    tmdb: TMDBClient, client: httpx.AsyncClient, films: list[dict[str, Any]], limit: int
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    selected = films[:limit]

    async def resolve_one(f: dict[str, Any]) -> Optional[tuple[dict[str, Any], dict[str, Any]]]:
        tid = f.get("tmdb_id")
        if not tid:
            tid = await tmdb.resolve_slug_to_tmdb(client, f["slug"], f["title"], f.get("year"))
        if not tid:
            return None
        details = await tmdb.get_movie_details(client, tid)
        if not details:
            return None
        return (f, details)

    results = await asyncio.gather(*(resolve_one(f) for f in selected))
    return [r for r in results if r is not None]


_PROFILE_CACHE: dict[tuple[str, float], dict[str, Any]] = {}


async def build_taste_profile(username: str) -> dict[str, Any]:
    user = db.get_user(username)
    cache_key = (username.lower(), float((user or {}).get("synced_at") or 0.0))
    if cache_key in _PROFILE_CACHE:
        cached = _PROFILE_CACHE[cache_key]
        return {**cached, "_internal": cached["_internal"]}

    films = db.get_user_films(username)
    watched = [f for f in films if f.get("in_watched")]
    watchlist = [f for f in films if f.get("in_watchlist") and not f.get("in_watched")]

    # Sort ALL watched films by signal strength (favorites & highest rated first) and enrich 100% of them
    ordered_watched = sorted(
        watched,
        key=lambda f: (_rating_signal(f), f.get("rating") or 0),
        reverse=True,
    )

    tmdb = TMDBClient()
    async with httpx.AsyncClient() as client:
        enriched = await _enrich_films(tmdb, client, ordered_watched, limit=len(ordered_watched))

    genre_weights: dict[int, float] = defaultdict(float)
    genre_names: dict[int, str] = {}
    director_weights: dict[int, float] = defaultdict(float)
    director_names: dict[int, str] = {}
    director_movies: dict[int, list[str]] = defaultdict(list)
    keyword_weights: dict[str, float] = defaultdict(float)
    cast_weights: dict[str, float] = defaultdict(float)
    decade_weights: dict[int, float] = defaultdict(float)
    lang_weights: dict[str, float] = defaultdict(float)

    doc_positive_count = 0
    superhero_positive_count = 0
    total_positive_count = 0
    favorites_list: list[str] = []

    for uf, movie in enriched:
        w = _rating_signal(uf)
        if uf.get("is_favorite"):
            favorites_list.append(movie["title"])
        if w > 0:
            total_positive_count += 1
        genre_ids = {g["id"] for g in movie.get("genres", [])}
        if DOCUMENTARY_GENRE_ID in genre_ids and w >= 0.6:
            doc_positive_count += 1
        if _is_superhero_movie(movie) and w >= 1.5:
            superhero_positive_count += 1

        for g in movie.get("genres", []):
            genre_weights[g["id"]] += w
            genre_names[g["id"]] = g["name"]
        for d in movie.get("directors", []):
            director_weights[d["id"]] += w
            director_names[d["id"]] = d["name"]
            if w >= 1.5:
                director_movies[d["id"]].append(movie["title"])
        for kw in movie.get("keywords", []):
            keyword_weights[kw.lower()] += w
        for actor in movie.get("cast", [])[:4]:
            cast_weights[actor.lower()] += w * 0.6
        dec = _decade(movie.get("year"))
        if dec:
            decade_weights[dec] += w
        lang = movie.get("original_language") or "en"
        lang_weights[lang] += max(w, 0)

    likes_documentary = doc_positive_count >= 2 or (
        total_positive_count > 0 and (doc_positive_count / total_positive_count) >= 0.08
    )
    likes_superhero = superhero_positive_count >= 4 and (
        total_positive_count > 0 and (superhero_positive_count / total_positive_count) >= 0.12
    )

    rated_values = [f["rating"] for f in watched if f.get("rating") is not None]
    avg_rating = round(sum(rated_values) / len(rated_values), 2) if rated_values else None

    top_genres = [
        {"id": gid, "name": genre_names[gid], "score": round(score, 1)}
        for gid, score in sorted(genre_weights.items(), key=lambda x: x[1], reverse=True)
        if score > 0
    ][:6]

    top_directors = [
        {"id": did, "name": director_names[did], "score": round(score, 1)}
        for did, score in sorted(director_weights.items(), key=lambda x: x[1], reverse=True)
        if score > 0
    ][:6]

    total_reviews = sum(1 for f in watched if f.get("review_text"))

    result = {
        "total_watched": len(watched),
        "total_watchlist": len(watchlist),
        "total_rated": len(rated_values),
        "total_reviews": total_reviews,
        "total_analyzed": len(enriched),
        "avg_rating": avg_rating,
        "favorites": favorites_list[:4],
        "likes_documentary": likes_documentary,
        "likes_superhero": likes_superhero,
        "top_genres": top_genres,
        "top_directors": top_directors,
        "_internal": {
            "genre_weights": dict(genre_weights),
            "genre_names": genre_names,
            "director_weights": dict(director_weights),
            "director_names": director_names,
            "director_movies": dict(director_movies),
            "keyword_weights": dict(keyword_weights),
            "cast_weights": dict(cast_weights),
            "decade_weights": dict(decade_weights),
            "lang_weights": dict(lang_weights),
            "seeds": enriched[:16],
            "watched": watched,
            "watchlist": watchlist,
        },
    }
    _PROFILE_CACHE[cache_key] = result
    return {**result, "_internal": result["_internal"]}


async def generate_recommendations(
    username: str,
    mood: str = "all",
    max_runtime: Optional[int] = None,
    source: str = "all",
    discovery: str = "balanced",
    limit: int = 4,
    exclude_ids: Optional[set[int]] = None,
    liked_ids: Optional[list[int]] = None,
    disliked_ids: Optional[list[int]] = None,
    seen_ids: Optional[list[int]] = None,
    skipped_ids: Optional[list[int]] = None,
) -> dict[str, Any]:
    profile = await build_taste_profile(username)
    internal = profile.pop("_internal")

    watched = internal["watched"]
    watchlist = internal["watchlist"]
    seeds = internal["seeds"]
    likes_doc = profile["likes_documentary"]

    dismissed_ids = db.get_dismissed_ids(username)
    watched_tmdb_ids = {f["tmdb_id"] for f in watched if f.get("tmdb_id")}
    watched_norm_titles = {_norm_title(f["title"]) for f in watched}

    liked_list = list(dict.fromkeys(liked_ids or []))
    disliked_list = list(dict.fromkeys(disliked_ids or []))
    seen_list = list(dict.fromkeys(seen_ids or []))
    skipped_list = list(dict.fromkeys(skipped_ids or []))

    excluded_ids = (
        watched_tmdb_ids
        | dismissed_ids
        | (exclude_ids or set())
        | set(liked_list)
        | set(disliked_list)
        | set(seen_list)
        | set(skipped_list)
    )

    if discovery == "popular":
        min_votes, max_votes = 2500, None
    elif discovery == "cult":
        min_votes, max_votes = 80, 2200
    else:
        min_votes, max_votes = 300, None

    tmdb = TMDBClient()
    candidate_ids: set[int] = set()
    seed_hits: dict[int, list[str]] = defaultdict(list)
    liked_hits: dict[int, list[str]] = defaultdict(list)
    watchlist_tmdb_ids: set[int] = set()

    # Session feedback deltas:
    # liked = strong+, seen = moderate+, skipped = mild-, disliked = strong-
    session_genre_delta: dict[int, float] = defaultdict(float)
    session_kw_delta: dict[str, float] = defaultdict(float)
    session_director_delta: dict[int, float] = defaultdict(float)

    async with httpx.AsyncClient() as client:
        feedback_ids = list(set(liked_list + disliked_list + seen_list + skipped_list))
        feedback_movies: dict[int, dict[str, Any]] = {}
        if feedback_ids:
            fb_details = await asyncio.gather(
                *(tmdb.get_movie_details(client, tid) for tid in feedback_ids)
            )
            for m in fb_details:
                if m:
                    feedback_movies[m["tmdb_id"]] = m

        for tid in liked_list:
            m = feedback_movies.get(tid)
            if not m:
                continue
            for g in m.get("genres", []):
                session_genre_delta[g["id"]] += 3.2
            for kw in m.get("keywords", []):
                session_kw_delta[kw.lower()] += 1.8
            for d in m.get("directors", []):
                session_director_delta[d["id"]] += 3.0

        for tid in disliked_list:
            m = feedback_movies.get(tid)
            if not m:
                continue
            for g in m.get("genres", []):
                session_genre_delta[g["id"]] -= 3.5
            for kw in m.get("keywords", []):
                session_kw_delta[kw.lower()] -= 2.2
            for d in m.get("directors", []):
                session_director_delta[d["id"]] -= 4.5

        for tid in seen_list:
            m = feedback_movies.get(tid)
            if not m:
                continue
            for g in m.get("genres", []):
                session_genre_delta[g["id"]] += 1.4
            for kw in m.get("keywords", []):
                session_kw_delta[kw.lower()] += 0.7

        for tid in skipped_list:
            m = feedback_movies.get(tid)
            if not m:
                continue
            for g in m.get("genres", []):
                session_genre_delta[g["id"]] -= 1.6
            for kw in m.get("keywords", []):
                session_kw_delta[kw.lower()] -= 0.8

        # 1. Watchlist sample
        wl_limit = 60 if source == "watchlist" else 20
        wl_enriched = await _enrich_films(tmdb, client, watchlist, limit=wl_limit)
        for _, m in wl_enriched:
            tid = m["tmdb_id"]
            if tid not in excluded_ids and _norm_title(m["title"]) not in watched_norm_titles:
                watchlist_tmdb_ids.add(tid)
                candidate_ids.add(tid)

        if source != "watchlist":
            # 2. TMDB recommendations from session-liked movies
            if liked_list:
                liked_rec_tasks = [tmdb.get_recommendations(client, tid) for tid in liked_list[:3]]
                liked_rec_results = await asyncio.gather(*liked_rec_tasks)
                for tid, recs in zip(liked_list[:3], liked_rec_results):
                    ref_title = (feedback_movies.get(tid) or {}).get("title", "sua escolha")
                    for r in recs[:15]:
                        rid = r["id"]
                        if rid not in excluded_ids:
                            candidate_ids.add(rid)
                            liked_hits[rid].append(ref_title)

            # 3. TMDB recommendations from user's top 14 seeds (favorites + highest rated)
            seed_tasks = [tmdb.get_recommendations(client, m["tmdb_id"]) for _, m in seeds[:14]]
            seed_results = await asyncio.gather(*seed_tasks)
            for (_, seed_movie), recs in zip(seeds[:14], seed_results):
                for r in recs[:12]:
                    rid = r["id"]
                    if rid not in excluded_ids:
                        candidate_ids.add(rid)
                        seed_hits[rid].append(seed_movie["title"])

            # 4. Top directors' unseen filmographies
            dir_tasks = []
            for d in profile["top_directors"][:3]:
                dir_tasks.append(
                    tmdb.discover_movies(
                        client,
                        {
                            "with_crew": str(d["id"]),
                            "vote_count.gte": max(min_votes // 2, 80),
                            "sort_by": "vote_average.desc",
                        },
                    )
                )
            if dir_tasks:
                dir_results = await asyncio.gather(*dir_tasks)
                for batch in dir_results:
                    for r in batch[:8]:
                        if r["id"] not in excluded_ids:
                            candidate_ids.add(r["id"])

            # 5. Rich Mood Discover (4 pages across popularity + rating) OR Top-Genre Discover
            discover_tasks = []
            if mood in MOOD_CONFIG:
                mc = MOOD_CONFIG[mood]
                without = set(mc["exclude"])
                if not likes_doc:
                    without.add(DOCUMENTARY_GENRE_ID)
                without_str = ",".join(str(g) for g in without)
                for sort_by in ("vote_average.desc", "popularity.desc"):
                    for page_num in (1, 2):
                        params: dict[str, Any] = {
                            "with_genres": "|".join(str(g) for g in mc["include"]),
                            "without_genres": without_str,
                            "vote_count.gte": min_votes,
                            "vote_average.gte": 6.6,
                            "sort_by": sort_by,
                            "page": page_num,
                        }
                        if max_votes:
                            params["vote_count.lte"] = max_votes
                        discover_tasks.append(tmdb.discover_movies(client, params))
            else:
                top_genre_ids = [
                    g["id"] for g in profile["top_genres"][:3] if g["id"] != DOCUMENTARY_GENRE_ID
                ]
                for gid in top_genre_ids[:2]:
                    for page_num in (1, 2):
                        params = {
                            "with_genres": str(gid),
                            "vote_count.gte": min_votes,
                            "vote_average.gte": 6.9,
                            "page": page_num,
                        }
                        if not likes_doc:
                            params["without_genres"] = str(DOCUMENTARY_GENRE_ID)
                        if max_votes:
                            params["vote_count.lte"] = max_votes
                        discover_tasks.append(tmdb.discover_movies(client, params))

            if discover_tasks:
                disc_results = await asyncio.gather(*discover_tasks)
                for batch in disc_results:
                    for r in batch[:20]:
                        if r["id"] not in excluded_ids:
                            candidate_ids.add(r["id"])

        prioritized_ids = sorted(
            candidate_ids,
            key=lambda tid: (
                len(liked_hits.get(tid, [])) * 3 + len(seed_hits.get(tid, [])) * 2,
                tid in watchlist_tmdb_ids,
            ),
            reverse=True,
        )[:110]

        details_list = await asyncio.gather(
            *(tmdb.get_movie_details(client, tid) for tid in prioritized_ids)
        )

    genre_weights = internal["genre_weights"]
    director_weights = internal["director_weights"]
    director_movies = internal["director_movies"]
    keyword_weights = internal["keyword_weights"]
    cast_weights = internal["cast_weights"]
    decade_weights = internal["decade_weights"]
    lang_weights = internal["lang_weights"]

    def _score_pool(strict_mood: bool, strict_votes: bool) -> list[dict[str, Any]]:
        scored_items: list[dict[str, Any]] = []
        seen_titles: set[str] = set()

        for m in details_list:
            if not m:
                continue
            tid = m["tmdb_id"]
            nt = _norm_title(m["title"])
            if tid in excluded_ids or nt in watched_norm_titles or nt in seen_titles:
                continue
            seen_titles.add(nt)

            in_wl = tid in watchlist_tmdb_ids
            if source == "watchlist" and not in_wl:
                continue

            m_genre_ids = {g["id"] for g in m.get("genres", [])}
            if DOCUMENTARY_GENRE_ID in m_genre_ids and not likes_doc and not in_wl:
                continue

            vc = m.get("vote_count") or 0
            pop = m.get("popularity") or 0.0
            if not in_wl:
                # Cult MUST NEVER leak blockbusters; Popular MUST NEVER leak obscure films
                if discovery == "cult":
                    if vc < 60 or vc > 2200 or pop > 55:
                        continue
                elif discovery == "popular":
                    if vc < (2500 if strict_votes else 1500):
                        continue
                else:
                    if strict_votes and vc < min_votes:
                        continue
                    if vc < 80:
                        continue

            rt = m.get("runtime") or 0
            if max_runtime and rt > 0 and rt > max_runtime:
                continue

            if mood in MOOD_CONFIG:
                mc = MOOD_CONFIG[mood]
                if not (m_genre_ids & mc["include"]):
                    continue
                if strict_mood and (m_genre_ids & mc["exclude"]):
                    continue

            score = 0.0
            reasons: list[str] = []

            l_hits = liked_hits.get(tid, [])
            if l_hits:
                score += len(l_hits) * 5.0
                reasons.append(f"Na vibe de {l_hits[0]}")

            hits = seed_hits.get(tid, [])
            if hits:
                # Multi-seed consensus is the strongest taste signal
                score += len(hits) * 3.5 + (2.0 if len(hits) >= 2 else 0.0)
                unique_hits = list(dict.fromkeys(hits))[:2]
                if len(reasons) < 2:
                    if len(unique_hits) == 1:
                        reasons.append(f"Semelhante a {unique_hits[0]}")
                    else:
                        reasons.append(f"Combina com {unique_hits[0]} e {unique_hits[1]}")

            for d in m.get("directors", []):
                dw = director_weights.get(d["id"], 0.0) + session_director_delta.get(d["id"], 0.0)
                if dw > 0:
                    score += min(dw * 1.6, 5.0)
                    ref = director_movies.get(d["id"], [])
                    if len(reasons) < 2:
                        reasons.append(f"Mesmo diretor de {ref[0]}" if ref else f"Dirigido por {d['name']}")
                elif dw < 0:
                    score += max(dw * 1.5, -6.0)
                break

            matched_genres = []
            for g in m.get("genres", []):
                gw = genre_weights.get(g["id"], 0.0)
                score += max(min(gw * 0.35, 2.2), -2.0)
                score += max(min(session_genre_delta.get(g["id"], 0.0), 4.5), -5.0)
                if gw >= 2.0:
                    matched_genres.append(g["name"])
            if matched_genres and len(reasons) < 2:
                reasons.append(f"Seu estilo: {', '.join(matched_genres[:2])}")

            for kw in m.get("keywords", []):
                kl = kw.lower()
                score += max(min(keyword_weights.get(kl, 0.0) * 0.5, 1.5), -1.5)
                score += max(min(session_kw_delta.get(kl, 0.0), 3.0), -3.5)

            for actor in m.get("cast", [])[:4]:
                score += max(min(cast_weights.get(actor.lower(), 0.0) * 0.35, 1.2), -1.0)

            dec = _decade(m.get("year"))
            if dec and decade_weights.get(dec, 0) > 0:
                score += min(decade_weights[dec] * 0.12, 1.0)

            va = m.get("vote_average") or 0.0
            score += (va - 6.2) * 0.9 + math.log10(max(vc, 10)) * 0.35

            lang = m.get("original_language") or "en"
            if lang != "en" and lang_weights.get(lang, 0) > 0:
                score += 0.8

            if in_wl:
                score += 1.6
                reasons.insert(0, "Na sua Watchlist")

            # Strongly limit superhero movies unless user clearly loves them
            if _is_superhero_movie(m) and not profile.get("likes_superhero") and not in_wl:
                score -= 5.5

            if not reasons:
                reasons.append(f"Nota {va} alinhada ao seu perfil")

            scored_items.append(
                {
                    **m,
                    "in_watchlist": in_wl,
                    "match_score": round(score, 2),
                    "reasons": reasons[:2],
                    "letterboxd_url": f"https://letterboxd.com/tmdb/{tid}/",
                }
            )

        scored_items.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_items

    # Multi-tier selection to GUARANTEE exact `limit` (4) results whenever possible
    final: list[dict[str, Any]] = []
    chosen_ids: set[int] = set()
    director_counts: dict[str, int] = defaultdict(int)

    tiers = [
        (True, True, 1),    # Tier 1: strict mood, strict votes, max 1 per director
        (True, False, 2),   # Tier 2: strict mood, relaxed votes, max 2 per director
        (False, False, 3),  # Tier 3: relaxed mood exclude, relaxed votes
    ]

    total_evaluated = 0
    for strict_mood, strict_votes, max_per_dir in tiers:
        if len(final) >= limit:
            break
        pool = _score_pool(strict_mood=strict_mood, strict_votes=strict_votes)
        total_evaluated = max(total_evaluated, len(pool))
        for item in pool:
            if item["tmdb_id"] in chosen_ids:
                continue
            d_key = item["directors"][0]["name"] if item.get("directors") else None
            if d_key and director_counts[d_key] >= max_per_dir:
                continue
            if d_key:
                director_counts[d_key] += 1
            chosen_ids.add(item["tmdb_id"])
            final.append(item)
            if len(final) >= limit:
                break

    # Fetch real IMDb and Letterboxd ratings for the final 4 movies (cached in SQLite)
    await tmdb.enrich_external_ratings(final)

    return {
        "profile": profile,
        "recommendations": final,
        "total_candidates_evaluated": total_evaluated,
    }

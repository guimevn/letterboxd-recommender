import csv
import io
import os
import re
import zipfile
from typing import Optional
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from app import db
from app.letterboxd import LetterboxdError, scrape_user_profile
from app.recommender import generate_recommendations

app = FastAPI(title="Letterboxd Recommender", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,40}$")


def _validate_username(username: str) -> str:
    uname = username.strip().lstrip("@").lower()
    if not USERNAME_RE.match(uname):
        raise HTTPException(status_code=400, detail="Username inválido.")
    return uname


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/config.js")
def serve_config_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "config.js"), media_type="application/javascript")


@app.get("/app.js")
def serve_app_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"), media_type="application/javascript")


@app.post("/api/sync/{username}")
async def sync_user(username: str):
    uname = _validate_username(username)
    try:
        profile_data = await scrape_user_profile(uname)
    except LetterboxdError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Não foi possível acessar o Letterboxd agora. Tente novamente em instantes.",
        )

    db.save_user_profile(
        username=profile_data["username"],
        display_name=profile_data["display_name"],
        avatar_url=profile_data["avatar_url"],
        films=profile_data["films"],
    )
    return db.get_user(uname)


def _parse_id_list(raw: Optional[str]) -> list[int]:
    if not raw:
        return []
    out = []
    for part in raw.split(","):
        p = part.strip()
        if p.isdigit():
            out.append(int(p))
    return out


@app.get("/api/recommendations/{username}")
async def get_recommendations(
    username: str,
    mood: str = Query("all", pattern="^(all|light|intense|thoughtful|epic)$"),
    max_runtime: Optional[int] = Query(None, ge=60, le=300),
    source: str = Query("all", pattern="^(all|watchlist)$"),
    discovery: str = Query("balanced", pattern="^(popular|balanced|cult)$"),
    limit: int = Query(4, ge=1, le=12),
    exclude_ids: Optional[str] = Query(None),
    liked_ids: Optional[str] = Query(None),
    disliked_ids: Optional[str] = Query(None),
    seen_ids: Optional[str] = Query(None),
    skipped_ids: Optional[str] = Query(None),
    lang: str = Query("pt", pattern="^(pt|en|es|fr)$"),
    region: str = Query("BR", min_length=2, max_length=2),
):
    uname = _validate_username(username)
    user = db.get_user(uname)
    if not user:
        try:
            profile_data = await scrape_user_profile(uname)
            db.save_user_profile(
                username=profile_data["username"],
                display_name=profile_data["display_name"],
                avatar_url=profile_data["avatar_url"],
                films=profile_data["films"],
            )
            user = db.get_user(uname)
        except LetterboxdError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="Erro ao sincronizar perfil do Letterboxd.",
            )

    try:
        result = await generate_recommendations(
            username=uname,
            mood=mood,
            max_runtime=max_runtime,
            source=source,
            discovery=discovery,
            limit=limit,
            exclude_ids=set(_parse_id_list(exclude_ids)),
            liked_ids=_parse_id_list(liked_ids),
            disliked_ids=_parse_id_list(disliked_ids),
            seen_ids=_parse_id_list(seen_ids),
            skipped_ids=_parse_id_list(skipped_ids),
            lang=lang,
            region=region.upper(),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {"user": user, **result}


class DismissBody(BaseModel):
    reason: str = "not_interested"


@app.post("/api/dismiss/{username}/{tmdb_id}")
def dismiss_film(username: str, tmdb_id: int, body: DismissBody):
    uname = _validate_username(username)
    reason = body.reason if body.reason in ("seen", "not_interested", "disliked") else "not_interested"
    db.dismiss_movie(uname, tmdb_id, reason)
    return {"ok": True, "tmdb_id": tmdb_id, "reason": reason}


def _slug_from_lb_uri(uri: str, title: str) -> str:
    m = re.search(r"/film/([^/]+)/?", uri or "")
    if m:
        return m.group(1)
    return re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")


@app.post("/api/import/{username}")
async def import_letterboxd_zip(username: str, file: UploadFile = File(...)):
    """Optional full-profile import from official Letterboxd .zip export (100% watched + watchlist + reviews)."""
    uname = _validate_username(username)
    raw = await file.read()
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Arquivo muito grande (limite 20MB).")

    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Envie o arquivo .zip exportado do Letterboxd.")

    merged: dict[str, dict] = {}

    def _read_csv(name: str):
        for zname in zf.namelist():
            if zname.endswith(name):
                with zf.open(zname) as fh:
                    return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace")))
        return []

    def _ensure(row: dict) -> Optional[dict]:
        title = (row.get("Name") or "").strip()
        if not title:
            return None
        slug = _slug_from_lb_uri(row.get("Letterboxd URI", ""), title)
        year_s = (row.get("Year") or "").strip()
        year = int(year_s) if year_s.isdigit() else None
        if slug not in merged:
            merged[slug] = {
                "slug": slug,
                "title": title,
                "year": year,
                "rating": None,
                "liked": False,
                "is_favorite": False,
                "in_watched": False,
                "in_watchlist": False,
                "review_text": None,
            }
        return merged[slug]

    for row in _read_csv("watched.csv"):
        f = _ensure(row)
        if f:
            f["in_watched"] = True

    for row in _read_csv("ratings.csv"):
        f = _ensure(row)
        if f:
            f["in_watched"] = True
            try:
                f["rating"] = float(row.get("Rating") or 0) or None
            except ValueError:
                pass

    for row in _read_csv("reviews.csv"):
        f = _ensure(row)
        if f:
            f["in_watched"] = True
            txt = (row.get("Review") or "").strip()
            if txt:
                f["review_text"] = txt

    for row in _read_csv("watchlist.csv"):
        f = _ensure(row)
        if f:
            f["in_watchlist"] = True

    for row in _read_csv("likes/films.csv"):
        f = _ensure(row)
        if f:
            f["liked"] = True

    if not merged:
        raise HTTPException(status_code=400, detail="Nenhum CSV do Letterboxd encontrado dentro do .zip.")

    existing = db.get_user(uname) or {}
    db.save_user_profile(
        username=uname,
        display_name=existing.get("display_name") or uname,
        avatar_url=existing.get("avatar_url"),
        films=list(merged.values()),
    )
    return db.get_user(uname)

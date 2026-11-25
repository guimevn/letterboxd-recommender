import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
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


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


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

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import db
from app.letterboxd import scrape_user_profile
from app.recommender import generate_recommendations


async def main() -> None:
    db.init_db()
    username = sys.argv[1] if len(sys.argv) > 1 else "guickz"
    print(f"Syncing @{username}...")
    p = await scrape_user_profile(username)
    films = p["films"]
    watched = [f for f in films if f["in_watched"]]
    wl = [f for f in films if f["in_watchlist"]]
    favs = [f for f in films if f["is_favorite"]]
    rated = [f for f in films if f["rating"] is not None]
    print(
        f"User: {p['display_name']} | Watched: {len(watched)} | Watchlist: {len(wl)} | "
        f"Favs: {len(favs)} | Rated: {len(rated)}"
    )
    assert len(watched) > 0, "Expected watched films"

    db.save_user_profile(p["username"], p["display_name"], p["avatar_url"], films)

    res = await generate_recommendations(username, limit=8)
    prof = res["profile"]
    recs = res["recommendations"]
    print("Top genres:", [g["name"] for g in prof["top_genres"]])
    print("Likes documentary:", prof["likes_documentary"])
    print(f"Recommendations ({len(recs)}):")
    watched_titles = {f["title"].lower() for f in watched}
    for r in recs:
        assert r["title"].lower() not in watched_titles, f"Repeated watched film: {r['title']}"
        print(f"  - {r['title']} ({r['year']}) [WL={r['in_watchlist']}] -> {r['reasons']}")
    assert len(recs) > 0, "Expected at least 1 recommendation"
    print("ALL CHECKS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())

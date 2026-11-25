import asyncio
import re
from typing import Any, Optional
from bs4 import BeautifulSoup
import httpx

try:
    from curl_cffi.requests import AsyncSession as CffiAsyncSession
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False

BASE_URL = "https://letterboxd.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
}

RATING_RE = re.compile(r"rated-(\d+)")


class LetterboxdError(Exception):
    pass


async def _fetch_html(client: Any, url: str) -> tuple[int, str]:
    resp = await client.get(url, headers=HEADERS, timeout=20)
    return resp.status_code, resp.text


def _parse_poster_item(li) -> Optional[dict[str, Any]]:
    div = (
        li.find("div", attrs={"data-item-slug": True})
        or li.find("div", attrs={"data-film-slug": True})
        or li.find("div", attrs={"data-target-link": True})
    )
    slug = None
    title = None

    if div:
        slug = div.get("data-item-slug") or div.get("data-film-slug")
        if not slug and div.get("data-target-link"):
            slug = div["data-target-link"].strip("/").split("film/")[-1].strip("/")
        title = div.get("data-item-name") or div.get("data-film-name")

    if not slug:
        a = li.find("a", href=True)
        if a and "/film/" in a["href"]:
            slug = a["href"].split("/film/")[1].strip("/")

    img = li.find("img")
    if not title and img and img.get("alt"):
        title = img["alt"].strip()

    if not slug or not title:
        return None

    # Clean trailing year from title if present like "Inception (2010)"
    year = None
    year_match = re.search(r"\((\d{4})\)\s*$", title)
    if year_match:
        year = int(year_match.group(1))
        title = title[: year_match.start()].strip()

    rating = None
    rating_span = li.find("span", class_=lambda c: c and "rated-" in c)
    if rating_span:
        for cls in rating_span.get("class", []):
            m = RATING_RE.match(cls)
            if m:
                rating = int(m.group(1)) / 2.0
                break

    liked = bool(li.find("span", class_=lambda c: c and ("like" in c or "icon-liked" in c)))

    return {
        "slug": slug,
        "title": title,
        "year": year,
        "rating": rating,
        "liked": liked,
    }


def _extract_max_page(soup: BeautifulSoup) -> int:
    pages = soup.select("div.paginate-pages li.paginate-page a")
    if not pages:
        return 1
    nums = []
    for a in pages:
        txt = a.get_text(strip=True)
        if txt.isdigit():
            nums.append(int(txt))
    return max(nums) if nums else 1


def _extract_films_from_soup(soup: BeautifulSoup) -> list[dict[str, Any]]:
    items = soup.select("li.poster-container, li.griditem")
    films = []
    for li in items:
        parsed = _parse_poster_item(li)
        if parsed:
            films.append(parsed)
    return films


def _extract_reviews_from_soup(soup: BeautifulSoup) -> dict[str, str]:
    reviews: dict[str, str] = {}
    for item in soup.select("li.film-detail, article.production-viewing"):
        slug = None
        div = item.find("div", attrs={"data-item-slug": True}) or item.find("div", attrs={"data-film-slug": True})
        if div:
            slug = div.get("data-item-slug") or div.get("data-film-slug")
        if not slug:
            a = item.find("a", href=lambda h: h and "/film/" in h)
            if a:
                slug = a["href"].split("/film/")[1].strip("/")
        body = item.select_one("div.body-text, div.review-body")
        if slug and body:
            text = body.get_text(" ", strip=True)
            if text:
                if slug in reviews:
                    reviews[slug] = f"{reviews[slug]} {text}"
                else:
                    reviews[slug] = text
    return reviews


async def _fetch_all_reviews(client: Any, uname: str, sem: asyncio.Semaphore) -> dict[str, str]:
    status, html = await _fetch_html(client, f"{BASE_URL}/{uname}/films/reviews/page/1/")
    if status != 200:
        return {}

    soup = BeautifulSoup(html, "lxml")
    all_reviews = _extract_reviews_from_soup(soup)
    max_page = _extract_max_page(soup)

    if max_page <= 1:
        return all_reviews

    async def fetch_page(page: int) -> dict[str, str]:
        async with sem:
            await asyncio.sleep(0.15)
            st, body = await _fetch_html(client, f"{BASE_URL}/{uname}/films/reviews/page/{page}/")
            if st != 200:
                return {}
            return _extract_reviews_from_soup(BeautifulSoup(body, "lxml"))

    results = await asyncio.gather(*(fetch_page(p) for p in range(2, max_page + 1)))
    for page_revs in results:
        for slug, text in page_revs.items():
            if slug in all_reviews:
                all_reviews[slug] = f"{all_reviews[slug]} {text}"
            else:
                all_reviews[slug] = text
    return all_reviews


async def _fetch_all_pages(client: Any, base_path: str, sem: asyncio.Semaphore) -> list[dict[str, Any]]:
    status, html = await _fetch_html(client, f"{BASE_URL}{base_path}page/1/")
    if status != 200:
        return []

    soup = BeautifulSoup(html, "lxml")
    films = _extract_films_from_soup(soup)
    max_page = _extract_max_page(soup)

    if max_page <= 1:
        return films

    async def fetch_page(page: int) -> list[dict[str, Any]]:
        async with sem:
            await asyncio.sleep(0.15)
            st, body = await _fetch_html(client, f"{BASE_URL}{base_path}page/{page}/")
            if st != 200:
                return []
            return _extract_films_from_soup(BeautifulSoup(body, "lxml"))

    tasks = [fetch_page(p) for p in range(2, max_page + 1)]
    results = await asyncio.gather(*tasks)
    for page_films in results:
        films.extend(page_films)
    return films


async def scrape_user_profile(username: str) -> dict[str, Any]:
    uname = username.strip().lstrip("@").lower()
    if not uname or not re.match(r"^[a-z0-9_.-]+$", uname):
        raise LetterboxdError("Username inválido.")

    sem = asyncio.Semaphore(4)

    async def _run(client: Any) -> dict[str, Any]:
        status, html = await _fetch_html(client, f"{BASE_URL}/{uname}/")
        if status == 404:
            raise LetterboxdError(f"Usuário '{uname}' não encontrado no Letterboxd.")
        if status != 200:
            raise LetterboxdError(
                f"Letterboxd retornou status {status}. Tente novamente em alguns segundos."
            )

        soup = BeautifulSoup(html, "lxml")

        # Display name & avatar
        h1 = soup.select_one("h1.title-1, span.displayname")
        display_name = h1.get_text(strip=True) if h1 else uname
        avatar_img = soup.select_one("span.avatar img, .profile-avatar img")
        avatar_url = avatar_img["src"] if avatar_img and avatar_img.get("src") else None

        # Favorite films (0 to 4)
        fav_section = soup.select_one("section#favourites")
        fav_slugs: set[str] = set()
        fav_films: list[dict[str, Any]] = []
        if fav_section:
            for li in fav_section.select("li.griditem, li.poster-container, li.favourite-production-poster-container"):
                parsed = _parse_poster_item(li)
                if parsed and parsed["slug"] not in fav_slugs:
                    fav_slugs.add(parsed["slug"])
                    fav_films.append(parsed)

        # Fetch all watched films, watchlist, and reviews concurrently
        watched_films, watchlist_films, reviews_map = await asyncio.gather(
            _fetch_all_pages(client, f"/{uname}/films/", sem),
            _fetch_all_pages(client, f"/{uname}/watchlist/", sem),
            _fetch_all_reviews(client, uname, sem),
        )

        # Merge by slug (zero duplicates)
        merged: dict[str, dict[str, Any]] = {}

        for f in watched_films:
            slug = f["slug"]
            merged[slug] = {
                **f,
                "in_watched": True,
                "in_watchlist": False,
                "is_favorite": slug in fav_slugs,
                "review_text": reviews_map.get(slug),
            }

        for f in fav_films:
            slug = f["slug"]
            if slug in merged:
                merged[slug]["is_favorite"] = True
                merged[slug]["in_watched"] = True
            else:
                merged[slug] = {
                    **f,
                    "in_watched": True,
                    "in_watchlist": False,
                    "is_favorite": True,
                    "review_text": reviews_map.get(slug),
                }

        for f in watchlist_films:
            slug = f["slug"]
            if slug in merged:
                merged[slug]["in_watchlist"] = True
            else:
                merged[slug] = {
                    **f,
                    "in_watched": False,
                    "in_watchlist": True,
                    "is_favorite": False,
                    "review_text": reviews_map.get(slug),
                }

        if not merged:
            raise LetterboxdError(
                f"Nenhum filme encontrado para '{uname}'. Verifique se o perfil é público."
            )

        return {
            "username": uname,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "films": list(merged.values()),
        }

    if HAS_CURL_CFFI:
        async with CffiAsyncSession(impersonate="chrome") as client:
            return await _run(client)
    else:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            return await _run(client)

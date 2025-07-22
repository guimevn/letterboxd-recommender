import requests
from bs4 import BeautifulSoup
import random
import time

def get_watchlist_films(username: str):
    """
    Busca TODOS os filmes da watchlist com título E slug para links
    """
    all_films = []
    page = 1
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    while True:
        url = f"https://letterboxd.com/{username}/watchlist/page/{page}/"
        print(f"📄 Buscando página {page}...")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                if page == 1:
                    return None
                else:
                    break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_films = extract_films_with_links(soup)
            
            if not page_films:
                break
            
            print(f"   🎬 Encontrou {len(page_films)} filmes")
            all_films.extend(page_films)
            
            next_link = soup.find('a', class_='next')
            if not next_link and len(page_films) < 28:
                break
            
            page += 1
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Erro na página {page}: {e}")
            if page == 1:
                return None
            break
    
    print(f"✅ Total: {len(all_films)} filmes encontrados")
    return all_films if all_films else None

def extract_films_with_links(soup):
    """
    Extrai filmes COM título e slug para criar links
    """
    films = []
    
    film_posters = soup.find_all('li', class_='poster-container')
    
    for poster in film_posters:
        film_data = {}
        
        img_tag = poster.find('img')
        if img_tag and 'alt' in img_tag.attrs:
            film_data['titulo'] = img_tag['alt']
        
        link_tag = poster.find('a', class_='frame')
        if link_tag and 'href' in link_tag.attrs:
            href = link_tag['href']
            film_data['slug'] = href.strip('/')  # Remove as barras
        else:
            div_tag = poster.find('div', attrs={'data-film-slug': True})
            if div_tag:
                film_data['slug'] = f"film/{div_tag['data-film-slug']}"
        
        if 'titulo' in film_data and 'slug' in film_data:
            films.append(film_data)
        elif 'titulo' in film_data:
            film_data['slug'] = None
            films.append(film_data)
    
    return films


def sortear_filme_completo(username: str):
    """
    Sorteia um filme e retorna dados completos (título + link)
    """
    watchlist = get_watchlist_films(username)
    if not watchlist:
        return None
    
    filme_sorteado = random.choice(watchlist)
    return filme_sorteado

# test
if __name__ == "__main__":
    print("🚀 Testando scraper com links...\n")
    
    filme = sortear_filme_completo("dave")
    if filme:
        print(f"🎬 Filme sorteado: {filme['titulo']}")
        if filme['slug']:
            print(f"🔗 Link: https://letterboxd.com/{filme['slug']}")
        else:
            print("🔗 Link não disponível")
    else:
        print("❌ Erro ao buscar filme")
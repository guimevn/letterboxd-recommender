from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
from scraper import get_watchlist_films, sortear_filme_completo

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Olá! Este é o servidor do recomendador de filmes."}

@app.get("/sortear/{username}")
def sortear_filme(username: str):
    filme_data = sortear_filme_completo(username)
    
    if not filme_data:
        return {
            "erro": "Usuário não encontrado ou watchlist vazia/privada",
            "usuario": username
        }
    
    response = {
        "usuario": username,
        "filme_sorteado": filme_data['titulo']
    }
    
    if filme_data['slug']:
        response["filme_link"] = f"https://letterboxd.com/{filme_data['slug']}"
    
    return response

@app.get("/watchlist/{username}")
def ver_watchlist_completa(username: str):
    watchlist = get_watchlist_films(username)
    
    if not watchlist:
        return {
            "erro": "Usuário não encontrado ou watchlist vazia/privada",
            "usuario": username
        }
    
    return {
        "usuario": username,
        "watchlist": watchlist,
        "total_filmes": len(watchlist)
    }
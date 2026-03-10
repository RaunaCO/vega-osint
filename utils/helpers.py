import re
import json
import os
import aiohttp
import feedparser
from config.settings import FEEDS_NOTICIAS

VISTOS_PATH = "data/vistos.json"

def limpiar_html(texto: str) -> str:
    return re.sub(r'<[^>]+>', '', texto).strip()

def cargar_vistos() -> set:
    if os.path.exists(VISTOS_PATH):
        with open(VISTOS_PATH, "r") as f:
            return set(json.load(f))
    return set()

def guardar_vistos(vistos: set):
    with open(VISTOS_PATH, "w") as f:
        json.dump(list(vistos), f)

async def buscar_noticias_relevantes(tema: str, max_noticias: int = 8) -> list:
    palabras = re.split(r'[\s\-,]+', tema.lower())
    noticias_encontradas = []

    async with aiohttp.ClientSession() as session:
        for fuente, url in FEEDS_NOTICIAS.items():
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    contenido = await resp.text()
                    feed = feedparser.parse(contenido)

                    for entrada in feed.entries[:15]:
                        titulo = entrada.get("title", "")
                        resumen = limpiar_html(entrada.get("summary", ""))[:300]
                        link = entrada.get("link", "")
                        titulo_lower = titulo.lower()

                        if any(p in titulo_lower or p in resumen.lower() for p in palabras):
                            noticias_encontradas.append(
                                f"[{fuente}] {titulo}\n{resumen}\nFuente: {link}"
                            )
            except Exception as e:
                print(f"[VEGA] Error en feed {fuente}: {e}")

    return noticias_encontradas[:max_noticias]

async def obtener_feed_nitter(session, cuenta: str, instancias: list):
    for instancia in instancias:
        url = f"{instancia}/{cuenta}/rss"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status == 200:
                    contenido = await resp.text()
                    feed = feedparser.parse(contenido)
                    if feed.entries:
                        return feed
        except:
            continue
    return None
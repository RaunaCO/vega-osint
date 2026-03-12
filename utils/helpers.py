import re
import json
import os
import aiohttp
import feedparser
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from config.settings import FEEDS_NOTICIAS

VISTOS_PATH = "data/vistos.json"

def limpiar_html(texto: str) -> str:
    return re.sub(r'<[^>]+>', '', texto).strip()

def detectar_y_traducir(texto: str):    if not texto or len(texto) < 10:
        return texto, False
    try:
        idioma = detect(texto)
        if idioma == "es":
            return texto, False
        traducido = GoogleTranslator(source="auto", target="es").translate(texto)
        return traducido, True
    except LangDetectException:
        return texto, False
    except Exception as e:
        print(f"[VEGA] Error de traducción: {e}")
        return texto, False

def cargar_vistos() -> set:
    if os.path.exists(VISTOS_PATH):
        with open(VISTOS_PATH, "r") as f:
            return set(json.load(f))
    return set()

def guardar_vistos(vistos: set):
    with open(VISTOS_PATH, "w") as f:
        json.dump(list(vistos), f)

def extraer_imagen(entrada) -> str:
    if hasattr(entrada, "media_content") and entrada.media_content:
        for media in entrada.media_content:
            if media.get("type", "").startswith("image"):
                return media.get("url", "")

    if hasattr(entrada, "media_thumbnail") and entrada.media_thumbnail:
        return entrada.media_thumbnail[0].get("url", "")

    summary_raw = entrada.get("summary", "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary_raw)
    if match:
        return match.group(1)

    return ""

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
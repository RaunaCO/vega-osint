import discord
from discord.ext import commands
from groq import Groq
import aiohttp
import feedparser
import re
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

cliente_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

FEEDS_NOTICIAS = {
    "BBC World":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera":       "https://www.aljazeera.com/xml/rss/all.xml",
    "DW World":         "https://rss.dw.com/rdf/rss-en-world",
    "Kyiv Independent": "https://kyivindependent.com/feed/",
}

SYSTEM_PROMPT = """Eres VEGA, un sistema de inteligencia artificial especializado en análisis de conflictos geopolíticos y operaciones militares.

Tu función es generar SITREPs (Situational Reports) con el siguiente formato estricto:

**CLASIFICACIÓN:** VEGA-INTEL // NO DISTRIBUIR
**FECHA/HORA:** [UTC actual]
**ÁREA DE OPERACIONES:** [región identificada]

**RESUMEN EJECUTIVO:**
[2-3 oraciones con el estado actual de la situación]

**DESARROLLOS CLAVE:**
- [punto 1]
- [punto 2]
- [punto 3]

**EVALUACIÓN DE AMENAZA:** [CRÍTICA / ALTA / MEDIA / BAJA]

**TENDENCIA:** [ESCALANDO / ESTABLE / DESESCALANDO]

**OBSERVACIONES FINALES:**
[1-2 oraciones con proyección a corto plazo]

Responde siempre en español. Tono: técnico, directo, sin adornos.
Basa tu análisis ÚNICAMENTE en las noticias reales que se te proporcionan.
Si no hay suficiente información, indícalo claramente."""

def limpiar_html(texto):
    return re.sub(r'<[^>]+>', '', texto).strip()

async def buscar_noticias_relevantes(tema: str, max_noticias: int = 8):
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

                        if any(palabra in titulo_lower or palabra in resumen.lower() for palabra in palabras):
                            noticias_encontradas.append(
                                f"[{fuente}] {titulo}\n{resumen}\nFuente: {link}"
                            )

            except Exception as e:
                print(f"[VEGA] Error buscando en {fuente}: {e}")

    return noticias_encontradas[:max_noticias]

class AIBrain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(guild_ids=[int(os.getenv("GUILD_ID"))], description="Genera un SITREP basado en noticias reales")
    async def sitrep(self, ctx, tema: str):
        await ctx.defer()

        try:
            # Paso 1 — Buscar noticias reales sobre el tema
            await ctx.edit(content="📡 **VEGA** — Recopilando inteligencia de fuentes activas...")
            noticias = await buscar_noticias_relevantes(tema)

            if not noticias:
                contexto = f"No se encontraron noticias recientes específicas sobre '{tema}' en los feeds activos. Indica esto claramente en el SITREP y genera un análisis basado en contexto histórico conocido, marcando cada afirmación como [CONTEXTO HISTÓRICO]."
            else:
                contexto = "NOTICIAS REALES RECOPILADAS:\n\n" + "\n\n---\n\n".join(noticias)

            # Paso 2 — Generar SITREP con las noticias reales como contexto
            respuesta = cliente_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Fecha y hora actual: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nTema del SITREP: {tema}\n\n{contexto}"}
                ],
                max_tokens=1024,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content

            if len(contenido) > 4000:
                contenido = contenido[:4000] + "\n\n*[REPORTE TRUNCADO]*"

            fuentes_usadas = len(noticias)
            embed = discord.Embed(
                title=f"📋 SITREP — {tema.upper()}",
                description=contenido,
                color=0x00ff41,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"VEGA OSINT • {fuentes_usadas} fuentes analizadas — Verificar fuentes primarias")
            await ctx.respond(embed=embed)

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error en el módulo de IA: `{e}`")

    @discord.slash_command(guild_ids=[int(os.getenv("GUILD_ID"))], description="Analiza un texto o noticia con IA")
    async def analizar(self, ctx, texto: str):
        await ctx.defer()

        try:
            respuesta = cliente_groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Fecha y hora actual: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nAnaliza este texto desde una perspectiva de inteligencia geopolítica y evalúa su importancia operacional:\n\n{texto}"}
                ],
                max_tokens=800,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content

            embed = discord.Embed(
                title="🧠 ANÁLISIS DE INTELIGENCIA",
                description=contenido,
                color=0x7700ff,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="VEGA OSINT • Análisis generado por IA — Verificar fuentes primarias")
            await ctx.respond(embed=embed)

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error en el módulo de IA: `{e}`")

def setup(bot):
    bot.add_cog(AIBrain(bot))
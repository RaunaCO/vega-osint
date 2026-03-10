import discord
from discord.ext import commands, tasks
import aiohttp
import feedparser
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

CONFLICT_CHANNEL_ID = int(os.getenv("CONFLICT_CHANNEL_ID"))

FEEDS = {
    "Reuters": "https://feeds.reuters.com/reuters/worldNews",
    "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}

PALABRAS_CLAVE = [
    "war", "conflict", "attack", "strike", "missile",
    "troops", "invasion", "crisis", "bomb", "killed",
    "guerra", "conflicto", "ataque", "misil", "invasión"
]

class Intel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.noticias_vistas = set()
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    @tasks.loop(minutes=15)
    async def monitor(self):
        canal = self.bot.get_channel(CONFLICT_CHANNEL_ID)
        if not canal:
            return

        async with aiohttp.ClientSession() as session:
            for fuente, url in FEEDS.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        contenido = await resp.text()
                        feed = feedparser.parse(contenido)

                        for entrada in feed.entries[:5]:
                            titulo = entrada.get("title", "")
                            link = entrada.get("link", "")
                            resumen = entrada.get("summary", "Sin resumen disponible")[:300]

                            if link in self.noticias_vistas:
                                continue

                            titulo_lower = titulo.lower()
                            es_relevante = any(palabra in titulo_lower for palabra in PALABRAS_CLAVE)

                            if es_relevante:
                                self.noticias_vistas.add(link)

                                embed = discord.Embed(
                                    title=f"📡 {titulo}",
                                    url=link,
                                    description=resumen + "...",
                                    color=0xff4444
                                )
                                embed.set_author(name=f"INTEL FEED — {fuente}")
                                embed.set_footer(text=f"VEGA OSINT • {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
                                await canal.send(embed=embed)

                except Exception as e:
                    print(f"[VEGA] Error en feed {fuente}: {e}")

    @monitor.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()

    @discord.slash_command(guild_ids=[int(os.getenv("GUILD_ID"))], description="Escanea noticias de conflictos ahora mismo")
    async def scanfeed(self, ctx):
        await ctx.defer()
        await ctx.respond("📡 **VEGA** — Escaneando feeds de inteligencia... Los resultados aparecerán en `#conflict-watch`.")
        await self.monitor()

def setup(bot):
    bot.add_cog(Intel(bot))
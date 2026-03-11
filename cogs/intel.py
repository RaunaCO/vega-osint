import discord
import feedparser
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from config.settings import GUILD_ID, CONFLICT_CHANNEL_ID, FEEDS_NOTICIAS, PALABRAS_CLAVE, PALABRAS_CRITICAS
from utils.helpers import limpiar_html, cargar_vistos, guardar_vistos, detectar_y_traducir

class Intel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vistos = cargar_vistos()
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    async def ejecutar_escaneo(self):
        canal = self.bot.get_channel(CONFLICT_CHANNEL_ID)
        if not canal:
            return

        async with aiohttp.ClientSession() as session:
            for fuente, url in FEEDS_NOTICIAS.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        feed = feedparser.parse(await resp.text())

                        for entrada in feed.entries[:5]:
                            titulo = entrada.get("title", "")
                            link = entrada.get("link", "")
                            resumen = limpiar_html(entrada.get("summary", ""))[:300]

                            if link in self.vistos:
                                continue

                            if any(p in titulo.lower() for p in PALABRAS_CLAVE):
                                self.vistos.add(link)
                                guardar_vistos(self.vistos)

                                titulo_final, titulo_traducido = detectar_y_traducir(titulo)
                                resumen_final, resumen_traducido = detectar_y_traducir(resumen)
                                fue_traducido = titulo_traducido or resumen_traducido

                                es_critica = any(p in titulo.lower() for p in PALABRAS_CRITICAS)
                                color = 0xff0000 if es_critica else 0xff8800
                                nivel = "🔴 ALERTA CRÍTICA" if es_critica else "🟠 CONFLICTO"

                                embed = discord.Embed(title=f"📡 {titulo_final}", url=link, description=resumen_final + "...", color=color)
                                embed.set_author(name=f"{nivel} — {fuente}")
                                pie = f"VEGA OSINT • {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
                                if fue_traducido:
                                    pie += " • 🌐 Traducido automáticamente"
                                embed.set_footer(text=pie)
                                await canal.send(embed=embed)
                except Exception as e:
                    print(f"[VEGA] Error en feed {fuente}: {e}")

    @tasks.loop(minutes=5)
    async def monitor(self):
        await self.ejecutar_escaneo()

    @monitor.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()

    @discord.slash_command(guild_ids=[GUILD_ID], description="Escanea todas las fuentes ahora mismo")
    async def scanfeed(self, ctx):
        await ctx.defer()
        await ctx.respond("📡 **VEGA** — Escaneando fuentes... Resultados en `#conflict-watch`.")
        await self.ejecutar_escaneo()

def setup(bot):
    bot.add_cog(Intel(bot))
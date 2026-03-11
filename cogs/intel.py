import discord
import feedparser
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from groq import Groq
from config.settings import GUILD_ID, CONFLICT_CHANNEL_ID, FEEDS_NOTICIAS, PALABRAS_CLAVE, PALABRAS_CRITICAS, GROQ_API_KEY, GROQ_MODEL
from utils.helpers import limpiar_html, cargar_vistos, guardar_vistos, detectar_y_traducir, extraer_imagen

cliente_groq = Groq(api_key=GROQ_API_KEY)

PROMPT_CICLO = """Eres VEGA, sistema de inteligencia sintética. Se te proporciona una lista de noticias recientes de conflictos globales.

Para cada noticia genera exactamente este formato:

🔹 **[TÍTULO EN ESPAÑOL]**
📌 *Fuente: [fuente] • [fecha]*
🧠 **Análisis:** [2-3 oraciones de análisis geopolítico concreto sobre esta noticia específica]
🔗 [Ver artículo completo]([url])

Separa cada noticia con una línea en blanco.
Al final agrega:

---
**📊 TENDENCIA DEL CICLO:** [una sola oración resumiendo el patrón dominante de este ciclo]

Tono: técnico, directo. Sin introducciones ni despedidas."""

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

        noticias_nuevas = []

        async with aiohttp.ClientSession() as session:
            for fuente, url in FEEDS_NOTICIAS.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        feed = feedparser.parse(await resp.text())

                        for entrada in feed.entries[:5]:
                            titulo = entrada.get("title", "")
                            link = entrada.get("link", "")
                            resumen = limpiar_html(entrada.get("summary", ""))[:400]
                            fecha_raw = entrada.get("published", "")[:30] if entrada.get("published") else "N/A"
                            imagen = extraer_imagen(entrada)

                            if link in self.vistos:
                                continue

                            if any(p in titulo.lower() for p in PALABRAS_CLAVE):
                                self.vistos.add(link)
                                guardar_vistos(self.vistos)

                                titulo_final, _ = detectar_y_traducir(titulo)
                                resumen_final, _ = detectar_y_traducir(resumen)
                                es_critica = any(p in titulo.lower() for p in PALABRAS_CRITICAS)

                                noticias_nuevas.append({
                                    "titulo": titulo_final,
                                    "titulo_original": titulo,
                                    "resumen": resumen_final,
                                    "fuente": fuente,
                                    "link": link,
                                    "fecha": fecha_raw,
                                    "imagen": imagen,
                                    "critica": es_critica
                                })

                except Exception as e:
                    print(f"[VEGA] Error en feed {fuente}: {e}")

        # Si no hay noticias nuevas no hacemos nada
        if not noticias_nuevas:
            print(f"[VEGA] Sin noticias nuevas en este ciclo — {datetime.utcnow().strftime('%H:%M')} UTC")
            return

        # Construir contexto para Groq
        contexto = ""
        for i, n in enumerate(noticias_nuevas, 1):
            contexto += f"{i}. TÍTULO: {n['titulo']}\n"
            contexto += f"   FUENTE: {n['fuente']}\n"
            contexto += f"   FECHA: {n['fecha']}\n"
            contexto += f"   RESUMEN: {n['resumen']}\n"
            contexto += f"   URL: {n['link']}\n\n"

        # Generar análisis con Groq
        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CICLO},
                    {"role": "user", "content": f"Fecha del ciclo: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nNoticias a analizar:\n\n{contexto}"}
                ],
                max_tokens=2000,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content

            # Si el contenido es muy largo dividirlo en dos embeds
            hay_critica = any(n["critica"] for n in noticias_nuevas)
            color = 0xff0000 if hay_critica else 0xff8800
            nivel = "🔴 CICLO — ALERTA CRÍTICA DETECTADA" if hay_critica else "🟠 CICLO DE INTELIGENCIA"

            # Imagen de la primera noticia que tenga
            imagen_principal = next((n["imagen"] for n in noticias_nuevas if n["imagen"]), None)

            if len(contenido) <= 4000:
                embed = discord.Embed(
                    title=f"📡 {nivel}",
                    description=contenido,
                    color=color,
                    timestamp=datetime.utcnow()
                )
                if imagen_principal:
                    embed.set_image(url=imagen_principal)
                embed.set_footer(text=f"VEGA OSINT • {len(noticias_nuevas)} nuevas entradas analizadas")
                await canal.send(embed=embed)
            else:
                # Dividir en dos partes si es muy largo
                mitad = len(contenido) // 2
                corte = contenido.rfind("\n\n", 0, mitad)
                parte1 = contenido[:corte]
                parte2 = contenido[corte:]

                embed1 = discord.Embed(title=f"📡 {nivel} — Parte 1", description=parte1, color=color, timestamp=datetime.utcnow())
                if imagen_principal:
                    embed1.set_image(url=imagen_principal)
                embed1.set_footer(text=f"VEGA OSINT • {len(noticias_nuevas)} nuevas entradas analizadas")

                embed2 = discord.Embed(title=f"📡 {nivel} — Parte 2", description=parte2, color=color, timestamp=datetime.utcnow())
                embed2.set_footer(text="VEGA OSINT • Continúa del mensaje anterior")

                await canal.send(embed=embed1)
                await canal.send(embed=embed2)

        except Exception as e:
            print(f"[VEGA] Error generando análisis de ciclo: {e}")

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
import discord
import feedparser
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from groq import Groq
from config.settings import GUILD_ID, CONFLICT_CHANNEL_ID, CRITICAL_CHANNEL_ID, FEEDS_NOTICIAS, PALABRAS_CLAVE, PALABRAS_CRITICAS, GROQ_API_KEY, GROQ_MODEL
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

PROMPT_CRITICA = """Eres VEGA. Se te proporciona una noticia de máxima prioridad.
Genera un análisis de alerta crítica en este formato exacto:

🚨 **ALERTA CRÍTICA — [TÍTULO]**

**SITUACIÓN:** [1-2 oraciones describiendo el evento]
**IMPACTO INMEDIATO:** [consecuencias directas]
**NIVEL DE AMENAZA:** CRÍTICO
**ACCIÓN RECOMENDADA:** [qué monitorear ahora mismo]

Tono: urgente, directo, sin adornos."""

class Intel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vistos = cargar_vistos()
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    def get_admin(self):
        return self.bot.cogs.get("Admin")

    async def enviar_alerta_critica(self, noticia: dict):
        canal = self.bot.get_channel(CRITICAL_CHANNEL_ID)
        if not canal:
            return

        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CRITICA},
                    {"role": "user", "content": f"Noticia crítica:\nTítulo: {noticia['titulo']}\nResumen: {noticia['resumen']}\nFuente: {noticia['fuente']}\nURL: {noticia['link']}"}
                ],
                max_tokens=400,
                temperature=0.2
            )
            contenido = respuesta.choices[0].message.content

            embed = discord.Embed(
                title="🚨 ALERTA CRÍTICA",
                description=contenido,
                color=0xff0000,
                timestamp=datetime.utcnow()
            )
            if noticia.get("imagen"):
                embed.set_image(url=noticia["imagen"])
            embed.add_field(name="🔗 Fuente", value=f"[{noticia['fuente']}]({noticia['link']})", inline=False)
            embed.set_footer(text="VEGA OSINT • PRIORIDAD MÁXIMA")

            await canal.send("@everyone", embed=embed)

            admin = self.get_admin()
            if admin:
                admin.registrar(f"🚨 Alerta crítica enviada: {noticia['titulo'][:50]}...")

        except Exception as e:
            print(f"[VEGA] Error enviando alerta crítica: {e}")

    async def ejecutar_escaneo(self):
        admin = self.get_admin()
        if admin:
            admin.registrar("📡 Iniciando escaneo de fuentes...")

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

                                if admin:
                                    admin.registrar(f"{'🔴' if es_critica else '🟠'} [{fuente}] {titulo_final[:45]}...")

                except Exception as e:
                    print(f"[VEGA] Error en feed {fuente}: {e}")
                    if admin:
                        admin.registrar(f"⚠️ Error en feed {fuente}: {str(e)[:40]}")

        if not noticias_nuevas:
            if admin:
                admin.registrar(f"✅ Escaneo completado — Sin noticias nuevas")
            return

        # Enviar alertas críticas por separado
        for noticia in noticias_nuevas:
            if noticia["critica"]:
                await self.enviar_alerta_critica(noticia)

        # Construir contexto para Groq
        contexto = ""
        for i, n in enumerate(noticias_nuevas, 1):
            contexto += f"{i}. TÍTULO: {n['titulo']}\n"
            contexto += f"   FUENTE: {n['fuente']}\n"
            contexto += f"   FECHA: {n['fecha']}\n"
            contexto += f"   RESUMEN: {n['resumen']}\n"
            contexto += f"   URL: {n['link']}\n\n"

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
            hay_critica = any(n["critica"] for n in noticias_nuevas)
            color = 0xff0000 if hay_critica else 0xff8800
            nivel = "🔴 CICLO — ALERTA CRÍTICA DETECTADA" if hay_critica else "🟠 CICLO DE INTELIGENCIA"
            imagen_principal = next((n["imagen"] for n in noticias_nuevas if n["imagen"]), None)

            if len(contenido) <= 4000:
                embed = discord.Embed(title=f"📡 {nivel}", description=contenido, color=color, timestamp=datetime.utcnow())
                if imagen_principal:
                    embed.set_image(url=imagen_principal)
                embed.set_footer(text=f"VEGA OSINT • {len(noticias_nuevas)} nuevas entradas analizadas")
                await canal.send(embed=embed)
            else:
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

            if admin:
                admin.incrementar_ciclo()
                admin.registrar(f"✅ Ciclo completado — {len(noticias_nuevas)} noticias procesadas")

        except Exception as e:
            print(f"[VEGA] Error generando análisis de ciclo: {e}")
            if admin:
                admin.registrar(f"❌ Error en análisis IA: {str(e)[:50]}")

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
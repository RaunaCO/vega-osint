import discord
import feedparser
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from groq import Groq
from config.settings import GUILD_ID, CONFLICT_CHANNEL_ID, CRITICAL_CHANNEL_ID, REGION_CANALES, FEEDS_NOTICIAS, PALABRAS_CLAVE, PALABRAS_CRITICAS, GROQ_API_KEY, GROQ_MODEL
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

PROMPT_CLASIFICAR = """Eres VEGA, sistema de clasificación de inteligencia. Analiza esta noticia y responde ÚNICAMENTE con un JSON con este formato exacto, sin texto adicional:

{
  "es_critica": true/false,
  "nivel": "CRÍTICO/ALTO/MEDIO/BAJO",
  "region": "Medio Oriente/Europa/África/Asia/Américas/Global",
  "categoria": "Nuclear/Militar/Humanitario/Diplomático/Terrorismo/Otro",
  "razon": "Una sola oración explicando la clasificación"
}

Criterios para CRÍTICO: amenaza nuclear, ataque directo entre estados, masacre confirmada, uso de armas químicas, escalada mayor documentada.
Criterios para ALTO: ofensivas militares activas, ataques a infraestructura, crisis diplomática grave.
Criterios para MEDIO: tensiones, movimientos de tropas, declaraciones hostiles.
Criterios para BAJO: análisis, reportes históricos, contexto."""

PROMPT_ALERTA = """Eres VEGA. Genera una alerta crítica impactante en este formato exacto:

## ⚠️ CLASIFICACIÓN: [nivel]
## 🌍 REGIÓN: [region]
## 🏷️ CATEGORÍA: [categoria]

---

### SITUACIÓN ACTUAL
[2-3 oraciones describiendo el evento con precisión militar]

### IMPACTO INMEDIATO
[consecuencias directas en la región y actores involucrados]

### ACTORES CLAVE
[países, grupos o líderes involucrados]

### EVALUACIÓN DE AMENAZA
[proyección a 24-72 horas]

---
*Fuente verificada: [fuente] — [fecha]*

Tono: urgente, técnico, sin adornos. Máxima precisión."""

def color_por_nivel(nivel: str) -> int:
    return {
        "CRÍTICO": 0xff0000,
        "ALTO":    0xff6600,
        "MEDIO":   0xffaa00,
        "BAJO":    0xffff00,
    }.get(nivel, 0xff8800)

def emoji_por_nivel(nivel: str) -> str:
    return {
        "CRÍTICO": "🔴",
        "ALTO":    "🟠",
        "MEDIO":   "🟡",
        "BAJO":    "🟢",
    }.get(nivel, "🟠")

class Intel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.vistos = cargar_vistos()
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    def get_admin(self):
        return self.bot.cogs.get("Admin")

    async def clasificar_noticia(self, titulo: str, resumen: str, fuente: str) -> dict:
        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CLASIFICAR},
                    {"role": "user", "content": f"Título: {titulo}\nResumen: {resumen}\nFuente: {fuente}"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            import json
            contenido = respuesta.choices[0].message.content.strip()
            contenido = contenido.replace("```json", "").replace("```", "").strip()
            return json.loads(contenido)
        except Exception as e:
            print(f"[VEGA] Error clasificando noticia: {e}")
            return {
                "es_critica": False,
                "nivel": "MEDIO",
                "region": "Global",
                "categoria": "Otro",
                "razon": "Clasificación automática fallida"
            }

    async def enviar_alerta_critica(self, noticia: dict, clasificacion: dict):
        canal_critico = self.bot.get_channel(CRITICAL_CHANNEL_ID)
        if not canal_critico:
            return

        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_ALERTA},
                    {"role": "user", "content": f"Título: {noticia['titulo']}\nResumen: {noticia['resumen']}\nFuente: {noticia['fuente']}\nFecha: {noticia['fecha']}\nNivel: {clasificacion['nivel']}\nRegión: {clasificacion['region']}\nCategoría: {clasificacion['categoria']}"}
                ],
                max_tokens=600,
                temperature=0.2
            )
            contenido = respuesta.choices[0].message.content
            nivel = clasificacion["nivel"]
            color = color_por_nivel(nivel)
            emoji = emoji_por_nivel(nivel)

            embed = discord.Embed(
                title=f"{emoji} ALERTA {nivel} — {clasificacion['categoria'].upper()}",
                description=contenido,
                color=color,
                timestamp=datetime.utcnow()
            )
            if noticia.get("imagen"):
                embed.set_image(url=noticia["imagen"])

            embed.add_field(name="🌍 Región", value=clasificacion["region"], inline=True)
            embed.add_field(name="🏷️ Categoría", value=clasificacion["categoria"], inline=True)
            embed.add_field(name="🔗 Fuente", value=f"[{noticia['fuente']}]({noticia['link']})", inline=True)
            embed.set_footer(text=f"VEGA OSINT • Clasificado por IA • {clasificacion['razon']}")

            mention = "@everyone" if nivel == "CRÍTICO" else ""
            await canal_critico.send(content=mention, embed=embed)

            admin = self.get_admin()
            if admin:
                admin.registrar(f"{emoji} Alerta {nivel} enviada: {noticia['titulo'][:45]}...")

        except Exception as e:
            print(f"[VEGA] Error enviando alerta: {e}")

    async def enviar_a_region(self, noticia: dict, clasificacion: dict, analisis: str):
        region = clasificacion.get("region", "Global")
        canal_id = REGION_CANALES.get(region)

        if not canal_id:
            return

        canal = self.bot.get_channel(canal_id)
        if not canal:
            return

        nivel = clasificacion["nivel"]
        color = color_por_nivel(nivel)
        emoji = emoji_por_nivel(nivel)

        embed = discord.Embed(
            title=f"{emoji} {noticia['titulo'][:250]}",
            url=noticia["link"],
            description=analisis,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"{clasificacion['categoria']} — {noticia['fuente']}")
        if noticia.get("imagen"):
            embed.set_image(url=noticia["imagen"])
        embed.add_field(name="📅 Publicado", value=noticia["fecha"], inline=True)
        embed.add_field(name="⚠️ Nivel", value=nivel, inline=True)
        embed.add_field(name="🔗 Fuente", value=f"[{noticia['fuente']}]({noticia['link']})", inline=True)
        embed.set_footer(text="VEGA OSINT • 🌐 Traducido automáticamente" if noticia.get("traducido") else "VEGA OSINT")
        await canal.send(embed=embed)

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

                                titulo_final, titulo_traducido = detectar_y_traducir(titulo)
                                resumen_final, resumen_traducido = detectar_y_traducir(resumen)
                                fue_traducido = titulo_traducido or resumen_traducido

                                noticias_nuevas.append({
                                    "titulo": titulo_final,
                                    "titulo_original": titulo,
                                    "resumen": resumen_final,
                                    "fuente": fuente,
                                    "link": link,
                                    "fecha": fecha_raw,
                                    "imagen": imagen,
                                    "traducido": fue_traducido
                                })

                                if admin:
                                    admin.registrar(f"🟠 [{fuente}] {titulo_final[:45]}...")

                except Exception as e:
                    print(f"[VEGA] Error en feed {fuente}: {e}")
                    if admin:
                        admin.registrar(f"⚠️ Error en feed {fuente}: {str(e)[:40]}")

        if not noticias_nuevas:
            if admin:
                admin.registrar("✅ Escaneo completado — Sin noticias nuevas")
            return

        # Clasificar y enrutar cada noticia con IA
        if admin:
            admin.registrar(f"🧠 Clasificando {len(noticias_nuevas)} noticias con IA...")

        for noticia in noticias_nuevas:
            clasificacion = await self.clasificar_noticia(
                noticia["titulo"], noticia["resumen"], noticia["fuente"]
            )
            noticia["clasificacion"] = clasificacion

            # Enviar a canal de región
            await self.enviar_a_region(noticia, clasificacion, noticia["resumen"])

            # Enviar alerta crítica si aplica
            if clasificacion["nivel"] in ["CRÍTICO", "ALTO"]:
                await self.enviar_alerta_critica(noticia, clasificacion)

        # Generar reporte de ciclo para #conflict-watch
        contexto = ""
        for i, n in enumerate(noticias_nuevas, 1):
            c = n.get("clasificacion", {})
            contexto += f"{i}. TÍTULO: {n['titulo']}\n"
            contexto += f"   FUENTE: {n['fuente']}\n"
            contexto += f"   REGIÓN: {c.get('region', 'Global')}\n"
            contexto += f"   NIVEL: {c.get('nivel', 'MEDIO')}\n"
            contexto += f"   RESUMEN: {n['resumen']}\n"
            contexto += f"   URL: {n['link']}\n\n"

        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CICLO},
                    {"role": "user", "content": f"Fecha del ciclo: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nNoticias:\n\n{contexto}"}
                ],
                max_tokens=2000,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content
            hay_critica = any(n.get("clasificacion", {}).get("nivel") == "CRÍTICO" for n in noticias_nuevas)
            color = 0xff0000 if hay_critica else 0xff8800
            nivel_ciclo = "🔴 CICLO — ALERTA CRÍTICA DETECTADA" if hay_critica else "🟠 CICLO DE INTELIGENCIA"
            imagen_principal = next((n["imagen"] for n in noticias_nuevas if n["imagen"]), None)

            if len(contenido) <= 4000:
                embed = discord.Embed(title=f"📡 {nivel_ciclo}", description=contenido, color=color, timestamp=datetime.utcnow())
                if imagen_principal:
                    embed.set_image(url=imagen_principal)
                embed.set_footer(text=f"VEGA OSINT • {len(noticias_nuevas)} entradas analizadas")
                await canal.send(embed=embed)
            else:
                mitad = len(contenido) // 2
                corte = contenido.rfind("\n\n", 0, mitad)
                parte1 = contenido[:corte]
                parte2 = contenido[corte:]

                embed1 = discord.Embed(title=f"📡 {nivel_ciclo} — Parte 1", description=parte1, color=color, timestamp=datetime.utcnow())
                if imagen_principal:
                    embed1.set_image(url=imagen_principal)
                embed1.set_footer(text=f"VEGA OSINT • {len(noticias_nuevas)} entradas analizadas")
                embed2 = discord.Embed(title=f"📡 {nivel_ciclo} — Parte 2", description=parte2, color=color, timestamp=datetime.utcnow())
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
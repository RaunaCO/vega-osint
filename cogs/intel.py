import discord
import feedparser
import json
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from groq import Groq
from config.settings import GUILD_ID, CONFLICT_CHANNEL_ID, CRITICAL_CHANNEL_ID, REGION_CANALES, FEEDS_NOTICIAS, PALABRAS_CLAVE, PALABRAS_CRITICAS, GROQ_API_KEY, GROQ_MODEL, PROMPT_CLASIFICAR
from utils.helpers import limpiar_html, cargar_vistos, guardar_vistos, detectar_y_traducir, extraer_imagen

cliente_groq = Groq(api_key=GROQ_API_KEY)

PROMPT_CICLO = """Eres VEGA, sistema de inteligencia sintética. Se te proporciona una lista de noticias recientes de conflictos globales.

Genera un reporte de ciclo con este formato:

**📊 REPORTE DE CICLO — [fecha]**

**PANORAMA GENERAL:**
[2-3 oraciones resumiendo el estado global del ciclo]

**POR REGIÓN:**
[Para cada región con actividad]:
- **[Región]** — [1-2 oraciones del estado en esa región]

**TENDENCIA DOMINANTE:** [Una sola oración]
**NIVEL GLOBAL:** [CRÍTICO/ALTO/MEDIO/BAJO]

Tono: técnico, directo. Sin introducciones."""

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
                max_tokens=300,
                temperature=0.1
            )
            contenido = respuesta.choices[0].message.content.strip()
            contenido = contenido.replace("```json", "").replace("```", "").strip()
            return json.loads(contenido)
        except Exception as e:
            print(f"[VEGA] Error clasificando: {e}")
            return {
                "nivel": "MEDIO",
                "es_critica": False,
                "region": "Global",
                "categoria": "Otro",
                "actores_principales": [],
                "ubicacion_precisa": "No especificada",
                "confianza": "BAJA",
                "razon": "Clasificación automática fallida"
            }

    async def enviar_embed_individual(self, noticia: dict, clasificacion: dict):
        region = clasificacion.get("region", "Global")
        canal_id = REGION_CANALES.get(region)
        if not canal_id:
            return

        canal = self.bot.get_channel(canal_id)
        if not canal:
            return

        nivel = clasificacion["nivel"]
        emoji = emoji_por_nivel(nivel)
        color = color_por_nivel(nivel)
        ubicacion = clasificacion.get("ubicacion_precisa", "No especificada")
        categoria = clasificacion.get("categoria", "Otro")
        razon = clasificacion.get("razon", "")
        actores = ", ".join(clasificacion.get("actores_principales", [])) or "No identificados"
        confianza = clasificacion.get("confianza", "MEDIA")

        titulo_display = noticia["titulo"]
        if noticia.get("traducido") and noticia.get("titulo_original"):
            titulo_display = f"{noticia['titulo']}\n*({noticia['titulo_original']})*"

        embed = discord.Embed(
            title=titulo_display[:250],
            url=noticia["link"],
            color=color,
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="📰 Resumen",
            value=noticia["resumen"][:400] + "..." if len(noticia["resumen"]) > 400 else noticia["resumen"],
            inline=False
        )

        embed.add_field(name="🧠 Análisis VEGA", value=razon, inline=False)
        embed.add_field(name=f"{emoji} Nivel", value=nivel, inline=True)
        embed.add_field(name="🏷️ Tipo", value=categoria, inline=True)
        embed.add_field(name="🎯 Confianza", value=confianza, inline=True)
        embed.add_field(name="📍 Ubicación", value=ubicacion, inline=True)
        embed.add_field(name="👥 Actores", value=actores, inline=True)
        embed.add_field(name="🔗 Fuente", value=f"[{noticia['fuente']}]({noticia['link']})", inline=True)

        if noticia.get("traducido"):
            embed.add_field(name="🌐 Idioma", value="Traducido al español", inline=True)

        if noticia.get("imagen"):
            embed.set_image(url=noticia["imagen"])

        embed.set_author(name=f"VEGA INTEL — {region}")
        embed.set_footer(text="VEGA OSINT • Protocolo de Inteligencia Sintética")

        await canal.send(embed=embed)

    async def enviar_alerta_critica(self, noticia: dict, clasificacion: dict):
        canal_critico = self.bot.get_channel(CRITICAL_CHANNEL_ID)
        if not canal_critico:
            return

        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_ALERTA},
                    {"role": "user", "content": f"Título: {noticia['titulo']}\nResumen: {noticia['resumen']}\nFuente: {noticia['fuente']}\nFecha: {noticia['fecha']}\nNivel: {clasificacion['nivel']}\nRegión: {clasificacion['region']}\nCategoría: {clasificacion['categoria']}\nActores: {', '.join(clasificacion.get('actores_principales', []))}\nUbicación: {clasificacion.get('ubicacion_precisa', 'No especificada')}"}
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
            embed.add_field(name="📍 Ubicación", value=clasificacion.get("ubicacion_precisa", "No especificada"), inline=True)
            embed.add_field(name="👥 Actores", value=", ".join(clasificacion.get("actores_principales", [])) or "No identificados", inline=True)
            embed.add_field(name="🔗 Fuente", value=f"[{noticia['fuente']}]({noticia['link']})", inline=True)
            embed.set_footer(text="VEGA OSINT • PRIORIDAD MÁXIMA")

            mention = "@everyone" if nivel == "CRÍTICO" else ""
            await canal_critico.send(content=mention, embed=embed)

            admin = self.get_admin()
            if admin:
                admin.registrar(f"{emoji} Alerta {nivel}: {noticia['titulo'][:45]}...")

        except Exception as e:
            print(f"[VEGA] Error enviando alerta: {e}")

    async def ejecutar_escaneo(self):
        admin = self.get_admin()
        if admin:
            admin.registrar("📡 Iniciando escaneo de fuentes...")

        canal_principal = self.bot.get_channel(CONFLICT_CHANNEL_ID)
        if not canal_principal:
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
                                    "titulo_original": titulo if fue_traducido else None,
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
                        admin.registrar(f"⚠️ Error en {fuente}: {str(e)[:40]}")

        if not noticias_nuevas:
            if admin:
                admin.registrar("✅ Escaneo completado — Sin noticias nuevas")
            return

        if admin:
            admin.registrar(f"🧠 Clasificando {len(noticias_nuevas)} noticias...")

        for noticia in noticias_nuevas:
            clasificacion = await self.clasificar_noticia(
                noticia["titulo"], noticia["resumen"], noticia["fuente"]
            )
            noticia["clasificacion"] = clasificacion
            await self.enviar_embed_individual(noticia, clasificacion)

            if clasificacion["nivel"] in ["CRÍTICO", "ALTO"]:
                await self.enviar_alerta_critica(noticia, clasificacion)

        contexto = ""
        for i, n in enumerate(noticias_nuevas, 1):
            c = n.get("clasificacion", {})
            contexto += f"{i}. TÍTULO: {n['titulo']}\n"
            contexto += f"   FUENTE: {n['fuente']}\n"
            contexto += f"   REGIÓN: {c.get('region', 'Global')}\n"
            contexto += f"   NIVEL: {c.get('nivel', 'MEDIO')}\n"
            contexto += f"   UBICACIÓN: {c.get('ubicacion_precisa', 'No especificada')}\n"
            contexto += f"   ACTORES: {', '.join(c.get('actores_principales', []))}\n"
            contexto += f"   RESUMEN: {n['resumen']}\n\n"

        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CICLO},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n{contexto}"}
                ],
                max_tokens=1000,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content
            hay_critica = any(n.get("clasificacion", {}).get("nivel") == "CRÍTICO" for n in noticias_nuevas)
            color = 0xff0000 if hay_critica else 0x0088ff
            imagen_principal = next((n["imagen"] for n in noticias_nuevas if n["imagen"]), None)

            embed = discord.Embed(
                title="📡 REPORTE DE CICLO",
                description=contenido[:4000],
                color=color,
                timestamp=datetime.utcnow()
            )
            if imagen_principal:
                embed.set_thumbnail(url=imagen_principal)
            embed.set_footer(text=f"VEGA OSINT • {len(noticias_nuevas)} noticias procesadas")
            await canal_principal.send(embed=embed)

            if admin:
                admin.incrementar_ciclo()
                admin.registrar(f"✅ Ciclo completado — {len(noticias_nuevas)} noticias procesadas")

        except Exception as e:
            print(f"[VEGA] Error en reporte de ciclo: {e}")
            if admin:
                admin.registrar(f"❌ Error en reporte: {str(e)[:50]}")

    @tasks.loop(minutes=5)
    async def monitor(self):
        await self.ejecutar_escaneo()

    @monitor.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()

    @discord.slash_command(guild_ids=[GUILD_ID], description="Escanea todas las fuentes ahora mismo")
    async def scanfeed(self, ctx):
        await ctx.defer()
        await ctx.respond("📡 **VEGA** — Escaneando fuentes... Resultados en los canales de región.")
        await self.ejecutar_escaneo()

def setup(bot):
    bot.add_cog(Intel(bot))

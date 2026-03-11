import discord
from discord.ext import commands
from groq import Groq
from datetime import datetime, timezone, timedelta
from config.settings import GUILD_ID, GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, CONFLICT_CHANNEL_ID, MISSION_LOGS_CHANNEL_ID, REGION_CANALES
from utils.helpers import buscar_noticias_relevantes

cliente_groq = Groq(api_key=GROQ_API_KEY)

class AIBrain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def archivar_sitrep(self, tema: str, contenido: str, fuentes: int, autor: str):
        canal = self.bot.get_channel(MISSION_LOGS_CHANNEL_ID)
        if not canal:
            return
        embed = discord.Embed(
            title=f"📋 SITREP ARCHIVADO — {tema.upper()}",
            description=contenido[:4000],
            color=0x2b2d31,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"VEGA OSINT • {fuentes} fuentes • Solicitado por {autor}")
        await canal.send(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Genera un SITREP basado en noticias reales")
    async def sitrep(self, ctx, tema: str):
        await ctx.defer()
        try:
            noticias = await buscar_noticias_relevantes(tema)
            contexto = "NOTICIAS REALES:\n\n" + "\n\n---\n\n".join(noticias) if noticias else f"Sin noticias recientes sobre '{tema}'. Usa contexto histórico marcando [CONTEXTO HISTÓRICO]."

            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nTema: {tema}\n\n{contexto}"}
                ],
                max_tokens=1024,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content[:4000]
            embed = discord.Embed(title=f"📋 SITREP — {tema.upper()}", description=contenido, color=0x00ff41, timestamp=datetime.now(timezone.utc))
            embed.set_footer(text=f"VEGA OSINT • {len(noticias)} fuentes analizadas")
            await ctx.respond(embed=embed)

            await self.archivar_sitrep(tema, contenido, len(noticias), ctx.author.display_name)

            admin = self.bot.cogs.get("Admin")
            if admin:
                admin.registrar(f"📋 /sitrep generado: {tema[:40]} — {len(noticias)} fuentes")

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Analiza un texto con IA")
    async def analizar(self, ctx, texto: str):
        await ctx.defer()
        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nAnaliza este texto:\n\n{texto}"}
                ],
                max_tokens=800,
                temperature=0.2
            )
            contenido = respuesta.choices[0].message.content
            embed = discord.Embed(title="🧠 ANÁLISIS DE INTELIGENCIA", description=contenido, color=0x7700ff, timestamp=datetime.now(timezone.utc))
            embed.set_footer(text="VEGA OSINT • Verificar fuentes primarias")
            await ctx.respond(embed=embed)

            admin = self.bot.cogs.get("Admin")
            if admin:
                admin.registrar(f"🧠 /analizar ejecutado por {ctx.author.display_name}")

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Resume las últimas noticias del canal de inteligencia")
    async def resumen(self, ctx, cantidad: int = 10):
        await ctx.defer()
        try:
            canal = self.bot.get_channel(CONFLICT_CHANNEL_ID)
            if not canal:
                await ctx.respond("⚠️ **VEGA** — Canal de inteligencia no encontrado.")
                return

            mensajes = []
            async for mensaje in canal.history(limit=cantidad):
                if mensaje.author == self.bot.user and mensaje.embeds:
                    embed = mensaje.embeds[0]
                    titulo = embed.title or ""
                    descripcion = embed.description or ""
                    mensajes.append(f"• {titulo}\n{descripcion[:200]}")

            if not mensajes:
                await ctx.respond("⚠️ **VEGA** — No hay noticias recientes en el canal.")
                return

            mensajes.reverse()
            contexto = "\n\n".join(mensajes)

            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nGenera un resumen ejecutivo de estas noticias recientes:\n\n{contexto}"}
                ],
                max_tokens=800,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content
            embed = discord.Embed(
                title=f"📊 RESUMEN EJECUTIVO — Últimas {len(mensajes)} noticias",
                description=contenido,
                color=0x0088ff,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_footer(text=f"VEGA OSINT • Basado en {len(mensajes)} entradas recientes")
            await ctx.respond(embed=embed)

            admin = self.bot.cogs.get("Admin")
            if admin:
                admin.registrar(f"📊 /resumen ejecutado por {ctx.author.display_name}")

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Briefing de las últimas horas por región")
    async def briefing(self, ctx, horas: discord.Option(int, description="Horas hacia atrás (default: 8)", default=8)):
        await ctx.defer()
        try:
            ahora = datetime.now(timezone.utc)
            limite = ahora - timedelta(hours=horas)
            noticias_por_region = {}

            for region, canal_id in REGION_CANALES.items():
                canal = self.bot.get_channel(canal_id)
                if not canal:
                    continue

                entradas = []
                async for mensaje in canal.history(limit=100, after=limite):
                    if mensaje.author == self.bot.user and mensaje.embeds:
                        embed = mensaje.embeds[0]
                        titulo = embed.title or ""
                        nivel = "MEDIO"
                        ubicacion = "No especificada"
                        for field in embed.fields:
                            if "Nivel" in field.name:
                                nivel = field.value
                            if "Ubicación" in field.name:
                                ubicacion = field.value
                        hora_msg = mensaje.created_at.strftime("%H:%M UTC")
                        entradas.append(f"[{hora_msg}] [{nivel}] {titulo} — 📍{ubicacion}")

                if entradas:
                    noticias_por_region[region] = entradas

            if not noticias_por_region:
                await ctx.respond(f"⚠️ **VEGA** — Sin actividad registrada en las últimas {horas} horas.")
                return

            contexto = ""
            for region, entradas in noticias_por_region.items():
                contexto += f"\n## {region}\n"
                for entrada in entradas:
                    contexto += f"{entrada}\n"

            PROMPT_BRIEFING = f"""Eres VEGA. Genera un briefing de inteligencia de las últimas {horas} horas.

Formato exacto:

# 🌅 MORNING BRIEFING — {{fecha}}
**Período cubierto:** Últimas {horas} horas

---

## RESUMEN EJECUTIVO
[3-4 oraciones describiendo el panorama global del período]

---

[Para cada región con actividad, en orden cronológico]:

## 🌍 [REGIÓN]
[Lista cronológica de eventos con hora, nivel y análisis breve de cada uno]
**Balance regional:** [1 oración del estado final de la región]

---

## CONCLUSIÓN OPERACIONAL
**Evento más crítico:** [el más importante del período]
**Tendencia dominante:** [patrón general observado]
**Puntos a monitorear:** [qué seguir en las próximas horas]

Tono: técnico, preciso, como un briefing militar real."""

            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_BRIEFING},
                    {"role": "user", "content": f"Fecha actual: {ahora.strftime('%Y-%m-%d %H:%M')} UTC\n\nEventos registrados:\n{contexto}"}
                ],
                max_tokens=2000,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content
            total_eventos = sum(len(e) for e in noticias_por_region.values())

            if len(contenido) <= 4000:
                embed = discord.Embed(
                    title=f"🌅 MORNING BRIEFING — {ahora.strftime('%d/%m/%Y')}",
                    description=contenido,
                    color=0x0088ff,
                    timestamp=ahora
                )
                embed.set_footer(text=f"VEGA OSINT • {total_eventos} eventos • Últimas {horas}h • {len(noticias_por_region)} regiones activas")
                await ctx.respond(embed=embed)
            else:
                mitad = len(contenido) // 2
                corte = contenido.rfind("\n\n", 0, mitad)
                parte1 = contenido[:corte]
                parte2 = contenido[corte:]

                embed1 = discord.Embed(title=f"🌅 MORNING BRIEFING — {ahora.strftime('%d/%m/%Y')} — Parte 1", description=parte1, color=0x0088ff, timestamp=ahora)
                embed1.set_footer(text=f"VEGA OSINT • {total_eventos} eventos • Últimas {horas}h")
                embed2 = discord.Embed(title=f"🌅 MORNING BRIEFING — Parte 2", description=parte2, color=0x0088ff, timestamp=ahora)
                embed2.set_footer(text="VEGA OSINT • Continúa del mensaje anterior")
                await ctx.respond(embed=embed1)
                await ctx.followup.send(embed=embed2)

            admin = self.bot.cogs.get("Admin")
            if admin:
                admin.registrar(f"🌅 /briefing ejecutado por {ctx.author.display_name} — {total_eventos} eventos")

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

def setup(bot):
    bot.add_cog(AIBrain(bot))
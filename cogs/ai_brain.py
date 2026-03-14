import discord
from discord.ext import commands
from groq import Groq
from datetime import datetime, timezone, timedelta
from config.settings import (
    GUILD_ID, GROQ_API_KEY, GROQ_MODEL,
    PROMPT_SITREP, PROMPT_SISTEMA, PROMPT_BRIEFING,
    CONFLICT_CHANNEL_ID, MISSION_LOGS_CHANNEL_ID, REGION_CANALES
)
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
            title=f"📋 SITREP — {tema.upper()}",
            description=contenido[:4000],
            color=0x2b2d31,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text=f"VEGA OSINT • {fuentes} fuentes • Por {autor}")
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
                    {"role": "system", "content": PROMPT_SITREP},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\nTema: {tema}\n\n{contexto}"}
                ],
                max_tokens=1024,
                temperature=0.2
            )
            contenido = respuesta.choices[0].message.content[:4000]
            embed = discord.Embed(title=f"📋 SITREP — {tema.upper()}", description=contenido, color=0x00ff41, timestamp=datetime.now(timezone.utc))
            embed.set_footer(text=f"VEGA OSINT • {len(noticias)} fuentes analizadas")
            await ctx.respond(embed=embed)
            await self.archivar_sitrep(tema, contenido, len(noticias), ctx.author.display_name)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.registrar(f"📋 /sitrep: {tema[:40]} — {len(noticias)} fuentes")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Analiza un texto con IA")
    async def analizar(self, ctx, texto: str):
        await ctx.defer()
        try:
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEMA},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nAnaliza este texto desde perspectiva de inteligencia geopolítica:\n\n{texto}"}
                ],
                max_tokens=800,
                temperature=0.2
            )
            embed = discord.Embed(title="🧠 ANÁLISIS DE INTELIGENCIA", description=respuesta.choices[0].message.content, color=0x7700ff, timestamp=datetime.now(timezone.utc))
            embed.set_footer(text="VEGA OSINT • Verificar fuentes primarias")
            await ctx.respond(embed=embed)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.registrar(f"🧠 /analizar por {ctx.author.display_name}")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

    @discord.slash_command(guild_ids=[GUILD_ID], description="Resume las últimas noticias del canal")
    async def resumen(self, ctx, cantidad: int = 10):
        await ctx.defer()
        try:
            canal = self.bot.get_channel(CONFLICT_CHANNEL_ID)
            if not canal:
                await ctx.respond("⚠️ **VEGA** — Canal no encontrado.")
                return

            mensajes = []
            async for mensaje in canal.history(limit=cantidad):
                if mensaje.author == self.bot.user and mensaje.embeds:
                    embed = mensaje.embeds[0]
                    mensajes.append(f"• {embed.title or ''}\n{(embed.description or '')[:200]}")

            if not mensajes:
                await ctx.respond("⚠️ **VEGA** — No hay noticias recientes.")
                return

            mensajes.reverse()
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEMA},
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nGenera un resumen ejecutivo de estas noticias:\n\n" + "\n\n".join(mensajes)}
                ],
                max_tokens=800,
                temperature=0.2
            )
            embed = discord.Embed(title=f"📊 RESUMEN — Últimas {len(mensajes)} noticias", description=respuesta.choices[0].message.content, color=0x0088ff, timestamp=datetime.now(timezone.utc))
            embed.set_footer(text=f"VEGA OSINT • {len(mensajes)} entradas")
            await ctx.respond(embed=embed)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.registrar(f"📊 /resumen por {ctx.author.display_name}")
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
                        nivel = next((f.value for f in embed.fields if "Nivel" in f.name), "MEDIO")
                        ubicacion = next((f.value for f in embed.fields if "Ubicación" in f.name), "N/A")
                        hora_msg = mensaje.created_at.strftime("%H:%M UTC")
                        entradas.append(f"[{hora_msg}] [{nivel}] {embed.title} — 📍{ubicacion}")
                if entradas:
                    noticias_por_region[region] = entradas

            if not noticias_por_region:
                await ctx.respond(f"⚠️ **VEGA** — Sin actividad en las últimas {horas} horas.")
                return

            contexto = ""
            for region, entradas in noticias_por_region.items():
                contexto += f"\n## {region}\n" + "\n".join(entradas)

            prompt = PROMPT_BRIEFING.replace("{horas}", str(horas))
            respuesta = cliente_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Fecha: {ahora.strftime('%Y-%m-%d %H:%M')} UTC\n\n{contexto}"}
                ],
                max_tokens=2000,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content
            total = sum(len(e) for e in noticias_por_region.values())

            if len(contenido) <= 4000:
                embed = discord.Embed(title=f"🌅 MORNING BRIEFING — {ahora.strftime('%d/%m/%Y')}", description=contenido, color=0x0088ff, timestamp=ahora)
                embed.set_footer(text=f"VEGA OSINT • {total} eventos • Últimas {horas}h")
                await ctx.respond(embed=embed)
            else:
                corte = contenido.rfind("\n\n", 0, len(contenido)//2)
                embed1 = discord.Embed(title=f"🌅 MORNING BRIEFING — Parte 1", description=contenido[:corte], color=0x0088ff, timestamp=ahora)
                embed2 = discord.Embed(title=f"🌅 MORNING BRIEFING — Parte 2", description=contenido[corte:], color=0x0088ff, timestamp=ahora)
                embed1.set_footer(text=f"VEGA OSINT • {total} eventos • Últimas {horas}h")
                embed2.set_footer(text="VEGA OSINT • Continúa")
                await ctx.respond(embed=embed1)
                await ctx.followup.send(embed=embed2)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.registrar(f"🌅 /briefing por {ctx.author.display_name} — {total} eventos")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

def setup(bot):
    bot.add_cog(AIBrain(bot))
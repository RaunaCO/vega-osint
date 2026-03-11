import discord
from discord.ext import commands
from groq import Groq
from datetime import datetime
from config.settings import GUILD_ID, GROQ_API_KEY, GROQ_MODEL, SYSTEM_PROMPT, CONFLICT_CHANNEL_ID
from utils.helpers import buscar_noticias_relevantes

cliente_groq = Groq(api_key=GROQ_API_KEY)

class AIBrain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
            embed = discord.Embed(title=f"📋 SITREP — {tema.upper()}", description=contenido, color=0x00ff41, timestamp=datetime.utcnow())
            embed.set_footer(text=f"VEGA OSINT • {len(noticias)} fuentes analizadas")
            await ctx.respond(embed=embed)
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
            embed = discord.Embed(title="🧠 ANÁLISIS DE INTELIGENCIA", description=contenido, color=0x7700ff, timestamp=datetime.utcnow())
            embed.set_footer(text="VEGA OSINT • Verificar fuentes primarias")
            await ctx.respond(embed=embed)
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
                    {"role": "user", "content": f"Fecha: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nGenera un resumen ejecutivo breve de estas noticias recientes. Identifica patrones, tendencias y el tema dominante:\n\n{contexto}"}
                ],
                max_tokens=800,
                temperature=0.2
            )

            contenido = respuesta.choices[0].message.content
            embed = discord.Embed(
                title=f"📊 RESUMEN EJECUTIVO — Últimas {len(mensajes)} noticias",
                description=contenido,
                color=0x0088ff,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"VEGA OSINT • Basado en {len(mensajes)} entradas recientes")
            await ctx.respond(embed=embed)

        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")

def setup(bot):
    bot.add_cog(AIBrain(bot))
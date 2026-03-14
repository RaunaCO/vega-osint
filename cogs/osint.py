import discord
from discord.ext import commands
import aiohttp
from datetime import datetime, timezone
from config.settings import GUILD_ID, OSINT_HITS_CHANNEL_ID

class OSINT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(guild_ids=[GUILD_ID], description="Busca un usuario en múltiples redes sociales")
    async def userrecon(self, ctx, usuario: str):
        await ctx.defer()

        plataformas = {
            "GitHub":    f"https://github.com/{usuario}",
            "Instagram": f"https://www.instagram.com/{usuario}",
            "TikTok":    f"https://www.tiktok.com/@{usuario}",
            "Twitter/X": f"https://twitter.com/{usuario}",
            "Reddit":    f"https://www.reddit.com/user/{usuario}",
            "Pinterest": f"https://www.pinterest.com/{usuario}",
        }

        encontrados = []
        no_encontrados = []

        async with aiohttp.ClientSession() as session:
            for plataforma, url in plataformas.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            encontrados.append(f"🟢 **{plataforma}** — [ver perfil]({url})")
                        else:
                            no_encontrados.append(f"🔴 {plataforma}")
                except:
                    no_encontrados.append(f"⚫ {plataforma} (sin respuesta)")

        embed = discord.Embed(
            title=f"🔍 RECON — `{usuario}`",
            description="Análisis de presencia digital completado.",
            color=0x00ff41,
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="✅ PERFILES ENCONTRADOS", value="\n".join(encontrados) if encontrados else "Ninguno", inline=False)
        embed.add_field(name="❌ NO ENCONTRADOS", value="\n".join(no_encontrados) if no_encontrados else "Ninguno", inline=False)
        embed.set_footer(text="VEGA OSINT • Protocolo de Reconocimiento Digital")
        await ctx.respond(embed=embed)

        canal_hits = self.bot.get_channel(OSINT_HITS_CHANNEL_ID)
        if canal_hits:
            embed_archivo = discord.Embed(
                title=f"📁 RECON ARCHIVADO — `{usuario}`",
                color=0x00ff41,
                timestamp=datetime.now(timezone.utc)
            )
            embed_archivo.add_field(name="✅ Encontrados", value="\n".join(encontrados) if encontrados else "Ninguno", inline=False)
            embed_archivo.add_field(name="❌ No encontrados", value="\n".join(no_encontrados) if no_encontrados else "Ninguno", inline=False)
            embed_archivo.set_footer(text=f"VEGA OSINT • Ejecutado por {ctx.author.display_name}")
            await canal_hits.send(embed=embed_archivo)

        admin = self.bot.cogs.get("VegaAdmin")
        if admin:
            admin.registrar(f"🔍 /userrecon: {usuario} — {len(encontrados)} perfiles encontrados")

def setup(bot):
    bot.add_cog(OSINT(bot))
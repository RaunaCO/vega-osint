import discord
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

asyncio.set_event_loop(asyncio.new_event_loop())

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)

bot.load_extension("cogs.osint")

@bot.event
async def on_ready():
    print("=" * 40)
    print(f"  VEGA ONLINE — Conectado como {bot.user}")
    print(f"  Servidores activos: {len(bot.guilds)}")
    print("  Protocolo de inteligencia iniciado.")
    print("=" * 40)

@bot.slash_command(guild_ids=[GUILD_ID], description="Verifica que Vega está operativo")
async def ping(ctx):
    latencia = round(bot.latency * 1000)
    await ctx.respond(f"🟢 **VEGA OPERATIVO** — Latencia: `{latencia}ms`")

bot.run(TOKEN)
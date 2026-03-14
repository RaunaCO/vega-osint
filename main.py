import discord
import os
import asyncio
import json
from dotenv import load_dotenv
from utils.database import inicializar_db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

asyncio.set_event_loop(asyncio.new_event_loop())

inicializar_db()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)

# Cargar módulos desde modules.json
with open("modules.json", "r") as f:
    modulos = json.load(f)["modules"]

modulos_cargados = []
for nombre, config in modulos.items():
    if config["enabled"]:
        bot.load_extension(config["cog"])
        modulos_cargados.append(nombre)
        print(f"[VEGA] Módulo cargado: {nombre}")

@bot.event
async def on_ready():
    print("=" * 40)
    print(f"  VEGA ONLINE — Conectado como {bot.user}")
    print(f"  Servidores activos: {len(bot.guilds)}")
    print(f"  Módulos activos: {', '.join(modulos_cargados)}")
    print("  Protocolo de inteligencia iniciado.")
    print("=" * 40)

@bot.slash_command(guild_ids=[GUILD_ID], description="Verifica que Vega está operativo")
async def ping(ctx):
    latencia = round(bot.latency * 1000)
    await ctx.respond(f"🟢 **VEGA OPERATIVO** — Latencia: `{latencia}ms`")

bot.run(TOKEN)
import discord
import os
import asyncio
import json
from dotenv import load_dotenv
from utils.database import initialize_db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

asyncio.set_event_loop(asyncio.new_event_loop())

# Initialize database on startup
initialize_db()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)

# Load modules from modules.json
with open("modules.json", "r") as f:
    modules = json.load(f)["modules"]

loaded_modules = []
for name, config in modules.items():
    if config["enabled"]:
        bot.load_extension(config["cog"])
        loaded_modules.append(name)
        print(f"[VEGA] Module loaded: {name}")

@bot.event
async def on_ready():
    print("=" * 40)
    print(f"  VEGA ONLINE — Connected as {bot.user}")
    print(f"  Active servers: {len(bot.guilds)}")
    print(f"  Active modules: {', '.join(loaded_modules)}")
    print("  Intelligence protocol initiated.")
    print("=" * 40)

@bot.slash_command(guild_ids=[GUILD_ID], description="Check if Vega is operational")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.respond(f"🟢 **VEGA OPERATIONAL** — Latency: `{latency}ms`")

bot.run(TOKEN)
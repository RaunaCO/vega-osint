import discord
import os
import asyncio
import json
from dotenv import load_dotenv
from utils.database import initialize_db

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

asyncio.set_event_loop(asyncio.new_event_loop())

initialize_db()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = discord.Bot(intents=intents)

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

bot.run(TOKEN)
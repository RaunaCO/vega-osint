import discord
import aiohttp
from discord.ext import commands, tasks
from datetime import datetime, timezone, timedelta, time
from groq import Groq, RateLimitError
from config.settings import (
    GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY, GEMINI_MODEL,
    REGION_CHANNELS, BRIEFING_ROOM_CHANNEL_ID,
    BRIEFING_HOUR, PROMPT_BRIEFING
)

client_groq = Groq(api_key=GROQ_API_KEY)
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/" + GEMINI_MODEL + ":generateContent"

BRIEFING_HOURS = 24

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_briefing.start()

    def cog_unload(self):
        self.daily_briefing.cancel()

    async def call_ai(self, system, user, max_tokens=2000):
        """Groq first, Gemini fallback on 429 via HTTP."""
        try:
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user}
                ],
                max_tokens=max_tokens,
                temperature=0.2
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            print("[VEGA] Scheduler: Groq 429 — switching to Gemini")

        try:
            prompt  = system + "\n\n" + user
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            url     = GEMINI_URL + "?key=" + GEMINI_API_KEY
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print("[VEGA] Scheduler: Gemini fallback error: " + str(e))
            raise

    async def generate_briefing(self):
        admin = self.bot.cogs.get("VegaAdmin")
        now   = datetime.now(timezone.utc)
        since = now - timedelta(hours=BRIEFING_HOURS)

        news_by_region = {}

        for region, channel_id in REGION_CHANNELS.items():
            channel = self.bot.get_channel(channel_id)
            if not channel:
                continue
            entries = []
            async for message in channel.history(limit=200, after=since):
                if message.author == self.bot.user and message.embeds:
                    emb      = message.embeds[0]
                    author   = emb.author.name if emb.author else ""
                    level    = "MEDIUM"
                    location = "N/A"
                    for part in author.split("·"):
                        part = part.strip()
                        if part in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
                            level = part
                    for field in emb.fields:
                        if "Location" in field.name:
                            location = field.value
                    time_str = message.created_at.strftime("%H:%M UTC")
                    entries.append("[" + time_str + "] [" + level + "] " + (emb.title or "") + "  —  " + location)
            if entries:
                news_by_region[region] = entries

        if not news_by_region:
            if admin:
                admin.log("📋 Daily briefing skipped — no activity in last 24h")
            return

        context = ""
        for region, entries in news_by_region.items():
            context += "\n## " + region + "\n" + "\n".join(entries)

        total  = sum(len(e) for e in news_by_region.values())
        prompt = PROMPT_BRIEFING.replace("{hours}", str(BRIEFING_HOURS))

        try:
            content = await self.call_ai(system=prompt, user="Date: " + now.strftime("%Y-%m-%d %H:%M") + " UTC\n\n" + context)
        except Exception as e:
            print("[VEGA] Daily briefing error: " + str(e))
            if admin:
                await admin.report_error("daily_briefing", str(e))
            return

        briefing_channel = self.bot.get_channel(BRIEFING_ROOM_CHANNEL_ID)
        if not briefing_channel:
            return

        if len(content) <= 4000:
            embed = discord.Embed(
                title="Daily Intelligence Briefing  ·  " + now.strftime("%Y-%m-%d"),
                description=content,
                color=0x336699,
                timestamp=now
            )
            embed.set_footer(text=str(total) + " events  ·  last " + str(BRIEFING_HOURS) + "h  ·  VEGA")
            await briefing_channel.send(embed=embed)
        else:
            cut    = content.rfind("\n\n", 0, len(content) // 2)
            embed1 = discord.Embed(
                title="Daily Intelligence Briefing  ·  " + now.strftime("%Y-%m-%d") + "  (1/2)",
                description=content[:cut],
                color=0x336699,
                timestamp=now
            )
            embed2 = discord.Embed(
                title="Daily Intelligence Briefing  ·  " + now.strftime("%Y-%m-%d") + "  (2/2)",
                description=content[cut:],
                color=0x336699,
                timestamp=now
            )
            embed1.set_footer(text=str(total) + " events  ·  last " + str(BRIEFING_HOURS) + "h  ·  VEGA")
            embed2.set_footer(text="VEGA  ·  continued")
            await briefing_channel.send(embed=embed1)
            await briefing_channel.send(embed=embed2)

        if admin:
            admin.log("📋 Daily briefing posted — " + str(total) + " events")

    @tasks.loop(time=time(hour=BRIEFING_HOUR, minute=0, tzinfo=timezone.utc))
    async def daily_briefing(self):
        await self.generate_briefing()

    @daily_briefing.before_loop
    async def before_daily_briefing(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Scheduler(bot))
import discord
from discord.ext import commands
from groq import Groq
from datetime import datetime, timezone, timedelta
from config.settings import (
    GUILD_ID, GROQ_API_KEY, GROQ_MODEL,
    PROMPT_SITREP, PROMPT_SYSTEM, PROMPT_BRIEFING,
    CONFLICT_CHANNEL_ID, MISSION_LOGS_CHANNEL_ID, REGION_CHANNELS,
    AI_ANALYSIS_CHANNEL_ID, BRIEFING_ROOM_CHANNEL_ID
)
from utils.helpers import search_relevant_news
from utils.database import save_sitrep

client_groq = Groq(api_key=GROQ_API_KEY)

class AIBrain(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def archive_sitrep(self, topic: str, content: str, sources: int, author: str):
        save_sitrep(topic, content, sources, author)
        channel = self.bot.get_channel(MISSION_LOGS_CHANNEL_ID)
        if not channel:
            return
        embed = discord.Embed(
            title=f"SITREP ARCHIVED // {topic.upper()}",
            description=content[:4000],
            color=0x1a1a2e,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_author(name="[VEGA] MISSION LOGS")
        embed.set_footer(text=f"{sources} sources // requested by {author}")
        await channel.send(embed=embed)

    async def post_to_channel(self, channel_id: int, embed: discord.Embed):
        """Helper to post an embed to a specific channel."""
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(embed=embed)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Generate a SITREP based on real-time news")
    async def sitrep(self, ctx, topic: str):
        await ctx.defer()
        try:
            news = await search_relevant_news(topic)
            context = "REAL NEWS:\n\n" + "\n\n---\n\n".join(news) if news else f"No recent news on '{topic}'. Use historical context marking [HISTORICAL CONTEXT]."

            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_SITREP},
                    {"role": "user", "content": f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\nTopic: {topic}\n\n{context}"}
                ],
                max_tokens=1024,
                temperature=0.2
            )
            content = response.choices[0].message.content[:4000]

            embed = discord.Embed(
                title=f"SITREP // {topic.upper()}",
                description=content,
                color=0x1a1a2e,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_author(name="[VEGA] SITUATION REPORT")
            embed.set_footer(text=f"{len(news)} sources analyzed // VEGA")
            await ctx.respond(embed=embed)
            await self.archive_sitrep(topic, content, len(news), ctx.author.display_name)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.log(f"📋 /sitrep: {topic[:40]} — {len(news)} sources")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")
            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                await admin.report_error("sitrep", str(e))

    @discord.slash_command(guild_ids=[GUILD_ID], description="Analyze any text with AI")
    async def analyze(self, ctx, text: str):
        await ctx.defer()
        try:
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_SYSTEM},
                    {"role": "user", "content": f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nAnalyze this text from a geopolitical intelligence perspective:\n\n{text}"}
                ],
                max_tokens=800,
                temperature=0.2
            )
            embed = discord.Embed(
                title="INTEL ANALYSIS",
                description=response.choices[0].message.content,
                color=0x1a1a2e,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_author(name="[VEGA] AI ANALYSIS MODULE")
            embed.set_footer(text=f"requested by {ctx.author.display_name} // VEGA")
            await ctx.respond(embed=embed)

            await self.post_to_channel(AI_ANALYSIS_CHANNEL_ID, embed)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.log(f"🧠 /analyze by {ctx.author.display_name}")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")
            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                await admin.report_error("analyze", str(e))

    @discord.slash_command(guild_ids=[GUILD_ID], description="Summarize latest news from the intelligence channel")
    async def summary(self, ctx, count: int = 10):
        await ctx.defer()
        try:
            channel = self.bot.get_channel(CONFLICT_CHANNEL_ID)
            if not channel:
                await ctx.respond("⚠️ **VEGA** — Channel not found.")
                return

            messages = []
            async for message in channel.history(limit=count):
                if message.author == self.bot.user and message.embeds:
                    embed = message.embeds[0]
                    messages.append(f"• {embed.title or ''}\n{(embed.description or '')[:200]}")

            if not messages:
                await ctx.respond("⚠️ **VEGA** — No recent news found.")
                return

            messages.reverse()
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_SYSTEM},
                    {"role": "user", "content": f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\nGenerate an executive summary:\n\n" + "\n\n".join(messages)}
                ],
                max_tokens=800,
                temperature=0.2
            )
            embed = discord.Embed(
                title=f"EXEC SUMMARY // LAST {len(messages)} ENTRIES",
                description=response.choices[0].message.content,
                color=0x1a1a2e,
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_author(name="[VEGA] INTELLIGENCE DIGEST")
            embed.set_footer(text=f"{len(messages)} entries processed // requested by {ctx.author.display_name}")
            await ctx.respond(embed=embed)

            await self.post_to_channel(BRIEFING_ROOM_CHANNEL_ID, embed)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.log(f"📊 /summary by {ctx.author.display_name}")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")
            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                await admin.report_error("summary", str(e))

    @discord.slash_command(guild_ids=[GUILD_ID], description="Intelligence briefing for the last N hours by region")
    async def briefing(self, ctx, hours: discord.Option(int, description="Hours to look back (default: 8)", default=8)):
        await ctx.defer()
        try:
            now = datetime.now(timezone.utc)
            since = now - timedelta(hours=hours)
            news_by_region = {}

            for region, channel_id in REGION_CHANNELS.items():
                channel = self.bot.get_channel(channel_id)
                if not channel:
                    continue
                entries = []
                async for message in channel.history(limit=100, after=since):
                    if message.author == self.bot.user and message.embeds:
                        embed = message.embeds[0]
                        level = next((f.value for f in embed.fields if "Level" in f.name), "MEDIUM")
                        location = next((f.value for f in embed.fields if "Location" in f.name), "N/A")
                        time_str = message.created_at.strftime("%H:%M UTC")
                        entries.append(f"[{time_str}] [{level}] {embed.title} — 📍{location}")
                if entries:
                    news_by_region[region] = entries

            if not news_by_region:
                await ctx.respond(f"⚠️ **VEGA** — No activity recorded in the last {hours} hours.")
                return

            context = ""
            for region, entries in news_by_region.items():
                context += f"\n## {region}\n" + "\n".join(entries)

            prompt = PROMPT_BRIEFING.replace("{hours}", str(hours))
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Date: {now.strftime('%Y-%m-%d %H:%M')} UTC\n\n{context}"}
                ],
                max_tokens=2000,
                temperature=0.2
            )

            content = response.choices[0].message.content
            total = sum(len(e) for e in news_by_region.values())

            if len(content) <= 4000:
                embed = discord.Embed(
                    title=f"INTELLIGENCE BRIEFING // {now.strftime('%Y-%m-%d')}",
                    description=content,
                    color=0x1a1a2e,
                    timestamp=now
                )
                embed.set_author(name="[VEGA] REGIONAL BRIEFING")
                embed.set_footer(text=f"{total} events // last {hours}h // requested by {ctx.author.display_name}")
                await ctx.respond(embed=embed)

                await self.post_to_channel(BRIEFING_ROOM_CHANNEL_ID, embed)
            else:
                cut = content.rfind("\n\n", 0, len(content)//2)
                embed1 = discord.Embed(
                    title=f"INTELLIGENCE BRIEFING // {now.strftime('%Y-%m-%d')} // PART 1",
                    description=content[:cut],
                    color=0x1a1a2e,
                    timestamp=now
                )
                embed2 = discord.Embed(
                    title=f"INTELLIGENCE BRIEFING // {now.strftime('%Y-%m-%d')} // PART 2",
                    description=content[cut:],
                    color=0x1a1a2e,
                    timestamp=now
                )
                embed1.set_author(name="[VEGA] REGIONAL BRIEFING")
                embed2.set_author(name="[VEGA] REGIONAL BRIEFING — CONTINUED")
                embed1.set_footer(text=f"{total} events // last {hours}h")
                embed2.set_footer(text="VEGA // continued")
                await ctx.respond(embed=embed1)
                await ctx.followup.send(embed=embed2)

                await self.post_to_channel(BRIEFING_ROOM_CHANNEL_ID, embed1)
                await self.post_to_channel(BRIEFING_ROOM_CHANNEL_ID, embed2)

            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                admin.log(f"🌅 /briefing by {ctx.author.display_name} — {total} events")
        except Exception as e:
            await ctx.respond(f"⚠️ **VEGA** — Error: `{e}`")
            admin = self.bot.cogs.get("VegaAdmin")
            if admin:
                await admin.report_error("briefing", str(e))

def setup(bot):
    bot.add_cog(AIBrain(bot))
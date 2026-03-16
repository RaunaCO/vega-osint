import discord
import feedparser
import json
import json as json_lib
import asyncio
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from groq import Groq
from config.settings import (
    GUILD_ID, CONFLICT_CHANNEL_ID, CRITICAL_CHANNEL_ID, REGION_CHANNELS,
    KEYWORDS, CRITICAL_KEYWORDS,
    GROQ_API_KEY, GROQ_MODEL, PROMPT_CLASSIFY, PROMPT_CYCLE, PROMPT_ALERT
)
from utils.helpers import strip_html, load_seen, save_seen, detect_and_translate, extract_image
from utils.database import save_article, save_source_status

client_groq = Groq(api_key=GROQ_API_KEY)

def load_sources() -> dict:
    try:
        with open("sources.json", "r") as f:
            sources = json_lib.load(f)["sources"]
        return {s["name"]: s["url"] for s in sources if s["enabled"]}
    except Exception as e:
        print(f"[VEGA] Error loading sources: {e}")
        return {}

def color_by_level(level: str) -> int:
    return {
        "CRITICAL": 0xcc2200,
        "HIGH":     0xdd5500,
        "MEDIUM":   0xccaa00,
        "LOW":      0x448844,
    }.get(level, 0x555555)

def badge(level: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")

class Intel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen = load_seen()
        self.cycle_message = None
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    def get_admin(self):
        return self.bot.cogs.get("VegaAdmin")

    async def classify_article(self, title: str, summary: str, source: str) -> dict:
        try:
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CLASSIFY},
                    {"role": "user", "content": f"Title: {title}\nSummary: {summary}\nSource: {source}"}
                ],
                max_tokens=300,
                temperature=0.1
            )
            content = response.choices[0].message.content.strip().replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"[VEGA] Classification error: {e}")
            return {
                "level": "MEDIUM", "is_critical": False, "region": "Global",
                "category": "Other", "key_actors": [],
                "precise_location": "Not specified", "confidence": "LOW",
                "reason": "Automatic classification failed"
            }

    async def post_article_embed(self, article: dict, classification: dict):
        region     = classification.get("region", "Global")
        channel_id = REGION_CHANNELS.get(region)
        if not channel_id:
            return
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        level      = classification["level"]
        category   = classification.get("category", "Other")
        confidence = classification.get("confidence", "MEDIUM")
        location   = classification.get("precise_location", "—")
        actors     = ", ".join(classification.get("key_actors", [])) or "—"
        reason     = classification.get("reason", "")

        title = article["title"][:250]
        if article.get("translated") and article.get("original_title"):
            title = f"{article['title'][:220]} *(translated)*"

        # Description = summary then reason in italics — no labels needed
        description = article["summary"][:400]
        if reason:
            description += f"\n\n*{reason}*"

        embed = discord.Embed(
            title=title,
            url=article["link"],
            description=description,
            color=color_by_level(level),
            timestamp=datetime.utcnow()
        )

        # Author line = all classification context in one clean line
        embed.set_author(name=f"{badge(level)}  {region}  ·  {level}  ·  {category}")

        # Three inline fields — everything useful, nothing redundant
        embed.add_field(name="Location",   value=location[:60], inline=True)
        embed.add_field(name="Actors",     value=actors[:80],   inline=True)
        embed.add_field(name="Confidence", value=confidence,    inline=True)

        if article.get("image"):
            embed.set_image(url=article["image"])

        embed.set_footer(text=f"{article['source']}  ·  {article.get('date', 'N/A')}")
        await channel.send(embed=embed)

    async def post_critical_alert(self, article: dict, classification: dict):
        channel = self.bot.get_channel(CRITICAL_CHANNEL_ID)
        if not channel:
            return
        try:
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_ALERT},
                    {"role": "user", "content": (
                        f"Title: {article['title']}\n"
                        f"Summary: {article['summary']}\n"
                        f"Source: {article['source']}\n"
                        f"Level: {classification['level']}\n"
                        f"Region: {classification['region']}\n"
                        f"Category: {classification['category']}\n"
                        f"Actors: {', '.join(classification.get('key_actors', []))}\n"
                        f"Location: {classification.get('precise_location', 'N/A')}"
                    )}
                ],
                max_tokens=400,
                temperature=0.2
            )
            level    = classification["level"]
            region   = classification["region"]
            category = classification["category"]
            location = classification.get("precise_location", "—")
            actors   = ", ".join(classification.get("key_actors", [])) or "—"

            embed = discord.Embed(
                title=article["title"][:250],
                url=article["link"],
                description=response.choices[0].message.content,
                color=color_by_level(level),
                timestamp=datetime.utcnow()
            )
            embed.set_author(name=f"{badge(level)}  {level} ALERT  ·  {region}  ·  {category}")
            embed.add_field(name="Location", value=location[:60], inline=True)
            embed.add_field(name="Actors",   value=actors[:80],   inline=True)
            embed.set_footer(text=f"{article['source']}  ·  VEGA")

            if article.get("image"):
                embed.set_image(url=article["image"])

            await channel.send(content="@everyone" if level == "CRITICAL" else "", embed=embed)

            admin = self.get_admin()
            if admin:
                admin.log(f"{badge(level)} {level} Alert: {article['title'][:45]}...")
        except Exception as e:
            print(f"[VEGA] Alert error: {e}")
            admin = self.get_admin()
            if admin:
                await admin.report_error("critical_alert", str(e))

    async def update_cycle_report(self, channel, content: str, articles: list):
        has_critical = any(a.get("classification", {}).get("level") == "CRITICAL" for a in articles)
        image = next((a["image"] for a in articles if a.get("image")), None)

        embed = discord.Embed(
            description=content[:4000],
            color=0xcc2200 if has_critical else 0x336699,
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"Cycle Report  ·  {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
        if image:
            embed.set_thumbnail(url=image)
        embed.set_footer(text=f"{len(articles)} articles processed  ·  VEGA")

        try:
            if self.cycle_message:
                await self.cycle_message.edit(embed=embed)
            else:
                await channel.purge(limit=5)
                self.cycle_message = await channel.send(embed=embed)
        except discord.NotFound:
            self.cycle_message = await channel.send(embed=embed)
        except Exception as e:
            print(f"[VEGA] Cycle report update error: {e}")

    async def run_scan(self):
        admin = self.get_admin()
        if admin:
            admin.log("📡 Starting source scan...")

        main_channel = self.bot.get_channel(CONFLICT_CHANNEL_ID)
        if not main_channel:
            return

        new_articles = []
        news_feeds = load_sources()

        if admin:
            admin.log(f"📚 Loaded {len(news_feeds)} sources")

        async with aiohttp.ClientSession() as session:
            for source, url in news_feeds.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        feed = feedparser.parse(await resp.text())
                        source_hits = 0
                        for entry in feed.entries[:2]:
                            title    = entry.get("title", "")
                            link     = entry.get("link", "")
                            summary  = strip_html(entry.get("summary", ""))[:400]
                            pub_date = entry.get("published", "")[:30] if entry.get("published") else "N/A"
                            image    = extract_image(entry)

                            if link in self.seen:
                                continue
                            if any(k in title.lower() for k in KEYWORDS):
                                self.seen.add(link)
                                save_seen(self.seen)

                                title_en, was_translated = detect_and_translate(title)
                                summary_en, _ = detect_and_translate(summary)

                                new_articles.append({
                                    "title": title_en,
                                    "original_title": title if was_translated else None,
                                    "summary": summary_en,
                                    "source": source,
                                    "link": link,
                                    "date": pub_date,
                                    "image": image,
                                    "translated": was_translated
                                })
                                source_hits += 1

                                if admin:
                                    admin.log(f"🟠 [{source}] {title_en[:45]}...")
                                    admin.log_article({
                                        "title": title_en,
                                        "level": "MEDIUM",
                                        "region": "Global",
                                        "time": datetime.utcnow().strftime("%H:%M")
                                    })

                        save_source_status(source, True)

                except Exception as e:
                    print(f"[VEGA] Feed error {source}: {e}")
                    save_source_status(source, False, str(e)[:200])
                    if admin:
                        admin.log(f"⚠️ Feed error {source}: {str(e)[:40]}")

        if not new_articles:
            if admin:
                admin.log("✅ Scan complete — No new articles")
            return

        new_articles = new_articles[:5]

        if admin:
            admin.log(f"🧠 Classifying {len(new_articles)} articles...")

        for article in new_articles:
            classification = await self.classify_article(article["title"], article["summary"], article["source"])
            article["classification"] = classification
            await self.post_article_embed(article, classification)
            save_article({**article, **classification})

            if admin:
                admin.log_article({
                    "title": article["title"],
                    "level": classification.get("level", "MEDIUM"),
                    "region": classification.get("region", "Global"),
                    "time": datetime.utcnow().strftime("%H:%M")
                })

            if classification["level"] in ["CRITICAL", "HIGH"]:
                await self.post_critical_alert(article, classification)
            await asyncio.sleep(4)

        context = "\n".join([
            f"{i}. {a['title']} | {a['source']} | {a.get('classification', {}).get('region', 'Global')} | {a.get('classification', {}).get('level', 'MEDIUM')} | {a['summary'][:200]}"
            for i, a in enumerate(new_articles, 1)
        ])

        try:
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": PROMPT_CYCLE},
                    {"role": "user", "content": f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n{context}"}
                ],
                max_tokens=600,
                temperature=0.2
            )
            await self.update_cycle_report(main_channel, response.choices[0].message.content, new_articles)

            if admin:
                admin.increment_cycle()
                admin.log(f"✅ Cycle complete — {len(new_articles)} articles processed")
        except Exception as e:
            print(f"[VEGA] Cycle report error: {e}")
            if admin:
                admin.log(f"❌ Cycle report error: {str(e)[:50]}")
                await admin.report_error("cycle_report", str(e))

    @tasks.loop(minutes=15)
    async def monitor(self):
        await self.run_scan()

    @monitor.before_loop
    async def before_monitor(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(30)

    @discord.slash_command(guild_ids=[GUILD_ID], description="Scan all sources right now")
    async def scanfeed(self, ctx):
        await ctx.defer()
        await ctx.respond("📡 **VEGA** — Scanning sources...")
        await self.run_scan()

def setup(bot):
    bot.add_cog(Intel(bot))
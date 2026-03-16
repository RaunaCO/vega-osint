import discord
import feedparser
import json
import json as json_lib
import asyncio
from discord.ext import commands, tasks
import aiohttp
from datetime import datetime
from groq import Groq, RateLimitError
from config.settings import (
    CONFLICT_CHANNEL_ID, CRITICAL_CHANNEL_ID, REGION_CHANNELS,
    KEYWORDS, CRITICAL_KEYWORDS, GROQ_API_KEY, GROQ_MODEL,
    GEMINI_API_KEY, GEMINI_MODEL,
    PROMPT_CLASSIFY, PROMPT_CYCLE, PROMPT_ALERT
)
from utils.helpers import strip_html, load_seen, save_seen, detect_and_translate, extract_image
from utils.database import save_article, save_source_status

client_groq = Groq(api_key=GROQ_API_KEY)

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Max consecutive failures before a source is auto-disabled in sources.json
MAX_SOURCE_FAILURES = 3

# Topics that slip through global sources but are not intelligence-relevant
EXCLUDE_KEYWORDS = [
    "scored", "goal", "goals", "match", "tournament", "championship",
    "league", "fixture", "standings", "transfer", "signing",
    "album", "concert", "tour", "box office", "award", "oscar",
    "grammy", "celebrity", "kardashian", "weather forecast",
    "recipe", "fashion week", "earnings report",
    "quarterly results", "merger", "acquisition"
]

def load_sources() -> dict:
    try:
        with open("sources.json", "r") as f:
            sources = json_lib.load(f)["sources"]
        return {s["name"]: s["url"] for s in sources if s["enabled"]}
    except Exception as e:
        print(f"[VEGA] Error loading sources: {e}")
        return {}

def disable_source(name: str):
    """Mark a source as disabled in sources.json after repeated failures."""
    try:
        with open("sources.json", "r") as f:
            data = json_lib.load(f)
        for source in data["sources"]:
            if source["name"] == name:
                source["enabled"] = False
                break
        with open("sources.json", "w") as f:
            json_lib.dump(data, f, indent=2)
        print(f"[VEGA] Source auto-disabled: {name}")
    except Exception as e:
        print(f"[VEGA] Error disabling source {name}: {e}")

def color_by_level(level: str) -> int:
    return {
        "CRITICAL": 0xcc2200,
        "HIGH":     0xdd5500,
        "MEDIUM":   0xccaa00,
        "LOW":      0x448844,
    }.get(level, 0x555555)

def badge(level: str) -> str:
    return {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")

def score_article(title: str, summary: str) -> int:
    """
    Score article relevance. Minimum passing score: 3.
    Critical keyword in title = 10 (instant pass).
    Regular keyword in title  = 2 pts, in summary = 1 pt.
    """
    title_low   = title.lower()
    summary_low = summary.lower()
    if any(k in title_low for k in CRITICAL_KEYWORDS):
        return 10
    score = 0
    for k in KEYWORDS:
        kl = k.lower()
        if kl in title_low:
            score += 2
        elif kl in summary_low:
            score += 1
    return score

def is_excluded(title: str, summary: str) -> bool:
    combined = (title + " " + summary).lower()
    return any(ex in combined for ex in EXCLUDE_KEYWORDS)

def clean_summary(raw: str) -> str:
    """Strip HTML, collapse whitespace, cut at last full stop within 220 chars."""
    text = strip_html(raw).strip()
    text = " ".join(text.split())
    if not text:
        return ""
    chunk = text[:220]
    cut   = chunk.rfind(". ")
    return chunk[:cut + 1] if cut > 80 else chunk

class Intel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.seen = load_seen()
        self.cycle_message    = None
        self.articles_today   = 0
        self.sources_last_scan = 0
        # Track consecutive failures per source name
        self.source_failures  = {}
        self.monitor.start()

    def cog_unload(self):
        self.monitor.cancel()

    def get_admin(self):
        return self.bot.cogs.get("VegaAdmin")

    async def call_ai(self, system: str, user: str, max_tokens: int = 300) -> str:
        """
        Call Groq first. On RateLimitError (429) fall back to Gemini via HTTP.
        Returns the raw text response.
        """
        # --- Groq ---
        try:
            response = client_groq.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            print("[VEGA] Groq rate limit hit — switching to Gemini fallback")
            admin = self.get_admin()
            if admin:
                admin.log("⚠️ Groq 429 — Gemini fallback active")

        # --- Gemini fallback via HTTP (Python 3.8 compatible) ---
        try:
            prompt = f"{system}\n\n{user}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            print(f"[VEGA] Gemini fallback error: {e}")
            raise

    async def classify_article(self, title: str, summary: str, source: str) -> dict:
        try:
            raw = await self.call_ai(
                system=PROMPT_CLASSIFY,
                user=f"Title: {title}\nSummary: {summary}\nSource: {source}",
                max_tokens=300
            )
            content = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"[VEGA] Classification error: {e}")
            return {
                "level": "MEDIUM", "is_critical": False, "region": "Global",
                "category": "Other", "key_actors": [],
                "precise_location": "Not specified", "confidence": "LOW",
                "reason": ""
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

        description = article["short_summary"]
        if reason and "classification failed" not in reason.lower():
            description += f"\n\n*{reason}*"
        description += f"\n\n[→ {article['source']}]({article['link']})"

        embed = discord.Embed(
            title=title,
            description=description,
            color=color_by_level(level),
            timestamp=datetime.utcnow()
        )
        embed.set_author(name=f"{badge(level)}  {region}  ·  {level}  ·  {category}")
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
            raw = await self.call_ai(
                system=PROMPT_ALERT,
                user=(
                    f"Title: {article['title']}\n"
                    f"Summary: {article['summary']}\n"
                    f"Source: {article['source']}\n"
                    f"Level: {classification['level']}\n"
                    f"Region: {classification['region']}\n"
                    f"Category: {classification['category']}\n"
                    f"Actors: {', '.join(classification.get('key_actors', []))}\n"
                    f"Location: {classification.get('precise_location', 'N/A')}"
                ),
                max_tokens=400
            )
            level    = classification["level"]
            region   = classification["region"]
            category = classification["category"]
            location = classification.get("precise_location", "—")
            actors   = ", ".join(classification.get("key_actors", [])) or "—"

            embed = discord.Embed(
                title=article["title"][:250],
                description=raw,
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

        new_articles   = []
        news_feeds     = load_sources()
        self.sources_last_scan = len(news_feeds)

        if admin:
            admin.log(f"📚 Loaded {len(news_feeds)} sources")

        async with aiohttp.ClientSession() as session:
            for source, url in news_feeds.items():
                try:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        feed = feedparser.parse(await resp.text())
                        for entry in feed.entries[:2]:
                            title    = entry.get("title", "")
                            link     = entry.get("link", "")
                            raw_sum  = entry.get("summary", "")
                            pub_date = entry.get("published", "")[:30] if entry.get("published") else "N/A"
                            image    = extract_image(entry)

                            if link in self.seen:
                                continue

                            summary       = strip_html(raw_sum)[:400]
                            short_summary = clean_summary(raw_sum)

                            if is_excluded(title, summary):
                                continue
                            if score_article(title, summary) < 3:
                                continue

                            self.seen.add(link)
                            save_seen(self.seen)

                            title_en, was_translated = detect_and_translate(title)
                            summary_en, _            = detect_and_translate(summary)
                            short_en, _              = detect_and_translate(short_summary) if short_summary else (short_summary, False)

                            new_articles.append({
                                "title":          title_en,
                                "original_title": title if was_translated else None,
                                "summary":        summary_en,
                                "short_summary":  short_en,
                                "source":         source,
                                "link":           link,
                                "date":           pub_date,
                                "image":          image,
                                "translated":     was_translated
                            })

                            if admin:
                                admin.log(f"🟠 [{source}] {title_en[:45]}...")
                                admin.log_article({
                                    "title":  title_en,
                                    "level":  "MEDIUM",
                                    "region": "Global",
                                    "time":   datetime.utcnow().strftime("%H:%M")
                                })

                    # Success — reset failure counter for this source
                    self.source_failures[source] = 0
                    save_source_status(source, True)

                except Exception as e:
                    print(f"[VEGA] Feed error {source}: {e}")
                    save_source_status(source, False, str(e)[:200])

                    # Increment failure counter
                    self.source_failures[source] = self.source_failures.get(source, 0) + 1
                    fails = self.source_failures[source]

                    if admin:
                        admin.log(f"⚠️ Feed error {source} ({fails}/{MAX_SOURCE_FAILURES}): {str(e)[:40]}")

                    # Auto-disable after MAX_SOURCE_FAILURES consecutive failures
                    if fails >= MAX_SOURCE_FAILURES:
                        disable_source(source)
                        self.source_failures[source] = 0
                        if admin:
                            admin.log(f"🔴 Source auto-disabled: {source}")
                            await admin.report_error("source_disabled", f"{source} disabled after {MAX_SOURCE_FAILURES} consecutive failures")

        if not new_articles:
            if admin:
                admin.log("✅ Scan complete — No new articles")
            return

        new_articles = new_articles[:5]
        self.articles_today += len(new_articles)

        if admin:
            admin.log(f"🧠 Classifying {len(new_articles)} articles...")

        for article in new_articles:
            classification = await self.classify_article(article["title"], article["summary"], article["source"])
            article["classification"] = classification
            await self.post_article_embed(article, classification)
            save_article({**article, **classification})

            if admin:
                admin.log_article({
                    "title":  article["title"],
                    "level":  classification.get("level", "MEDIUM"),
                    "region": classification.get("region", "Global"),
                    "time":   datetime.utcnow().strftime("%H:%M")
                })

            if classification["level"] in ["CRITICAL", "HIGH"]:
                await self.post_critical_alert(article, classification)
            await asyncio.sleep(4)

        context = "\n".join([
            f"{i}. {a['title']} | {a['source']} | {a.get('classification', {}).get('region', 'Global')} | {a.get('classification', {}).get('level', 'MEDIUM')} | {a['summary'][:200]}"
            for i, a in enumerate(new_articles, 1)
        ])

        try:
            raw = await self.call_ai(
                system=PROMPT_CYCLE,
                user=f"Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC\n\n{context}",
                max_tokens=600
            )
            await self.update_cycle_report(main_channel, raw, new_articles)

            if admin:
                admin.increment_cycle()
                admin.set_scan_stats(self.sources_last_scan, self.articles_today)
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

def setup(bot):
    bot.add_cog(Intel(bot))
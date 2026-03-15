import re
import json
import os
import aiohttp
import feedparser
from deep_translator import GoogleTranslator
from langdetect import detect, LangDetectException
from config.settings import NEWS_FEEDS

SEEN_PATH = "data/seen.json"

def strip_html(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r'<[^>]+>', '', text).strip()

def detect_and_translate(text: str):
    """
    Detect language and translate to English if not already English.
    Returns (translated_text, was_translated).
    """
    if not text or len(text) < 10:
        return text, False
    try:
        lang = detect(text)
        if lang == "en":
            return text, False
        translated = GoogleTranslator(source="auto", target="en").translate(text)
        return translated, True
    except LangDetectException:
        return text, False
    except Exception as e:
        print(f"[VEGA] Translation error: {e}")
        return text, False

def load_seen() -> set:
    """Load seen article links from database or fallback JSON."""
    try:
        from utils.database import get_all_links
        return get_all_links()
    except Exception:
        if os.path.exists(SEEN_PATH):
            with open(SEEN_PATH, "r") as f:
                return set(json.load(f))
        return set()

def save_seen(seen: set):
    """Save seen article links to fallback JSON."""
    with open(SEEN_PATH, "w") as f:
        json.dump(list(seen), f)

def extract_image(entry) -> str:
    """Extract image URL from a feed entry."""
    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            if media.get("type", "").startswith("image"):
                return media.get("url", "")
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url", "")
    summary_raw = entry.get("summary", "")
    match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary_raw)
    if match:
        return match.group(1)
    return ""

async def search_relevant_news(topic: str, max_results: int = 8) -> list:
    """Search news feeds for articles relevant to a given topic."""
    keywords = re.split(r'[\s\-,]+', topic.lower())
    found = []
    async with aiohttp.ClientSession() as session:
        for source, url in NEWS_FEEDS.items():
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    content = await resp.text()
                    feed = feedparser.parse(content)
                    for entry in feed.entries[:15]:
                        title = entry.get("title", "")
                        summary = strip_html(entry.get("summary", ""))[:300]
                        link = entry.get("link", "")
                        if any(k in title.lower() or k in summary.lower() for k in keywords):
                            found.append(f"[{source}] {title}\n{summary}\nSource: {link}")
            except Exception as e:
                print(f"[VEGA] Feed error {source}: {e}")
    return found[:max_results]
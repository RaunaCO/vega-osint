import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# DISCORD
# ============================================
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CONFLICT_CHANNEL_ID = int(os.getenv("CONFLICT_CHANNEL_ID"))
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID"))
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID"))
CRITICAL_CHANNEL_ID = int(os.getenv("CRITICAL_CHANNEL_ID"))
OSINT_HITS_CHANNEL_ID = int(os.getenv("OSINT_HITS_CHANNEL_ID"))
MISSION_LOGS_CHANNEL_ID = int(os.getenv("MISSION_LOGS_CHANNEL_ID"))
COMMAND_CENTER_ID = int(os.getenv("COMMAND_CENTER_ID"))
VEGA_ERRORS_CHANNEL_ID = int(os.getenv("VEGA_ERRORS_CHANNEL_ID"))
AI_ANALYSIS_CHANNEL_ID = int(os.getenv("AI_ANALYSIS_CHANNEL_ID"))
BRIEFING_ROOM_CHANNEL_ID = int(os.getenv("BRIEFING_ROOM_CHANNEL_ID"))
EVIDENCE_VAULT_CHANNEL_ID = int(os.getenv("EVIDENCE_VAULT_CHANNEL_ID"))

# REGION_CHANNELS maps the region string returned by the AI classifier
# to the Discord channel ID where articles get routed.
# "Asia-Pacific" replaces "Asia" to include Oceania (Australia, NZ, Pacific Islands).
# The Discord channel ID (REGION_ASIA_ID) is the same — no .env change needed.
REGION_CHANNELS = {
    "Middle East":  int(os.getenv("REGION_MEDIO_ORIENTE_ID")),
    "Europe":       int(os.getenv("REGION_EUROPA_ID")),
    "Africa":       int(os.getenv("REGION_AFRICA_ID")),
    "Asia-Pacific": int(os.getenv("REGION_ASIA_ID")),   # covers Asia + Oceania
    "Americas":     int(os.getenv("REGION_AMERICAS_ID")),
}

# ============================================
# AI
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
MONITOR_INTERVAL = 15

# ============================================
# NEWS SOURCES (legacy static dict — system now uses sources.json)
# ============================================
NEWS_FEEDS = {
    "BBC World":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera":       "https://www.aljazeera.com/xml/rss/all.xml",
    "DW World":         "https://rss.dw.com/rdf/rss-en-world",
    "Kyiv Independent": "https://kyivindependent.com/feed/",
    "The War Zone":     "https://www.thedrive.com/the-war-zone/rss",
    "Foreign Policy":   "https://foreignpolicy.com/feed/",
    "Military Times":   "https://www.militarytimes.com/arc/outboundfeeds/rss/",
    "Defense News":     "https://www.defensenews.com/arc/outboundfeeds/rss/",
    "France 24":        "https://www.france24.com/en/rss",
    "The Guardian":     "https://www.theguardian.com/world/rss",
}

# ============================================
# FILTERS
# ============================================
KEYWORDS = [
    "war", "conflict", "attack", "strike", "missile", "airstrike",
    "troops", "invasion", "crisis", "bomb", "killed", "casualties",
    "offensive", "ceasefire", "evacuation", "siege", "hostage",
    "nuclear", "drone", "explosion", "forces", "military",
    "NATO", "UN", "Pentagon", "Kremlin", "IDF", "Hamas", "Hezbollah",
    "Ukraine", "Gaza", "Iran", "Israel", "Syria", "Sudan",
    "Yemen", "Taiwan", "Korea", "Russia", "China",
    # Asia-Pacific & Oceania additions
    "Pacific", "Indo-Pacific", "Australia", "AUKUS", "ANZUS",
    "New Zealand", "Papua", "Fiji", "Solomons", "Vanuatu",
    "Philippines", "Indonesia", "Myanmar", "South China Sea",
    "ASEAN", "Quad", "Five Eyes",
    "OSINT", "intelligence", "geopolitics", "satellite", "confirmed",
    "geolocated", "footage", "evidence", "vessel", "aircraft"
]

CRITICAL_KEYWORDS = [
    "nuclear", "killed", "airstrike", "bomb",
    "casualties", "explosion", "massacre", "chemical", "ballistic"
]

# ============================================
# AI PROMPTS
# ============================================
PROMPT_SYSTEM = """You are VEGA, an AI-powered geopolitical intelligence system specializing in conflict analysis and military operations. Tone: technical, direct, no filler. Always respond in English."""

PROMPT_SITREP = """You are VEGA. Generate SITREPs using this exact format:

**CLASSIFICATION:** VEGA-INTEL // DO NOT DISTRIBUTE
**DATE/TIME:** [UTC]
**AREA OF OPERATIONS:** [region]

**EXECUTIVE SUMMARY:** [2-3 sentences]

**KEY DEVELOPMENTS:**
- [point 1]
- [point 2]
- [point 3]

**KEY ACTORS:** [list]
**THREAT ASSESSMENT:** [CRITICAL/HIGH/MEDIUM/LOW]
**TREND:** [ESCALATING/STABLE/DE-ESCALATING]
**OUTLOOK:** [1-2 sentences]

Base analysis ONLY on provided news. If insufficient data, state it clearly."""

PROMPT_CLASSIFY = """Classify this news article. Respond ONLY with valid JSON, no extra text.

LEVELS:
- CRITICAL: NBC weapons use, direct inter-state attack with confirmed casualties, documented massacre
- HIGH: active military offensive, critical infrastructure attacked, serious diplomatic crisis
- MEDIUM: active tensions, troop movements, hostile declarations
- LOW: analysis, context, unconfirmed reports

REGION RULES — follow strictly, geography does not override these rules:
- Middle East   → Israel, Palestine, Iran, Iraq, Syria, Lebanon, Jordan, Yemen,
                  Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman, Egypt, Turkey.
                  *** Iran and Iraq are ALWAYS Middle East, never Asia-Pacific ***
- Europe        → Russia, Ukraine, UK, France, Germany, NATO Europe, Balkans, Caucasus
- Africa        → Sub-Saharan Africa, North Africa, Sahel, Horn of Africa, Libya, Algeria
- Asia-Pacific  → China, Japan, South Korea, North Korea, India, Pakistan, Afghanistan,
                  Southeast Asia, Oceania, Australia, New Zealand, Pacific Islands.
                  *** Do NOT include Iran, Iraq, or any Gulf state here ***
- Americas      → North America, Central America, South America, Caribbean
- Global        → Events spanning 3 or more regions simultaneously

{
  "level": "CRITICAL/HIGH/MEDIUM/LOW",
  "is_critical": true/false,
  "region": "region name",
  "category": "Nuclear/Chemical/Military/Humanitarian/Diplomatic/Terrorism/Intelligence/Other",
  "key_actors": ["actor1"],
  "precise_location": "city or specific region",
  "confidence": "HIGH/MEDIUM/LOW",
  "reason": "one technical sentence"
}"""

PROMPT_CYCLE = """You are VEGA. Generate a brief cycle report:

**📊 CYCLE REPORT [date]**
**OVERVIEW:** [2 sentences]
**ACTIVE REGIONS:** [list with 1 sentence each]
**DOMINANT TREND:** [1 sentence]
**GLOBAL LEVEL:** [CRITICAL/HIGH/MEDIUM/LOW]"""

PROMPT_ALERT = """You are VEGA. Generate a critical alert:

⚠️ **[level] — [category]**
🌍 [region] | 📍 [location]

**SITUATION:** [2 sentences]
**IMMEDIATE IMPACT:** [1-2 sentences]
**KEY ACTORS:** [list]
**24H OUTLOOK:** [1 sentence]

*[source] — [date]*"""

PROMPT_BRIEFING = """You are VEGA. Generate an intelligence briefing:

# 🌅 INTELLIGENCE BRIEFING — [date]
**Period covered:** Last {hours} hours

## EXECUTIVE SUMMARY
[3 sentences on the global picture]

[For each active region:]
## [REGION]
[Chronological events with time and threat level]
**Regional assessment:** [1 sentence]

## OPERATIONAL CONCLUSION
**Most critical event:** [top event]
**Dominant trend:** [pattern]
**Watch list:** [what to monitor next]"""
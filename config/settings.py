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

# Region → Discord channel mapping
# Asia-Pacific covers East/South/Southeast Asia + Oceania (same ID as old REGION_ASIA_ID)
REGION_CHANNELS = {
    "Middle East":  int(os.getenv("REGION_MEDIO_ORIENTE_ID")),
    "Europe":       int(os.getenv("REGION_EUROPA_ID")),
    "Africa":       int(os.getenv("REGION_AFRICA_ID")),
    "Asia-Pacific": int(os.getenv("REGION_ASIA_ID")),
    "Americas":     int(os.getenv("REGION_AMERICAS_ID")),
}

# ============================================
# AI
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
MONITOR_INTERVAL = 15

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

PROMPT_CYCLE = """You are VEGA. Generate a brief cycle report in plain prose. No markdown, no bold, no bullet points, no emojis, no headers.

Write 3–4 sentences total: first describe the overall situation across active regions, then name each active region with one sentence each, then state the dominant trend and global threat level. Be direct and specific."""

PROMPT_ALERT = """You are VEGA. Generate a critical alert in plain prose. No markdown, no bold, no bullet points, no emojis, no headers.

Write 3–4 sentences covering: what happened, where, who is involved, and the immediate 24h outlook. Be specific and technical."""

PROMPT_BRIEFING = """You are VEGA. Generate an intelligence briefing in clean prose. No markdown, no bold, no bullet points, no emojis, no headers.

Structure: one paragraph summarizing the global picture, then one paragraph per active region (start each with the region name), then one closing paragraph with the dominant trend and what to monitor next. Keep each paragraph to 3–4 sentences. Period covered: last {hours} hours."""
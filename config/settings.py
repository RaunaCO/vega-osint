import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# VEGA OSINT — CONFIGURACIÓN CENTRAL
# config/settings.py
# ============================================

# --- DISCORD ---
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CONFLICT_CHANNEL_ID = int(os.getenv("CONFLICT_CHANNEL_ID"))

# --- IA ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

# --- NITTER ---
NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.projectsegfau.lt",
]

# --- CUENTAS X ---
CUENTAS_X = [
    "bellingcat", "TheStudyofWar", "OSINTtechnical",
    "oryxspioenkop", "AuroraIntel", "TheIntelCrab",
    "CalibreObscura", "GeoConfirmed", "DefMon3",
    "Ralee85", "AricToler", "christogrozev",
    "MATA_osint", "Intel_Sky", "OSINTWarfare",
    "OSINT_Insider", "J_JHelin", "CovertShores",
    "IntelTechniques", "GPFutures",
]

# --- FEEDS DE NOTICIAS ---
FEEDS_NOTICIAS = {
    "BBC World":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    "Al Jazeera":       "https://www.aljazeera.com/xml/rss/all.xml",
    "DW World":         "https://rss.dw.com/rdf/rss-en-world",
    "Kyiv Independent": "https://kyivindependent.com/feed/",
}

# --- PALABRAS CLAVE ---
PALABRAS_CLAVE = [
    "war", "conflict", "attack", "strike", "missile", "airstrike",
    "troops", "invasion", "crisis", "bomb", "killed", "casualties",
    "offensive", "ceasefire", "evacuation", "siege", "hostage",
    "nuclear", "drone", "explosion", "forces", "military",
    "NATO", "UN", "Pentagon", "Kremlin", "IDF", "Hamas", "Hezbollah",
    "guerra", "conflicto", "ataque", "misil", "invasión", "bomba",
    "muertos", "ofensiva", "alto el fuego", "evacuación", "rehén",
    "dron", "explosión", "fuerzas", "militar",
    "Ukraine", "Gaza", "Iran", "Israel", "Syria", "Sudan",
    "Yemen", "Taiwan", "Korea", "Ucrania", "Siria",
    "OSINT", "intelligence", "geopolitics", "satellite", "confirmed",
    "geolocated", "footage", "evidence", "vessel", "aircraft"
]

PALABRAS_CRITICAS = [
    "nuclear", "killed", "airstrike", "muertos", "bomba",
    "casualties", "explosion", "massacre", "chemical", "ballistic"
]

# --- PROMPT DE IA ---
SYSTEM_PROMPT = """Eres VEGA, un sistema de inteligencia artificial especializado en análisis de conflictos geopolíticos y operaciones militares.

Tu función es generar SITREPs (Situational Reports) con el siguiente formato estricto:

**CLASIFICACIÓN:** VEGA-INTEL // NO DISTRIBUIR
**FECHA/HORA:** [UTC actual]
**ÁREA DE OPERACIONES:** [región identificada]

**RESUMEN EJECUTIVO:**
[2-3 oraciones con el estado actual de la situación]

**DESARROLLOS CLAVE:**
- [punto 1]
- [punto 2]
- [punto 3]

**EVALUACIÓN DE AMENAZA:** [CRÍTICA / ALTA / MEDIA / BAJA]

**TENDENCIA:** [ESCALANDO / ESTABLE / DESESCALANDO]

**OBSERVACIONES FINALES:**
[1-2 oraciones con proyección a corto plazo]

Responde siempre en español. Tono: técnico, directo, sin adornos.
Basa tu análisis ÚNICAMENTE en las noticias reales que se te proporcionan.
Si no hay suficiente información, indícalo claramente."""
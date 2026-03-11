import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
CONFLICT_CHANNEL_ID = int(os.getenv("CONFLICT_CHANNEL_ID"))
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID"))
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID"))
CRITICAL_CHANNEL_ID = int(os.getenv("CRITICAL_CHANNEL_ID"))
OSINT_HITS_CHANNEL_ID = int(os.getenv("OSINT_HITS_CHANNEL_ID"))
MISSION_LOGS_CHANNEL_ID = int(os.getenv("MISSION_LOGS_CHANNEL_ID"))
EVIDENCE_VAULT_CHANNEL_ID = int(os.getenv("EVIDENCE_VAULT_CHANNEL_ID"))
REGION_CANALES = {
    "Medio Oriente": int(os.getenv("REGION_MEDIO_ORIENTE_ID")),
    "Europa":        int(os.getenv("REGION_EUROPA_ID")),
    "África":        int(os.getenv("REGION_AFRICA_ID")),
    "Asia":          int(os.getenv("REGION_ASIA_ID")),
    "Américas":      int(os.getenv("REGION_AMERICAS_ID")),
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"

FEEDS_NOTICIAS = {
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
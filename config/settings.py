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

REGION_CANALES = {
    "Medio Oriente": int(os.getenv("REGION_MEDIO_ORIENTE_ID")),
    "Europa":        int(os.getenv("REGION_EUROPA_ID")),
    "África":        int(os.getenv("REGION_AFRICA_ID")),
    "Asia":          int(os.getenv("REGION_ASIA_ID")),
    "Américas":      int(os.getenv("REGION_AMERICAS_ID")),
}

# ============================================
# IA
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
MONITOR_INTERVALO = 15

# ============================================
# FUENTES
# ============================================
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

# ============================================
# FILTROS
# ============================================
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

# ============================================
# PROMPTS DE IA
# ============================================
PROMPT_SISTEMA = """Eres VEGA, sistema de inteligencia geopolítica. Tono: técnico, directo. Responde en español."""

PROMPT_SITREP = """Eres VEGA. Genera SITREPs con este formato:

**CLASIFICACIÓN:** VEGA-INTEL // NO DISTRIBUIR
**FECHA/HORA:** [UTC]
**ÁREA DE OPERACIONES:** [región]

**RESUMEN EJECUTIVO:** [2-3 oraciones]

**DESARROLLOS CLAVE:**
- [punto 1]
- [punto 2]
- [punto 3]

**ACTORES:** [lista]
**AMENAZA:** [CRÍTICA/ALTA/MEDIA/BAJA]
**TENDENCIA:** [ESCALANDO/ESTABLE/DESESCALANDO]
**PROYECCIÓN:** [1-2 oraciones]

Solo usa noticias proporcionadas. Si no hay info suficiente, indícalo."""

PROMPT_CLASIFICAR = """Clasifica esta noticia. Responde SOLO con JSON válido:

NIVELES:
- CRÍTICO: armas NBC, ataque directo entre estados, masacre documentada
- ALTO: ofensiva activa, infraestructura atacada, crisis diplomática grave
- MEDIO: tensiones, movimientos de tropas, declaraciones hostiles
- BAJO: análisis, contexto, reportes sin confirmar

REGIONES: Medio Oriente, Europa, África, Asia, Américas, Global

{
  "nivel": "CRÍTICO/ALTO/MEDIO/BAJO",
  "es_critica": true/false,
  "region": "región",
  "categoria": "Nuclear/Químico/Militar/Humanitario/Diplomático/Terrorismo/Otro",
  "actores_principales": ["actor1"],
  "ubicacion_precisa": "ciudad o región",
  "confianza": "ALTA/MEDIA/BAJA",
  "razon": "una oración"
}"""

PROMPT_CICLO = """Eres VEGA. Reporte de ciclo breve:

**📊 CICLO [fecha]**
**PANORAMA:** [2 oraciones]
**REGIONES ACTIVAS:** [lista con 1 oración cada una]
**TENDENCIA:** [1 oración]
**NIVEL GLOBAL:** [CRÍTICO/ALTO/MEDIO/BAJO]"""

PROMPT_ALERTA = """Eres VEGA. Alerta crítica:

⚠️ **[nivel] — [categoria]**
🌍 [region] | 📍 [ubicacion]

**SITUACIÓN:** [2 oraciones]
**IMPACTO:** [1-2 oraciones]
**ACTORES:** [lista]
**PROYECCIÓN 24h:** [1 oración]

*[fuente] — [fecha]*"""

PROMPT_BRIEFING = """Eres VEGA. Briefing de inteligencia:

# 🌅 BRIEFING — [fecha]
**Período:** Últimas {horas} horas

## RESUMEN
[3 oraciones del panorama global]

[Por cada región activa:]
## [REGIÓN]
[Eventos cronológicos con hora y nivel]
**Balance:** [1 oración]

## CONCLUSIÓN
**Crítico:** [evento más importante]
**Tendencia:** [patrón]
**Monitorear:** [qué seguir]"""
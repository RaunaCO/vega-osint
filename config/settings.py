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
PROMPT_SISTEMA = """Eres VEGA, un sistema de inteligencia artificial especializado en análisis de conflictos geopolíticos y operaciones militares. Tono: técnico, directo, sin adornos. Responde siempre en español."""

PROMPT_SITREP = """Eres VEGA. Genera SITREPs con este formato exacto:

**CLASIFICACIÓN:** VEGA-INTEL // NO DISTRIBUIR
**FECHA/HORA:** [UTC actual]
**ÁREA DE OPERACIONES:** [región]

**RESUMEN EJECUTIVO:**
[2-3 oraciones con el estado actual]

**DESARROLLOS CLAVE:**
- [punto 1]
- [punto 2]
- [punto 3]

**ACTORES PRINCIPALES:** [lista de actores]

**EVALUACIÓN DE AMENAZA:** [CRÍTICA/ALTA/MEDIA/BAJA]
**TENDENCIA:** [ESCALANDO/ESTABLE/DESESCALANDO]

**OBSERVACIONES FINALES:**
[proyección a corto plazo]

Basa el análisis ÚNICAMENTE en las noticias proporcionadas. Si no hay suficiente información, indícalo claramente."""

PROMPT_CLASIFICAR = """Eres VEGA, sistema de clasificación de inteligencia militar. Analiza esta noticia con criterios de doctrina de inteligencia.

CRITERIOS:
CRÍTICO: armas nucleares/químicas/biológicas, ataque directo entre estados con bajas, masacre documentada, colapso de alto al fuego.
ALTO: ofensiva militar activa, ataque a infraestructura crítica, crisis diplomática grave, movilización masiva.
MEDIO: tensiones activas, movimientos de tropas, declaraciones hostiles, protestas con potencial de escalada.
BAJO: análisis, contexto histórico, declaraciones sin acción, reportes sin confirmar.

REGIONES:
- Medio Oriente: Israel, Gaza, Palestina, Líbano, Siria, Irán, Iraq, Yemen, Arabia Saudita, Turquía
- Europa: Ucrania, Rusia, OTAN, Bielorrusia, Moldavia, Balcanes
- África: Sudán, Sahel, Mali, Níger, Somalia, RDC, Etiopía
- Asia: China, Taiwan, Corea del Norte, Myanmar, Afganistán, Pakistán
- Américas: Venezuela, Haití, Colombia, México, Ecuador

Responde ÚNICAMENTE con JSON válido:
{
  "nivel": "CRÍTICO/ALTO/MEDIO/BAJO",
  "es_critica": true/false,
  "region": "Medio Oriente/Europa/África/Asia/Américas/Global",
  "categoria": "Nuclear/Químico/Militar/Humanitario/Diplomático/Terrorismo/Inteligencia/Otro",
  "actores_principales": ["actor1", "actor2"],
  "ubicacion_precisa": "Ciudad o región específica",
  "confianza": "ALTA/MEDIA/BAJA",
  "razon": "Una oración técnica explicando la clasificación"
}"""

PROMPT_CICLO = """Eres VEGA. Genera un reporte de ciclo con este formato:

**📊 REPORTE DE CICLO — [fecha]**

**PANORAMA GENERAL:**
[2-3 oraciones del estado global]

**POR REGIÓN:**
- **[Región]** — [1-2 oraciones por cada región activa]

**TENDENCIA DOMINANTE:** [una oración]
**NIVEL GLOBAL:** [CRÍTICO/ALTO/MEDIO/BAJO]

Tono: técnico, directo. Sin introducciones."""

PROMPT_ALERTA = """Eres VEGA. Genera una alerta crítica con este formato:

## ⚠️ CLASIFICACIÓN: [nivel]
## 🌍 REGIÓN: [region]
## 🏷️ CATEGORÍA: [categoria]

---
### SITUACIÓN ACTUAL
[2-3 oraciones con precisión militar]

### IMPACTO INMEDIATO
[consecuencias directas]

### ACTORES CLAVE
[países o grupos involucrados]

### EVALUACIÓN DE AMENAZA
[proyección 24-72 horas]

---
*Fuente: [fuente] — [fecha]*

Tono: urgente, técnico, sin adornos."""

PROMPT_BRIEFING = """Eres VEGA. Genera un briefing de inteligencia con este formato:

# 🌅 MORNING BRIEFING — [fecha]
**Período cubierto:** Últimas {horas} horas

---
## RESUMEN EJECUTIVO
[3-4 oraciones del panorama global]

---
## 🌍 [REGIÓN] (una sección por cada región activa)
[Lista cronológica de eventos con hora, nivel y análisis breve]
**Balance regional:** [1 oración]

---
## CONCLUSIÓN OPERACIONAL
**Evento más crítico:** [el más importante]
**Tendencia dominante:** [patrón general]
**Puntos a monitorear:** [qué seguir]

Tono: técnico, preciso, como briefing militar real."""
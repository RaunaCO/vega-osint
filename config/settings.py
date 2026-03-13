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

PROMPT_CLASIFICAR = """Eres VEGA, sistema de clasificación de inteligencia militar. Analiza esta noticia con criterios de doctrina de inteligencia.

CRITERIOS DE CLASIFICACIÓN:

CRÍTICO — Requiere acción inmediata:
- Uso confirmado de armas nucleares, químicas o biológicas
- Ataque directo entre estados soberanos con bajas confirmadas
- Masacre o crimen de guerra documentado con evidencia
- Escalada que amenaza estabilidad regional inmediata
- Colapso de alto al fuego activo con reanudación de hostilidades

ALTO — Situación grave en desarrollo:
- Ofensiva militar activa con avance territorial confirmado
- Ataque a infraestructura crítica (energía, agua, comunicaciones)
- Crisis diplomática con ruptura de relaciones o expulsión de embajadores
- Movilización militar masiva documentada
- Atentado terrorista de alto impacto

MEDIO — Situación que requiere monitoreo:
- Tensiones diplomáticas activas sin escalada inmediata
- Movimientos de tropas sin contacto confirmado
- Declaraciones hostiles entre líderes de estado
- Protestas o disturbios con potencial de escalada
- Negociaciones en riesgo de colapso

BAJO — Contexto e información de fondo:
- Análisis, opinión o contexto histórico
- Declaraciones de organizaciones internacionales sin acción
- Reportes de inteligencia sin confirmación
- Desarrollos diplomáticos positivos

REGIONES:
- Medio Oriente: Israel, Gaza, Palestina, Líbano, Siria, Irán, Iraq, Yemen, Arabia Saudita, Turquía
- Europa: Ucrania, Rusia, OTAN, Bielorrusia, Moldavia, Balcanes, Europa Oriental
- África: Sudán, Sahel, Mali, Níger, Somalia, RDC, Etiopía, Mozambique
- Asia: China, Taiwan, Corea del Norte, Myanmar, Afganistán, Pakistán, India
- Américas: Venezuela, Haití, Colombia, México, Ecuador

Responde ÚNICAMENTE con JSON válido, sin texto adicional:

{
  "nivel": "CRÍTICO/ALTO/MEDIO/BAJO",
  "es_critica": true/false,
  "region": "Medio Oriente/Europa/África/Asia/Américas/Global",
  "categoria": "Nuclear/Químico/Militar/Humanitario/Diplomático/Terrorismo/Inteligencia/Otro",
  "actores_principales": ["actor1", "actor2"],
  "ubicacion_precisa": "Ciudad, provincia o región específica mencionada en la noticia",
  "confianza": "ALTA/MEDIA/BAJA",
  "razon": "Una sola oración técnica explicando la clasificación"
}"""
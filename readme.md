<div align="center">

# 🛰️ VEGA OSINT
### Protocolo de Inteligencia Sintética

**Plataforma de inteligencia geopolítica en tiempo real impulsada por IA**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-py--cord-5865F2?style=flat-square&logo=discord)](https://pycord.dev)
[![Groq](https://img.shields.io/badge/AI-Groq%20LLaMA-orange?style=flat-square)](https://groq.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## ¿Qué es Vega?

Vega es una plataforma de inteligencia de fuentes abiertas (OSINT) que combina monitoreo automatizado de noticias, análisis con inteligencia artificial y herramientas de reconocimiento digital, todo accesible desde Discord.

No es un bot de noticias. Es un sistema de inteligencia sintética que clasifica, analiza y sintetiza información de conflictos globales en tiempo real.

---

## Capacidades

| Módulo | Descripción |
|--------|-------------|
| 🔴 **Intel** | Monitoreo de 10+ fuentes de noticias con clasificación automática por IA |
| 🧠 **AI Brain** | Generación de SITREPs, briefings y análisis geopolíticos con LLaMA 3.3 |
| 🔍 **OSINT** | Reconocimiento de usuarios en múltiples plataformas |
| ⚙️ **Admin** | Panel de control en vivo, logs y gestión del sistema |

---

## Comandos

### Inteligencia
| Comando | Descripción |
|---------|-------------|
| `/scanfeed` | Escanea todas las fuentes ahora mismo |
| `/sitrep [tema]` | Genera un informe de situación basado en noticias reales |
| `/briefing [horas]` | Resumen cronológico por región de las últimas N horas |
| `/resumen [cantidad]` | Resume las últimas noticias del canal |
| `/analizar [texto]` | Análisis geopolítico de cualquier texto con IA |

### OSINT
| Comando | Descripción |
|---------|-------------|
| `/userrecon [usuario]` | Busca un nombre de usuario en múltiples redes sociales |

### Administración
| Comando | Descripción |
|---------|-------------|
| `/estado` | Panel de estado del sistema |
| `/modulos` | Lista de módulos activos |
| `/pausar [accion]` | Pausa o reanuda el monitor automático |
| `/intervalo [minutos]` | Cambia la frecuencia de escaneo |
| `/limpiar` | Resetea la memoria de noticias vistas |
| `/purgar [canal]` | Elimina todos los mensajes de un canal |
| `/ping` | Verificación de estado |

---

## Arquitectura
```
vega-osint/
├── main.py                 # Punto de entrada — carga módulos desde modules.json
├── modules.json            # Configuración de módulos activos
├── config/
│   └── settings.py         # Variables de entorno y prompts de IA
├── cogs/                   # Módulos del bot
│   ├── intel.py            # Monitor de noticias y clasificación IA
│   ├── ai_brain.py         # SITREPs, briefings y análisis
│   ├── osint.py            # Herramientas de reconocimiento
│   └── admin.py            # Panel de control
├── utils/
│   ├── helpers.py          # Funciones reutilizables
│   └── database.py         # Capa de base de datos SQLite
└── data/
    └── vega.db             # Base de datos persistente
```

---

## Instalación

### Requisitos
- Python 3.8+
- Cuenta de Discord + Bot Token
- Cuenta de Groq (gratuita)

### Pasos

**1. Clonar el repositorio**
```bash
git clone https://github.com/RaunaCO/vega-osint.git
cd vega-osint
```

**2. Crear entorno virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

**3. Instalar dependencias**
```bash
pip install py-cord python-dotenv aiohttp feedparser groq deep-translator langdetect
```

**4. Configurar variables de entorno**
```bash
cp .env.example .env
# Edita .env con tus credenciales
```

**5. Configurar el servidor de Discord**

Crea las siguientes categorías y canales:
```
⫸ VEGA SYSTEM
  #vega-status
  #vega-logs
  #command-center

⫸ INTEL FEED
  #conflict-watch
  #critical-alerts
  #region-medio-oriente
  #region-europa
  #region-africa
  #region-asia
  #region-americas

⫸ OPERATIONS
  #sitrep-request
  #recon-tasks

⫸ ARCHIVE
  #mission-logs
  #osint-hits
  #evidence-vault
```

**6. Iniciar Vega**
```bash
python main.py
```

---

## Variables de entorno

Crea un archivo `.env` basado en este template:
```env
DISCORD_TOKEN=
GUILD_ID=
GROQ_API_KEY=
CONFLICT_CHANNEL_ID=
STATUS_CHANNEL_ID=
LOGS_CHANNEL_ID=
CRITICAL_CHANNEL_ID=
COMMAND_CENTER_ID=
OSINT_HITS_CHANNEL_ID=
MISSION_LOGS_CHANNEL_ID=
REGION_MEDIO_ORIENTE_ID=
REGION_EUROPA_ID=
REGION_AFRICA_ID=
REGION_ASIA_ID=
REGION_AMERICAS_ID=
```

---

## Sistema de módulos

Vega usa un sistema de plugins basado en `modules.json`. Para desactivar un módulo sin borrar código:
```json
{
  "modules": {
    "intel": {
      "enabled": false
    }
  }
}
```

---

## Fuentes de inteligencia

Vega monitorea automáticamente:

- BBC World News
- Al Jazeera
- DW World
- Kyiv Independent
- The War Zone
- Foreign Policy
- Military Times
- Defense News
- France 24
- The Guardian

---

## Roadmap

- [ ] Interfaz web propia
- [ ] API REST para terceros
- [ ] Módulo naval (seguimiento de embarcaciones)
- [ ] Módulo aéreo (seguimiento de aeronaves)
- [ ] Módulo ciberseguridad
- [ ] Soporte multi-servidor
- [ ] Dashboard de estadísticas
- [ ] Soporte para múltiples modelos de IA

---

## Contribuir

Las contribuciones son bienvenidas. Para agregar un nuevo módulo:

1. Crea `cogs/tu_modulo.py` con una clase `Cog` y función `setup(bot)`
2. Agrégalo a `modules.json`
3. Documenta los comandos en este README
4. Abre un Pull Request

---

## Licencia

MIT License — libre para usar, modificar y distribuir.

---

<div align="center">

**Construido con Python, py-cord, Groq LLaMA 3.3 y código abierto**

*Vega OSINT — Inteligencia para todos*

</div>

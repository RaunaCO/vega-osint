<div align="center">

<img src="https://img.shields.io/badge/VEGA-OSINT-red?style=for-the-badge&labelColor=000000" alt="VEGA OSINT"/>

# VEGA OSINT
### Open-Source Synthetic Intelligence Platform

**Real-time geopolitical intelligence powered by AI — built for analysts, researchers, and anyone who needs to stay ahead.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-py--cord-5865F2?style=flat-square&logo=discord&logoColor=white)](https://pycord.dev)
[![Groq](https://img.shields.io/badge/AI-Groq%20LLaMA%203.3-F55036?style=flat-square)](https://groq.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-22C55E?style=flat-square)]()

[Features](#features) • [Quick Start](#quick-start) • [Commands](#commands) • [Architecture](#architecture) • [Roadmap](#roadmap) • [Contributing](#contributing)

</div>

---

## What is VEGA?

VEGA is an open-source intelligence platform that monitors global conflicts in real time, classifies threats using AI, and delivers structured intelligence reports directly to Discord.

It's not a news bot. It's a **synthetic intelligence protocol** — monitoring 10+ sources simultaneously, classifying every article by threat level and region, generating military-grade SITREPs, and maintaining a persistent intelligence database.

Think of it as a lightweight, self-hosted alternative to commercial threat intelligence platforms — completely free and open source.

---

## Features

### 🔴 Real-Time Intelligence Feed
- Monitors 10+ verified sources (BBC, Al Jazeera, Foreign Policy, The War Zone, and more)
- AI-powered classification by threat level: `CRITICAL` `HIGH` `MEDIUM` `LOW`
- Automatic routing to regional channels (Middle East, Europe, Africa, Asia, Americas)
- Critical alerts with `@everyone` mentions for maximum-priority events
- Automatic translation to English for non-English sources

### 🧠 AI-Powered Analysis
- **SITREPs** — Structured situation reports based on real news, not hallucinations
- **Intelligence Briefings** — Chronological regional summaries for any time window
- **Text Analysis** — Geopolitical analysis of any text, URL or raw intelligence
- **Executive Summaries** — Quick synthesis of the latest intelligence feed
- Powered by **LLaMA 3.3 70B** via Groq (free tier)

### 🔍 OSINT Tools
- Username reconnaissance across GitHub, Instagram, TikTok, Twitter/X, Reddit, Pinterest
- Results automatically archived to `#osint-hits`
- Extensible — new platforms can be added in minutes

### ⚙️ System Administration
- **3 live panels** — Status, Activity Log, and Global Situation updated in real time
- Module system — enable/disable capabilities without touching code
- Persistent SQLite database — all intelligence survives restarts
- Hot-reload interval — change scan frequency without restarting

---

## Quick Start

### Prerequisites
- Python 3.8+
- A Discord account + Bot Token ([guide](https://discord.com/developers/applications))
- A free Groq API key ([console.groq.com](https://console.groq.com))

### Installation
```bash
# Clone the repository
git clone https://github.com/RaunaCO/vega-osint.git
cd vega-osint

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install py-cord python-dotenv aiohttp feedparser groq deep-translator langdetect

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Discord Server Setup

Create the following structure in your server:
```
📁 VEGA SYSTEM
  #vega-status        ← Live system status panel
  #vega-logs          ← Real-time activity log
  #command-center     ← Global situation + commands

📁 INTEL FEED
  #conflict-watch     ← Live cycle reports
  #critical-alerts    ← Maximum priority alerts
  #region-middle-east
  #region-europe
  #region-africa
  #region-asia
  #region-americas

📁 ARCHIVE
  #mission-logs       ← SITREP history
  #osint-hits         ← Recon results
```

### Start VEGA
```bash
python main.py
```

---

## Commands

### Intelligence
| Command | Description |
|---------|-------------|
| `/scanfeed` | Trigger an immediate scan of all sources |
| `/sitrep [topic]` | Generate a SITREP from real-time news |
| `/briefing [hours]` | Regional intelligence briefing for the last N hours |
| `/summary [count]` | Executive summary of the latest feed entries |
| `/analyze [text]` | AI geopolitical analysis of any text |

### OSINT
| Command | Description |
|---------|-------------|
| `/userrecon [username]` | Search for a username across 6 major platforms |

### Administration
| Command | Description |
|---------|-------------|
| `/status` | Display current system status |
| `/modules` | List all active modules |
| `/pause [pause\|resume]` | Control the automatic monitor |
| `/interval [minutes]` | Change scan frequency (no restart required) |
| `/clear` | Reset article memory |
| `/purge [channel]` | Delete all messages from a channel |
| `/ping` | Verify bot is operational |

---

## Architecture
```
vega-osint/
├── main.py                 # Entry point — loads modules from modules.json
├── modules.json            # Module configuration — enable/disable without code changes
├── .env.example            # Environment variable template
├── config/
│   └── settings.py         # All configuration, constants and AI prompts
├── cogs/                   # Bot modules (Cogs)
│   ├── intel.py            # News monitoring, AI classification, cycle reports
│   ├── ai_brain.py         # SITREPs, briefings, analysis
│   ├── osint.py            # Username reconnaissance
│   └── admin.py            # Live panels, system control
├── utils/
│   ├── helpers.py          # Shared utilities — translation, parsing, feed fetching
│   └── database.py         # SQLite data layer
└── data/
    └── vega.db             # Persistent intelligence database
```

### Module System

VEGA uses a plugin architecture. To disable a module without deleting code, simply edit `modules.json`:
```json
{
  "modules": {
    "intel": { "enabled": false }
  }
}
```

To add a new module:
1. Create `cogs/your_module.py` with a `Cog` class and `setup(bot)` function
2. Add it to `modules.json`
3. Restart VEGA

---

## Intelligence Sources

| Source | Focus |
|--------|-------|
| BBC World | Global news |
| Al Jazeera | Middle East, Global |
| DW World | Europe, Global |
| Kyiv Independent | Ukraine, Eastern Europe |
| The War Zone | Military, Defense |
| Foreign Policy | Geopolitics, Diplomacy |
| Military Times | US Military |
| Defense News | Defense Industry |
| France 24 | Global, Francophone regions |
| The Guardian | Global, Investigative |

---

## Environment Variables
```env
# Discord
DISCORD_TOKEN=
GUILD_ID=

# AI
GROQ_API_KEY=

# Channels
CONFLICT_CHANNEL_ID=
STATUS_CHANNEL_ID=
LOGS_CHANNEL_ID=
CRITICAL_CHANNEL_ID=
COMMAND_CENTER_ID=
OSINT_HITS_CHANNEL_ID=
MISSION_LOGS_CHANNEL_ID=

# Regional Channels
REGION_MEDIO_ORIENTE_ID=
REGION_EUROPA_ID=
REGION_AFRICA_ID=
REGION_ASIA_ID=
REGION_AMERICAS_ID=
```

---

## Roadmap

### v2.0
- [ ] Web dashboard (React + FastAPI)
- [ ] REST API for third-party integrations
- [ ] Multi-server support

### v2.5
- [ ] Naval module — vessel tracking via AIS
- [ ] Aviation module — aircraft tracking
- [ ] Cyber module — threat intelligence feeds

### v3.0
- [ ] Multiple AI model support (Gemini, Claude, GPT-4)
- [ ] Custom source configuration via Discord
- [ ] Public API with authentication

---

## Contributing

Contributions are welcome. Please read the guidelines before opening a PR.

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit using Conventional Commits: `feat(module): description`
4. Push and open a Pull Request

**Adding a new intelligence source:**
Simply add it to `NEWS_FEEDS` in `config/settings.py` — no other changes needed.

**Adding a new module:**
Create `cogs/your_module.py`, add it to `modules.json`, document commands in this README.

---

## License

MIT License — free to use, modify and distribute.

---

<div align="center">

Built with Python, py-cord, Groq LLaMA 3.3, and open-source tools

**VEGA OSINT — Intelligence for everyone**

⭐ Star this repo if you find it useful

</div>

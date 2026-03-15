<div align="center">

<img src="https://img.shields.io/badge/ASTRAL-NETWORK-red?style=for-the-badge&labelColor=000000" alt="Astral Network"/>

# VEGA OSINT
### Open-Source Synthetic Intelligence Platform

**Real-time geopolitical intelligence powered by AI — built for analysts, researchers, and anyone who needs to stay ahead.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Discord](https://img.shields.io/badge/Discord-py--cord-5865F2?style=flat-square&logo=discord&logoColor=white)](https://pycord.dev)
[![Groq](https://img.shields.io/badge/AI-Groq%20LLaMA%203.3-F55036?style=flat-square)](https://groq.com)
[![SQLite](https://img.shields.io/badge/Database-SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-22C55E?style=flat-square)]()

[Features](#features) • [Quick Start](#quick-start) • [Commands](#commands) • [Architecture](#architecture) • [Sources](#intelligence-sources) • [Roadmap](#roadmap) • [Contributing](#contributing)

</div>

---

## What is VEGA?

VEGA is the intelligence engine powering **Astral Network** — an open-source platform for real-time geopolitical monitoring, conflict analysis, and OSINT research.

It monitors 30+ verified intelligence sources simultaneously, classifies every article by threat level and region using AI, generates military-grade SITREPs, and maintains a persistent intelligence database — all accessible through Discord.

Think of it as a lightweight, self-hosted alternative to commercial threat intelligence platforms like Palantir — completely free and open source.

---

## Features

### 🔴 Real-Time Intelligence Feed
- Monitors **30+ verified sources** across 5 categories
- AI-powered classification: `CRITICAL` `HIGH` `MEDIUM` `LOW`
- Automatic routing to regional channels
- Critical alerts with `@everyone` for maximum-priority events
- Automatic translation to English for non-English sources
- Source health tracking — knows which feeds are up or down

### 🧠 AI-Powered Analysis
- **SITREPs** — Structured situation reports based on real news
- **Intelligence Briefings** — Chronological regional summaries
- **Text Analysis** — Geopolitical analysis of any text
- **Executive Summaries** — Quick synthesis of the latest feed
- Powered by **LLaMA 3.3 70B** via Groq (free tier)

### 🔍 OSINT Tools
- Username reconnaissance across 6 major platforms
- Results automatically archived to `#osint-lab`
- Extensible — new platforms can be added in minutes

### ⚙️ System Administration
- **4 live panels** — Status, Activity Log, Error Monitor, Global Situation
- Module system — enable/disable capabilities without touching code
- Source system — manage 30+ feeds via `sources.json`
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
```
📋 INFORMATION
  #rules · #announcements · #changelog · #events

🔔 DISCORD SYSTEM
  #community-updates · #safety-notifications · #mod-log

💬 COMMUNITY
  #general · #memes

📡 GLOBAL INTEL
  #conflict-watch · #critical-alerts

🌍 REGIONAL (one per region)
  #[region]-feed · #[region]-discussion

🔍 OPERATIONS
  #command-center · #sitrep-request · #analysis-board · #osint-lab

🧠 AI LAB
  #ai-analysis · #briefing-room · #mission-logs · #evidence-vault

🛠️ DEVELOPMENT
  #dev-general · #dev-contributions · #dev-ideas

⚙️ SYSTEM (admin only)
  #vega-status · #vega-logs · #vega-errors
```

### Start VEGA
```bash
python main.py
```

---

## Commands

### Intelligence
| Command | Description | Posts to |
|---------|-------------|----------|
| `/scanfeed` | Trigger an immediate scan of all sources | Regional feeds |
| `/sitrep [topic]` | Generate a SITREP from real-time news | Response + `#mission-logs` |
| `/briefing [hours]` | Regional intelligence briefing | Response + `#briefing-room` |
| `/summary [count]` | Executive summary of the latest feed | Response + `#briefing-room` |
| `/analyze [text]` | AI geopolitical analysis of any text | Response + `#ai-analysis` |

### OSINT
| Command | Description | Posts to |
|---------|-------------|----------|
| `/userrecon [username]` | Search username across 6 platforms | Response + `#osint-lab` |

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
├── modules.json            # Module configuration
├── sources.json            # Intelligence source definitions (30+ sources)
├── .env.example            # Environment variable template
├── config/
│   └── settings.py         # All configuration, constants and AI prompts
├── cogs/                   # Bot modules
│   ├── intel.py            # News monitoring, AI classification, cycle reports
│   ├── ai_brain.py         # SITREPs, briefings, analysis
│   ├── osint.py            # Username reconnaissance
│   └── admin.py            # Live panels, system control
├── utils/
│   ├── helpers.py          # Shared utilities
│   └── database.py         # SQLite data layer
└── data/
    └── vega.db             # Persistent intelligence database
```

### Module System
```json
{
  "modules": {
    "intel": { "enabled": true }
  }
}
```

### Source System
```json
{
  "sources": [
    {
      "name": "BBC World",
      "url": "http://feeds.bbci.co.uk/news/world/rss.xml",
      "category": "conflict",
      "region": "Global",
      "enabled": true
    }
  ]
}
```

To add a new source just add an entry to `sources.json` — no code changes needed.

---

## Intelligence Sources

### Conflict & War News
BBC World, Al Jazeera, DW World, Kyiv Independent, France 24, The Guardian, Middle East Eye, Jerusalem Post, Africa News, AllAfrica, ACLED

### Military & Defense
The War Zone, Military Times, Defense News, War on the Rocks, IISS, Bellingcat

### Geopolitics & Diplomacy
Foreign Policy, Council on Foreign Relations, Brookings, South China Morning Post, Stimson Center

### Government & Official
UN News, NATO News, US State Department

### Financial & Economic Intelligence
Financial Times, Bloomberg Politics

---

## Environment Variables
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
VEGA_ERRORS_CHANNEL_ID=
AI_ANALYSIS_CHANNEL_ID=
BRIEFING_ROOM_CHANNEL_ID=
EVIDENCE_VAULT_CHANNEL_ID=

REGION_MEDIO_ORIENTE_ID=
REGION_EUROPA_ID=
REGION_AFRICA_ID=
REGION_ASIA_ID=
REGION_AMERICAS_ID=
```

---

## Roadmap

### v2.0 — Web Platform
- [ ] Web dashboard (FastAPI + React)
- [ ] REST API for third-party integrations
- [ ] Multi-server support

### v2.5 — Expanded Intelligence
- [ ] Naval module — vessel tracking via AIS
- [ ] Aviation module — aircraft tracking
- [ ] Cyber module — threat intelligence feeds
- [ ] Evidence Vault — file metadata analysis

### v3.0 — Platform
- [ ] Multiple AI model support
- [ ] Custom source configuration via Discord
- [ ] Public API with authentication
- [ ] User accounts and saved searches

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit using Conventional Commits: `feat(module): description`
4. Push and open a Pull Request

**Adding a new intelligence source:**
Add an entry to `sources.json` — no code changes needed.

**Adding a new module:**
Create `cogs/your_module.py`, add it to `modules.json`, document commands here.

---

## License

MIT License — free to use, modify and distribute.

---

<div align="center">

Built with Python, py-cord, Groq LLaMA 3.3, and open-source tools

**Astral Network — VEGA OSINT — Intelligence for everyone**

⭐ Star this repo if you find it useful

</div>

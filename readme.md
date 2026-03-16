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

It monitors 37+ verified intelligence sources simultaneously, classifies every article by threat level and region using AI, generates military-grade SITREPs, and maintains a persistent intelligence database — all accessible through Discord.

Think of it as a lightweight, self-hosted alternative to commercial threat intelligence platforms like Palantir — completely free and open source.

---

## Features

### Real-Time Intelligence Feed
- Monitors **37+ verified sources** across 5 categories and 6 regions
- AI-powered classification: `CRITICAL` `HIGH` `MEDIUM` `LOW`
- Automatic routing to regional channels including **Asia-Pacific / Oceania**
- Strict region rules prevent misclassification (Iran and Iraq always route to Middle East)
- Critical alerts with `@everyone` for maximum-priority events
- Automatic translation to English for non-English sources
- Source health tracking per scan cycle

### AI-Powered Analysis
- **SITREPs** — Structured situation reports based on real news
- **Intelligence Briefings** — Regional summaries in clean prose
- **Text Analysis** — Geopolitical analysis of any text
- **Executive Summaries** — Quick synthesis of the latest feed
- Powered by **LLaMA 3.3 70B** via Groq (free tier, 100k tokens/day)

### OSINT Tools
- Username reconnaissance across 6 major platforms
- Results automatically archived to `#osint-lab`

### System Administration
- 4 live auto-updating panels: Status, Activity Log, Error Monitor, Global Situation
- Module system — enable/disable capabilities via `modules.json`
- Source system — manage all feeds via `sources.json`, no code changes needed
- Persistent SQLite database — all intelligence survives restarts
- Hot-reload scan interval — change frequency without restarting

---

## Quick Start

### Prerequisites
- Python 3.8+
- A Discord account + Bot Token ([guide](https://discord.com/developers/applications))
- A free Groq API key ([console.groq.com](https://console.groq.com))

### Installation
```bash
git clone https://github.com/RaunaCO/vega-osint.git
cd vega-osint

python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

pip install py-cord python-dotenv aiohttp feedparser groq deep-translator langdetect

cp .env.example .env
# Edit .env with your credentials
```

### Start
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
├── modules.json            # Module on/off configuration
├── sources.json            # 37+ intelligence sources with region/category/enabled flags
├── .env                    # Secrets — never committed to git
├── .env.example            # Environment variable template
├── config/
│   └── settings.py         # Channel IDs, AI model config, keywords, prompts
├── cogs/
│   ├── intel.py            # RSS monitoring, AI classification, article routing
│   ├── ai_brain.py         # SITREPs, briefings, analysis, summaries
│   ├── osint.py            # Username reconnaissance
│   └── admin.py            # Live panels, system control commands
├── utils/
│   ├── helpers.py          # strip_html, translate, load_seen, extract_image, search_relevant_news
│   └── database.py         # SQLite — articles, sitreps, events, source_health tables
└── data/
    ├── vega.db             # Persistent intelligence database
    └── seen.json           # Fallback article deduplication (used if DB unavailable)
```

### Source System
All sources are managed in `sources.json`. No code changes needed to add, remove, or disable a source.

```json
{
  "sources": [
    {
      "name": "ABC News Australia",
      "url": "https://www.abc.net.au/news/feed/51120/rss.xml",
      "category": "conflict",
      "region": "Asia-Pacific",
      "enabled": true
    }
  ]
}
```

### Module System
Enable or disable any cog without touching code.

```json
{
  "modules": {
    "intel": { "enabled": true, "cog": "cogs.intel" }
  }
}
```

---

## Intelligence Sources

### Conflict & War News
BBC World, Al Jazeera, DW World, Kyiv Independent, France 24, The Guardian, Middle East Eye, Jerusalem Post, Africa News, AllAfrica, ACLED

### Military & Defense
The War Zone, Military Times, Defense News, War on the Rocks, IISS, Bellingcat

### Geopolitics & Diplomacy
Foreign Policy, Council on Foreign Relations, Brookings, South China Morning Post, The Diplomat, Nikkei Asia, Asia Times, Stimson Center, Lowy Institute

### Asia-Pacific & Oceania
Channel NewsAsia, ABC News Australia, RNZ World, Times of India, The Diplomat, Nikkei Asia, Asia Times, Lowy Institute

### Government & Official
UN News, NATO News, US State Department

### Financial & Economic Intelligence
Financial Times, Bloomberg Politics

---

## Region Coverage

| Region | Coverage |
|--------|----------|
| Middle East | Israel, Palestine, Iran, Iraq, Syria, Lebanon, Jordan, Yemen, Gulf states, Egypt, Turkey |
| Europe | Russia, Ukraine, NATO Europe, Balkans, Caucasus |
| Africa | Sub-Saharan Africa, North Africa, Sahel, Horn of Africa |
| Asia-Pacific | East Asia, South Asia, Southeast Asia, Oceania, Australia, New Zealand, Pacific Islands |
| Americas | North America, Central America, South America, Caribbean |
| Global | Events spanning multiple regions |

> Iran and Iraq are always classified as Middle East regardless of geographic context.

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

## Changelog

### v1.4 — March 2026
- Codebase cleanup: removed dead `NEWS_FEEDS` static dict from `settings.py`
- `search_relevant_news()` in `helpers.py` now reads `sources.json` directly — uses all 37 sources instead of 10
- Removed `exportproject.py` from the repository
- All AI prompts rewritten to output clean prose — no markdown headers, bold, or bullet points in cycle reports, alerts, or briefings

### v1.3 — March 2026
- Expanded source database from 30 to **37 sources**
- Added **Asia-Pacific / Oceania** regional coverage: ABC News Australia, RNZ World, Channel NewsAsia, The Diplomat, Nikkei Asia, Asia Times, Lowy Institute
- Renamed `Asia` region to `Asia-Pacific` across the entire system
- Strict AI classifier region rules — prevents Middle East events routing to Asia-Pacific
- Redesigned all Discord embeds: clean author line, inline fields, source-named article links, no decorative blocks

### v1.2
- SQLite persistent database
- Live panels: status, logs, errors, command center
- Source health tracking

### v1.1
- AI classification pipeline
- Regional channel routing
- Critical alerts with @everyone

### v1.0
- Initial release

---

## Roadmap

### Immediate
- [ ] `/stats` — total articles, by region, by level, total SITREPs
- [ ] Evidence Vault — file metadata analysis (images, PDFs)
- [ ] `/chat` — free AI conversation with session memory

### v2.0 — Web Platform
- [ ] FastAPI backend serving `vega.db`
- [ ] Single-page HTML dashboard
- [ ] REST API: `/api/articles`, `/api/sitreps`, `/api/stats`, `/api/sources`

### v2.5 — Expanded Intelligence
- [ ] Naval module — vessel tracking via AIS
- [ ] Aviation module — aircraft tracking
- [ ] Cyber module — CVE feeds, threat intel
- [ ] RSS.app integration for Twitter/X accounts

### v3.0 — Platform
- [ ] Multi-server support
- [ ] Multiple AI models (Gemini Flash as Groq backup)
- [ ] Public API with authentication
- [ ] User accounts and saved searches

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit using Conventional Commits: `feat(module): description`
4. Push and open a Pull Request

**Adding a new source:** edit `sources.json` — no code changes needed.

**Adding a new module:** create `cogs/your_module.py`, register it in `modules.json`.

---

## License

MIT License — free to use, modify and distribute.

---

<div align="center">

Built with Python, py-cord, Groq LLaMA 3.3, and open-source tools

**Astral Network — VEGA OSINT — Intelligence for everyone**

⭐ Star this repo if you find it useful

</div>
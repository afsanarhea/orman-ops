---
title: ORMÁN-Ops
emoji: 🔥
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: Autonomous Wildfire Emergency Operations Agent for Kazakhstan
---

# 🔥 ORMÁN-Ops: Wildfire Emergency Operations Agent

An autonomous LLM-based agent for wildfire threat assessment and emergency response planning in Kazakhstan.


## What It Does

ORMÁN-Ops is an autonomous AI agent that takes a Kazakhstan region as input and independently:

1. **Fetches** live satellite fire data from NASA FIRMS (VIIRS sensors)
2. **Checks** real-time weather conditions (Open-Meteo — wind, temperature, humidity)
3. **Assesses** regional fire risk (vegetation, historical data, seasonal factors)
4. **Analyzes** threat level with confidence scoring
5. **Plans** emergency or preventive response (adapts based on findings)
6. **Generates** a structured operational report

The agent uses **chain-of-thought reasoning** — every decision is visible. It adapts its strategy based on what it finds: if fires are detected, it plans emergency response; if not, it assesses preventive readiness.

## Architecture

```
User Input (Region)
    → Custom Agent Controller (Llama 3.3 70B via Groq LPU)
        → Tool 1: NASA FIRMS API (satellite fire data)
        → Tool 2: Open-Meteo API (weather conditions)
        → Tool 3: Regional Risk Assessment (historical/environmental)
        → Tool 4: Threat Analyzer (multi-source scoring)
        → Tool 5: Response Planner (emergency or preventive)
        → Tool 6: Report Generator (operational report)
    → Interactive Dashboard + Fire Map
```

## Tech Stack

- **LLM**: Llama 3.3 70B via Groq LPU (300+ tokens/sec)
- **Backend**: FastAPI with SSE streaming
- **Frontend**: React (CDN) + Leaflet maps + custom CSS
- **Data**: NASA FIRMS VIIRS, Open-Meteo weather API
- **Deployment**: Docker on Hugging Face Spaces

## Setup

```bash
cp .env.example .env
# Edit .env with your API keys
pip install -r requirements.txt
python main.py
```

## Category: Operations

The agent automates the wildfire threat assessment and emergency response planning workflow — a process that traditionally requires satellite analysts, meteorologists, and emergency coordinators working together.

---



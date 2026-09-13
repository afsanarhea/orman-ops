---
title: ORMÁN-Ops
**Live demo:** https://orman-ops.onrender.com

*(Free hosting — the first request after inactivity may take up to a minute to wake the service.)*
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: Autonomous Wildfire Emergency Operations Agent for Kazakhstan
---

# ORMÁN-Ops: Wildfire Emergency Operations Agent

An autonomous LLM-based agent for wildfire threat assessment and emergency response planning in Kazakhstan.

![ORMÁN-Ops dashboard](docs/images/dashboard.png)

## What It Does

ORMÁN-Ops takes a Kazakhstan region as input and independently:

1. Fetches live satellite fire data from NASA FIRMS (VIIRS sensors)
2. Checks real-time weather conditions (Open-Meteo — wind, temperature, humidity)
3. Assesses regional fire risk (vegetation, historical data, seasonal factors)
4. Analyzes threat level with confidence scoring
5. Plans emergency or preventive response, adapting to what it finds
6. Generates a structured bilingual operational report (English / Russian)

The agent uses chain-of-thought reasoning, so every decision is visible. It adapts its strategy based on findings: if fires are detected it plans emergency response; if not, it assesses preventive readiness.

A full region assessment completes in roughly 60 seconds across six tool calls.

## Coverage

Four major fire-prone forest areas (Semey Ormanı, Burabay, Bayanaul, Karkaraly) and thirteen administrative regions of Kazakhstan.

![Supported regions](docs/images/regions.png)

## Architecture

```
User Input (Region)
    → Custom Agent Controller (GPT-OSS 120B via Groq LPU)
        → Tool 1: NASA FIRMS API (satellite fire data)
        → Tool 2: Open-Meteo API (weather conditions)
        → Tool 3: Regional Risk Assessment (historical/environmental)
        → Tool 4: Threat Analyzer (multi-source scoring)
        → Tool 5: Response Planner (emergency or preventive)
        → Tool 6: Report Generator (operational report)
    → Interactive Dashboard + Fire Map
```

## Tech Stack

- **LLM:** GPT-OSS 120B via Groq LPU
- **Backend:** FastAPI with SSE streaming
- **Frontend:** React (CDN) + Leaflet maps + custom CSS
- **Data:** NASA FIRMS VIIRS, Open-Meteo weather API
- **Deployment:** Docker

## Setup

```
cp .env.example .env
pip install -r requirements.txt
python main.py
```

Then open http://localhost:7860

## Notes

The agent originally ran on Llama 3.3 70B via Groq. When that model was deprecated in 2026, the backend was migrated to GPT-OSS 120B with no changes to the agent logic or tool definitions.

Reports include wind-based fire spread direction and the responsible coordinating bodies — regional ДЧС, local akimat, and МЧС of the Republic of Kazakhstan.

## Category

Operations — the agent automates the wildfire threat assessment and emergency response planning workflow, a process that traditionally requires satellite analysts, meteorologists, and emergency coordinators working together.
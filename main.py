"""
ORMÁN-Ops FastAPI Backend
Serves the React frontend + provides SSE streaming endpoint for agent execution.
"""
import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from agent.controller import OrmanAgent
from agent.tools import KZ_REGIONS

load_dotenv()

app = FastAPI(title="ORMÁN-Ops", description="Wildfire Emergency Operations Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
FIRMS_API_KEY = os.getenv("FIRMS_API_KEY", "")


@app.get("/api/regions")
async def get_regions():
    """Return available regions with metadata."""
    regions = []
    for name, data in KZ_REGIONS.items():
        regions.append({
            "name": name,
            "lat": data["lat"],
            "lon": data["lon"],
            "area": data["area"],
            "vegetation": data.get("vegetation", ""),
            "historical_fires": data.get("historical_fires_yearly", 0),
            "fire_season": data.get("fire_season", ""),
            "description_ru": data.get("description_ru", ""),
        })
    return {"regions": regions}


@app.get("/api/run/{region}")
async def run_agent(region: str):
    """Run the agent and stream results via SSE."""
    if not GROQ_API_KEY or not FIRMS_API_KEY:
        return {"error": "API keys not configured. Set GROQ_API_KEY and FIRMS_API_KEY."}
    
    if region not in KZ_REGIONS:
        return {"error": f"Region '{region}' not found."}
    
    async def event_stream():
        agent = OrmanAgent(
            groq_api_key=GROQ_API_KEY,
            firms_api_key=FIRMS_API_KEY,
        )
        
        for step in agent.run(region):
            # Clean the step for JSON serialization
            clean_step = {}
            for k, v in step.items():
                if k == "result":
                    # Simplify large result objects
                    if isinstance(v, dict):
                        clean_step[k] = _clean_for_json(v)
                    else:
                        clean_step[k] = str(v)[:1000]
                else:
                    clean_step[k] = v
            
            data = json.dumps(clean_step, default=str, ensure_ascii=False)
            yield f"data: {data}\n\n"
        
        yield f"data: {json.dumps({'type': 'stream_end'})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "groq_configured": bool(GROQ_API_KEY),
        "firms_configured": bool(FIRMS_API_KEY),
    }


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend."""
    html_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


def _clean_for_json(obj, depth=0):
    """Recursively clean objects for JSON serialization, limiting depth."""
    if depth > 3:
        return str(obj)[:200]
    if isinstance(obj, dict):
        return {k: _clean_for_json(v, depth + 1) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_for_json(item, depth + 1) for item in obj[:30]]
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)[:200]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))

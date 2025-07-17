from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import json, os, asyncio
from datetime import datetime

app = FastAPI()

# Enable CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'news_data.json')
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "../frontend"))

class DateRange(BaseModel):
    start_date: str
    end_date: str

async def run_crawler(args=None):
    cmd = ["python3", os.path.join(BASE_DIR, "news_scraper.py")]
    if args:
        cmd.extend(args)
    proc = await asyncio.create_subprocess_exec(*cmd)
    await proc.communicate()
    if proc.returncode != 0:
        raise Exception("Crawler exited with an error")

@app.get("/incidents")
async def get_incidents(party: str = None, location: str = None, min_casualties: int = None):
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            incidents = json.load(f)
        if party:
            incidents = [i for i in incidents if i.get('party') == party]
        if location:
            incidents = [i for i in incidents if i.get('location') == location]
        if min_casualties is not None:
            incidents = [i for i in incidents if (i.get('deaths', 0) + i.get('injured', 0)) >= min_casualties]
        return {"incidents": incidents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_stats():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            incidents = json.load(f)
        return {
            "total_incidents": len(incidents),
            "total_deaths": sum(i.get('deaths', 0) for i in incidents),
            "total_injured": sum(i.get('injured', 0) for i in incidents),
            "unique_locations": len(set(i.get('location', '') for i in incidents))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl")
async def start_crawl():
    try:
        await run_crawler()
        return {"message": "Crawl completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crawl/range")
async def start_date_range_crawl(date_range: DateRange):
    try:
        await run_crawler([
            "--start", date_range.start_date,
            "--end", date_range.end_date
        ])
        return {"message": "Date range crawl completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/filters")
async def get_filters():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            incidents = json.load(f)
        parties = sorted(set(i.get('party', 'Unknown') for i in incidents))
        locations = sorted(set(i.get('location', 'Unknown') for i in incidents))
        return {
            "parties": parties,
            "locations": locations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve static files (like CSS/JS) from frontend dir
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

# Serve index.html directly for root ("/")
@app.get("/", response_class=HTMLResponse)
async def serve_root():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="index.html not found in frontend directory")

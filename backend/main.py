from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, asyncio
from datetime import datetime

app = FastAPI()

# Enable CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this for prod!
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve path to news_data.json relative to this file (main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'news_data.json')

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
        # Pass dates as CLI args to news_scraper.py, your scraper must accept these
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

# Mount frontend static files (adjust the path if needed)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

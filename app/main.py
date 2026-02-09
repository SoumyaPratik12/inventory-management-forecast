from fastapi import FastAPI
from ingest import ingest_csvs
from scheduler import setup_scheduler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Inventory Sentinel")


@app.on_event("startup")
async def startup_event():
    logger.info("Starting Inventory Sentinel...")
    setup_scheduler()
    ingest_csvs()
    logger.info("App started successfully")


@app.get("/")
async def root():
    return {"message": "Inventory Sentinel is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

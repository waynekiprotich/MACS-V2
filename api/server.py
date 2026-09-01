import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router as api_router
from models.database import init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="MACS-V2 API",
    description="Multi-Agent Trading System API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up MACS-V2 API...")
    try:
        init_db()
    except Exception as e:
        logger.error(f"Failed to initialize database during startup: {e}")

app.include_router(api_router, prefix="/api")

@app.get("/")
def root():
    return {"message": "MACS-V2 API is running."}

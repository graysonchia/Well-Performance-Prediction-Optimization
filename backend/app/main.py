from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analytics, auth, wells


app = FastAPI(
    title="Well Performance Prediction & Optimization API",
    description="FastAPI backend for oil and gas well analytics, production trends, and optimization dashboards.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(wells.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {
        "project": "Well Performance Prediction & Optimization",
        "status": "online",
        "api_prefix": API_PREFIX,
        "docs": "/docs",
    }

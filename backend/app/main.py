from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.routers import agents, health, tickets

app = FastAPI(
    title="DeskFlow API · Vansh Dobhal — Roll No. 10099",
    description=(
        "Helpdesk / support ticket management API for the Session 21 DevOps capstone.\n\n"
        "Author: **Vansh Dobhal — Roll No. 10099**"
    ),
    version="1.0.0",
    # Served under /api so the Ingress /api route covers it (ingress-nginx rejects "." in paths).
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(tickets.router)
app.include_router(agents.router)

Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, include_in_schema=False)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "deskflow-backend",
        "version": app.version,
        "environment": settings.environment,
        "author": "Vansh Dobhal — Roll No. 10099",
        "docs": "/docs",
    }

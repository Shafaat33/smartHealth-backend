import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.analytics import router as analytics_router
from app.api.appointments import router as appointments_router
from app.api.assistant import router as assistant_router
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.notifications import router as notifications_router
from app.api.patients import router as patients_router
from app.api.providers import router as providers_router
from app.api.temporal import router as temporal_router
from app.core.logging import RequestIdMiddleware
from app.core.tracing import setup_tracing

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Healthcare Management System",
    version="0.1.0",
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
setup_tracing(app)
Instrumentator(excluded_handlers=["/metrics", "/health"]).instrument(app).expose(
    app,
    endpoint="/metrics",
    include_in_schema=False,
)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(providers_router)
app.include_router(appointments_router)
app.include_router(notifications_router)
app.include_router(analytics_router)
app.include_router(knowledge_router)
app.include_router(assistant_router)
app.include_router(temporal_router)


@app.get("/health")
async def health_check():
    return {"health": "ok"}

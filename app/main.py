from fastapi import FastAPI

from app.api.appointments import router as appointments_router
from app.api.auth import router as auth_router
from app.api.patients import router as patients_router
from app.api.providers import router as providers_router
from app.api.temporal import router as temporal_router

app = FastAPI(
    title="Healthcare Management System",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(providers_router)
app.include_router(appointments_router)
app.include_router(temporal_router)


@app.get("/health")
async def health_check():
    return {"health": "ok"}

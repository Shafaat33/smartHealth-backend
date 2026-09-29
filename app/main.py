from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.patients import router as patients_router

app = FastAPI(
    title="Healthcare Management System",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(patients_router)


@app.get("/health")
async def health_check():
    return {"health": "ok"}

from fastapi import FastAPI

app = FastAPI(
    title="Healthcare Management System",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    return {"health": "ok"}
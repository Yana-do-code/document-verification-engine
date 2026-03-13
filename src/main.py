from fastapi import FastAPI
import os
from src.routes.documents import router as documents_router
from src.config.settings import settings

app = FastAPI(title="Document Verification Engine", version="1.0.0")

os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.compressed_dir, exist_ok=True)
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}

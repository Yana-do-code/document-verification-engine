from fastapi import FastAPI
from src.routes.documents import router as documents_router

app = FastAPI(title="Document Verification Engine", version="1.0.0")

app.include_router(documents_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.settings import settings
from src.database import connection as db_conn
from src.routes.documents import router as documents_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_conn.connect()
    yield
    await db_conn.disconnect()


app = FastAPI(
    title="Document Verification Engine",
    version="1.0.0",
    description="OCR-powered API for extracting and validating Indian identity documents.",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — controlled via CORS_ORIGINS env var (default "*" for development)
# ---------------------------------------------------------------------------
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handler — ensures all unhandled errors return JSON
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Unexpected server error: {exc}"},
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}

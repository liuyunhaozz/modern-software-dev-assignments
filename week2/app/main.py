from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import init_db
from .routers import action_items, notes
from .services.extract import LLMExtractionError


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run DB schema migrations on startup instead of at module import time
    # so importing the app for tests / tooling does not have side effects.
    init_db()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)


# ---------- Global exception handlers --------------------------------------


@app.exception_handler(LLMExtractionError)
async def _llm_error_handler(_: Request, exc: LLMExtractionError) -> JSONResponse:
    # Bad gateway: the upstream LLM (Ollama) failed or returned garbage.
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc)},
    )


# ---------- Static & index -------------------------------------------------


_INDEX_HTML: str | None = None


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    global _INDEX_HTML
    if _INDEX_HTML is None:
        _INDEX_HTML = (settings.frontend_dir / "index.html").read_text(encoding="utf-8")
    return _INDEX_HTML


app.include_router(notes.router)
app.include_router(action_items.router)


app.mount(
    "/static",
    StaticFiles(directory=str(settings.frontend_dir)),
    name="static",
)

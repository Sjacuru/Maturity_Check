from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from assessment.api.routes import router

_FRONTEND_DIST = Path("frontend") / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="PPP Maturity Check — Auditor Review Interface")
    app.include_router(router, prefix="/api")
    if _FRONTEND_DIST.is_dir():
        app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
    return app

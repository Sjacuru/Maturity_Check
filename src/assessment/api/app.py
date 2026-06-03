from __future__ import annotations

from fastapi import FastAPI

from assessment.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="PPP Maturity Check — Auditor Review Interface")
    app.include_router(router)
    return app

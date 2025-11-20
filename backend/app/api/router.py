"""Top-level API router that wires all sub-routers together."""

from fastapi import APIRouter

from backend.api.routes import router as legacy_router

api_router = APIRouter()
api_router.include_router(legacy_router)

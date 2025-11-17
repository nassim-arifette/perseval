"""FastAPI application entry point."""

from fastapi import FastAPI

from backend.api.routes import router
from backend.config import API_TITLE

app = FastAPI(title=API_TITLE)
app.include_router(router)


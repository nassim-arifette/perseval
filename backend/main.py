"""FastAPI application entry point."""

from fastapi import FastAPI

from api.routes import router
from config import API_TITLE

app = FastAPI(title=API_TITLE)
app.include_router(router)


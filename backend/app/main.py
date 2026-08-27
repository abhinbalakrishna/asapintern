from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .config import settings
from .database import Base, engine
from .routers import attention, auth, sessions

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Focus Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(attention.router)


@app.get("/health")
def health():
    return {"status": "ok"}

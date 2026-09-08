from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, devices, images, analytics

# Dev convenience: auto-create tables. In production, use Alembic migrations instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PaiMonitor Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(devices.router)
app.include_router(images.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}

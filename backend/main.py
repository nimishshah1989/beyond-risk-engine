"""Beyond Risk Engine — FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.models.database import init_db
from app.core.seed import seed_database
from app.api.questions import router as questions_router
from app.api.investors import router as investors_router
from app.api.products import router as products_router
from app.api.context import router as context_router
from app.api.games import router as games_router
from app.api.documents import router as documents_router

app = FastAPI(
    title="Beyond · Adaptive Behavioral Risk Engine",
    description="IRT-based investor risk profiling with AI instrument analysis",
    version="2.0.0",
)

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(questions_router)
app.include_router(investors_router)
app.include_router(products_router)
app.include_router(context_router)
app.include_router(games_router)
app.include_router(documents_router)


@app.on_event("startup")
def startup():
    init_db()
    seed_database()


@app.get("/")
def root():
    return {"app": "Beyond Risk Engine", "version": "2.0.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

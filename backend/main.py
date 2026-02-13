"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings

# Validate configuration on startup
settings.validate_secret()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup: Initialize database tables (if DATABASE_URL is configured).
    Shutdown: Close database connections.
    """
    # Startup
    if settings.database_url:
        from backend.database import init_db, close_db
        # Import models to register them with SQLModel metadata
        from backend.models import database as _  # noqa: F401
        await init_db()

    yield

    # Shutdown
    if settings.database_url:
        from backend.database import close_db
        await close_db()


# Create FastAPI application
app = FastAPI(
    title="Todo Application API",
    description="JWT-authenticated Todo API with user isolation",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint for health checks."""
    return {"status": "ok", "message": "Todo API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and register routers after app is created
from backend.routes import auth, tasks, chat

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(chat.router)

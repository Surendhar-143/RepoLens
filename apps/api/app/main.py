from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging, LoggingMiddleware
from app.core.exceptions import register_exception_handlers
from app.core.redis import close_redis
from app.core.qdrant import close_qdrant
from app.api.routes import health, auth, github, repositories, jobs, analysis, files, symbols, graph, search, ai, workspace, documentation, quality, enterprise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    setup_logging(env=settings.ENV)
    yield
    # Shutdown actions
    await close_redis()
    await close_qdrant()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom request/response structured logging middleware
app.add_middleware(LoggingMiddleware)

# Exception handlers config
register_exception_handlers(app)

# Include root level checks
app.include_router(health.router, tags=["System"])

# Include versioned API route endpoints
app.include_router(health.router, prefix="/api/v1", tags=["System"])
app.include_router(auth.router, prefix="/api/v1")
app.include_router(github.router, prefix="/api/v1")
app.include_router(repositories.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(symbols.router, prefix="/api/v1")
app.include_router(graph.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(workspace.router, prefix="/api/v1")
app.include_router(documentation.router, prefix="/api/v1")
app.include_router(quality.router, prefix="/api/v1")
app.include_router(enterprise.router, prefix="/api/v1")

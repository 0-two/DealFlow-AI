"""
FastAPI Main Application Entry Point
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from app.config.settings import settings
from app.api.routes import query, investors, trends, ingest, pitch_deck, investor_thesis

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for CPU-bound operations (LLM calls, document parsing)
thread_pool = ThreadPoolExecutor(max_workers=4)

async def run_in_thread(func, *args, **kwargs):
    """Run a synchronous function in the thread pool to avoid blocking the event loop"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, lambda: func(*args, **kwargs))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown"""
    # Startup
    logger.info("Starting up application...")
    logger.info(f"Thread pool initialized with {thread_pool._max_workers} workers")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    thread_pool.shutdown(wait=True)
    logger.info("Thread pool shutdown complete")

app = FastAPI(
    title="Bidirectional Funding Intelligence API",
    description="AI-powered matching platform for founders and investors",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timeout and concurrency limiting
import asyncio
from asyncio import Semaphore

# Limit concurrent heavy operations (LLM calls, document parsing)
MAX_CONCURRENT_HEAVY_OPS = 3
heavy_ops_semaphore = Semaphore(MAX_CONCURRENT_HEAVY_OPS)

async def with_timeout(coro, timeout_seconds: int = 120):
    """Wrap a coroutine with a timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timed out")

async def acquire_heavy_op():
    """Acquire semaphore for heavy operations"""
    acquired = await asyncio.wait_for(heavy_ops_semaphore.acquire(), timeout=30)
    if not acquired:
        raise HTTPException(status_code=503, detail="Server busy, please try again")
    return True

def release_heavy_op():
    """Release semaphore for heavy operations"""
    heavy_ops_semaphore.release()


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests"""
    start_time = time.time()
    
    # Log request details
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    try:
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.4f}s"
        )
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            f"Error in {request.method} {request.url.path} - "
            f"Error: {str(e)} - Time: {process_time:.4f}s"
        )
        raise


# Error Handling Middleware
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail} - "
        f"Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        f"Unhandled Exception: {str(exc)} - Path: {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
            "status_code": 500,
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


# Include routers
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(investors.router, prefix="/api/investors", tags=["Investors"])
app.include_router(trends.router, prefix="/api/trends", tags=["Trends"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["Ingest"])
app.include_router(pitch_deck.router, prefix="/api/pitch-deck", tags=["Pitch Deck"])
app.include_router(investor_thesis.router, prefix="/api/investor-thesis", tags=["Investor Thesis"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Bidirectional Funding Intelligence API",
        "status": "running",
        "version": "2.0.0",
        "features": ["Founder matching", "Investor matching", "Multilingual support"]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    
    # Calculate optimal workers (2-4 per CPU core for I/O bound apps)
    workers = min(multiprocessing.cpu_count() * 2, 4)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else workers,  # Single worker in debug mode for hot reload
        timeout_keep_alive=30,
        limit_concurrency=100,  # Max concurrent connections
        limit_max_requests=1000,  # Restart worker after N requests to prevent memory leaks
    )

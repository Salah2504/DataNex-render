from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from api.routes import router, limiter
from core.logger import logger

import os

#-------------------------------------------------------

app = FastAPI()

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.include_router(router)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

port = int(os.environ.get("PORT", 10000))

#-------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}

#-------------------------------------------------------

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "🚫 Too many requests"}
    )

#-------------------------------------------------------

@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):

    logger.error(f"Unhandled Error: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error"}
    )

#-------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=port)
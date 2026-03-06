"""
News Service - Главное приложение
"""
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db
from app.api.routes import router as api_router
from app.middleware import RequestTracingMiddleware, ErrorHandlingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске"""
    # Создаём директории
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.IMAGES_FOLDER, exist_ok=True)
    
    # Инициализируем БД
    await init_db()
    
    logger.info("News Service запущен")
    
    yield
    
    logger.info("News Service остановлен")


app = FastAPI(
    title="News Service",
    description="Сервис автосбора и адаптации новостей для Telegram",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestTracingMiddleware)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# API Router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root(request: Request):
    """Главная страница - админ панель"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Проверка здоровья с проверкой БД"""
    from sqlalchemy import text
    from app.database import engine
    
    health_status = {"status": "ok", "version": "1.0.0", "checks": {}}
    
    # Check database
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    status_code = 200 if health_status["status"] == "ok" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@app.get("/favicon.ico")
async def favicon():
    """Favicon"""
    from fastapi.responses import Response
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=True
    )

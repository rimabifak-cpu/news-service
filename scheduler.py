"""
Планировщик для автоматического парсинга источников
"""
import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from loguru import logger
import os
import sys

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import async_session_maker
from app.models.db_models import Source
from app.services.news_processor import news_processor
from app.config import settings


async def parse_all_sources():
    """Парсинг всех активных источников"""
    logger.info("Запуск парсинга источников...")
    
    async with async_session_maker() as session:
        result = await session.execute(
            select(Source).where(Source.is_active == True)
        )
        sources = result.scalars().all()
    
    total_processed = 0
    for source in sources:
        try:
            count = await news_processor.process_source(source.id)
            total_processed += count
            logger.info(f"Источник {source.name}: обработано {count} постов")
        except Exception as e:
            logger.error(f"Ошибка парсинга источника {source.name}: {e}")
    
    logger.info(f"Парсинг завершён. Всего обработано: {total_processed} постов")


def run_scheduler():
    """Запуск планировщика"""
    scheduler = AsyncIOScheduler()
    
    interval = int(os.getenv("PARSER_INTERVAL", settings.PARSER_INTERVAL))
    
    scheduler.add_job(
        parse_all_sources,
        trigger=IntervalTrigger(seconds=interval),
        id="parse_sources",
        name="Парсинг источников",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Планировщик запущен. Интервал: {interval} секунд")
    
    # Держим процесс запущенным
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Планировщик остановлен")


if __name__ == "__main__":
    run_scheduler()

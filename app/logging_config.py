"""
Конфигурация логирования
"""
import sys
from loguru import logger
from datetime import datetime
import json


# Формат JSON для структурированного логирования
class JSONFormatter:
    """Форматтер для JSON логов"""
    
    def __init__(self, include_extra=True):
        self.include_extra = include_extra
    
    def format(self, record):
        log_data = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
            "message": record["message"],
        }
        
        # Добавляем дополнительные поля
        if self.include_extra and record.get("extra"):
            for key, value in record["extra"].items():
                log_data[key] = value
        
        # Добавляем exception если есть
        if record.get("exception"):
            log_data["exception"] = record["exception"]
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(log_level: str = "INFO", log_format: str = "text"):
    """
    Настройка логирования
    
    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_format: Формат логов ("text" или "json")
    """
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Консольный вывод
    if log_format == "json":
        console_format = JSONFormatter(include_extra=True)
    else:
        # Текстовый формат с деталями
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level> | "
            "{extra}"
        )
    
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # Файловый лог
    logger.add(
        "logs/app_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level=log_level,
        format=console_format if log_format == "text" else JSONFormatter(include_extra=True),
        backtrace=True,
        diagnose=True,
    )
    
    # Лог ошибок (отдельный файл)
    logger.add(
        "logs/error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        level="ERROR",
        format=console_format if log_format == "text" else JSONFormatter(include_extra=True),
        backtrace=True,
        diagnose=True,
    )
    
    logger.info("Logging initialized", extra={"log_level": log_level, "log_format": log_format})


# Инициализация логирования по умолчанию
setup_logging(log_level="INFO", log_format="text")

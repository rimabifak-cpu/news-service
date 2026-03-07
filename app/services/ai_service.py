"""
Сервис для адаптации текста с помощью AI
"""
import httpx
from typing import Optional
from loguru import logger
import time

from app.config import settings


class AIService:
    """Сервис для работы с AI"""

    def __init__(self):
        self.api_key = settings.AI_API_KEY
        self.api_url = settings.AI_API_URL
        self.model = settings.AI_MODEL
        self.request_count = 0
        self.error_count = 0
    
    async def adapt_text(
        self,
        original_text: str,
        prompt: Optional[str] = None,
        max_length: int = 2000
    ) -> str:
        """
        Адаптация текста под стиль Telegram-канала

        Args:
            original_text: Исходный текст
            prompt: Пользовательский промт (опционально)
            max_length: Максимальная длина результата

        Returns:
            Адаптированный текст
        """
        start_time = time.time()
        self.request_count += 1
        
        if not self.api_key:
            logger.warning("⚠️ AI API key не настроен, возвращаем исходный текст")
            return original_text
        
        if not original_text or len(original_text.strip()) == 0:
            logger.warning("⚠️ Пустой текст для адаптации, возвращаем пустую строку")
            return original_text

        default_prompt = """
Адаптируй этот текст для публикации в Telegram-канале:
- Сделай текст более живым и engaging
- Добавь эмодзи где уместно (но не переусердствуй)
- Разбей на короткие абзацы для удобства чтения
- Выдели жирным ключевые моменты
- Сохрани основной смысл и факты
- Длина до 2000 символов

⚠️ ВАЖНО:
- НЕ выдумывай новые факты, цитаты или детали
- НЕ добавляй информацию, которой нет в исходном тексте
- ТОЧНО передавай факты из оригинала
- Если в оригинале есть сомнения — сохраняй их
"""

        system_prompt = prompt or default_prompt
        
        logger.debug(
            "AI_ADAPT_START",
            extra={
                "text_length": len(original_text),
                "prompt_type": "custom" if prompt else "default",
                "model": self.model,
            }
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Ты профессиональный редактор Telegram-канала."},
                            {"role": "user", "content": f"{system_prompt}\n\nИсходный текст:\n{original_text[:5000]}"}
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    adapted = data["choices"][0]["message"]["content"]
                    duration = time.time() - start_time
                    
                    logger.info(
                        "AI_ADAPT_SUCCESS",
                        extra={
                            "input_length": len(original_text),
                            "output_length": len(adapted),
                            "duration_ms": round(duration * 1000, 2),
                            "model": self.model,
                        }
                    )
                    return adapted.strip()
                else:
                    self.error_count += 1
                    logger.error(
                        "AI_API_ERROR",
                        extra={
                            "status_code": response.status_code,
                            "response_body": response.text[:500],
                            "api_url": self.api_url,
                            "total_requests": self.request_count,
                            "total_errors": self.error_count,
                        }
                    )
                    return original_text

        except httpx.TimeoutException as e:
            self.error_count += 1
            logger.error(
                "AI_TIMEOUT",
                extra={
                    "timeout_seconds": 60,
                    "model": self.model,
                    "error": str(e),
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                }
            )
            return original_text
        except httpx.RequestError as e:
            self.error_count += 1
            logger.error(
                "AI_REQUEST_ERROR",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "api_url": self.api_url,
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                }
            )
            return original_text
        except Exception as e:
            self.error_count += 1
            logger.error(
                "AI_UNEXPECTED_ERROR",
                extra={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                },
                exc_info=True
            )
            return original_text
    
    async def generate_title(
        self,
        content: str,
        max_length: int = 100
    ) -> str:
        """
        Генерация цепляющего заголовка
        
        Args:
            content: Содержание поста
            max_length: Максимальная длина заголовка
        
        Returns:
            Заголовок
        """
        if not self.api_key:
            # Возвращаем первую строку контента
            return content.split('\n')[0][:max_length]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "Ты создаёшь цепляющие заголовки для Telegram. Максимум {max_length} символов."},
                            {"role": "user", "content": f"Создай цепляющий заголовок до {max_length} символов для этого текста:\n\n{content[:1000]}"}
                        ],
                        "max_tokens": 100,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    title = data["choices"][0]["message"]["content"]
                    return title.strip()[:max_length]
                else:
                    return content.split('\n')[0][:max_length]
                    
        except Exception as e:
            logger.error(f"Ошибка генерации заголовка: {e}")
            return content.split('\n')[0][:max_length]


# Singleton
ai_service = AIService()

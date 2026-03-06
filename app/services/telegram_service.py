"""
Сервис для публикации в Telegram
"""
import os
from typing import Optional
from loguru import logger

from app.config import settings


class TelegramService:
    """Сервис для работы с Telegram"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.channel_id = settings.TELEGRAM_CHANNEL_ID
    
    async def publish_post(
        self,
        text: str,
        image_path: Optional[str] = None,
        channel_id: Optional[str] = None
    ) -> Optional[int]:
        """
        Публикация поста в Telegram канале

        Args:
            text: Текст поста
            image_path: Путь к изображению (опционально)
            channel_id: ID канала (опционально)

        Returns:
            message_id опубликованного сообщения или None
        """
        if not self.bot_token:
            logger.error("Telegram bot token не настроен")
            return None

        channel_id = channel_id or self.channel_id
        if not channel_id:
            logger.error("Telegram channel ID не настроен")
            return None

        import httpx

        api_url = f"https://api.telegram.org/bot{self.bot_token}"

        try:
            # Проверяем изображение
            image_exists = image_path and os.path.exists(image_path)
            logger.info(f"Публикация: image_path={image_path}, exists={image_exists}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if image_exists:
                    # Отправляем с фото
                    logger.info(f"Отправка фото: {image_path}")
                    with open(image_path, 'rb') as photo:
                        files = {'photo': photo}
                        data = {
                            'chat_id': channel_id,
                            'caption': text,
                            'parse_mode': 'HTML'
                        }
                        logger.info(f"Отправка в канал: {channel_id}")
                        response = await client.post(
                            f"{api_url}/sendPhoto",
                            files=files,
                            data=data
                        )
                else:
                    # Отправляем только текст
                    logger.info(f"Отправка текста в канал: {channel_id}")
                    data = {
                        'chat_id': channel_id,
                        'text': text,
                        'parse_mode': 'HTML'
                    }
                    response = await client.post(
                        f"{api_url}/sendMessage",
                        json=data
                    )

                logger.info(f"Telegram response status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result['result']['message_id']
                    logger.info(f"Пост опубликован в {channel_id}, message_id: {message_id}")
                    return message_id
                else:
                    logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Ошибка публикации в Telegram: {e}", exc_info=True)
            return None
    
    async def edit_post(
        self,
        message_id: int,
        text: str,
        channel_id: Optional[str] = None
    ) -> bool:
        """
        Редактирование поста
        
        Args:
            message_id: ID сообщения для редактирования
            text: Новый текст
            channel_id: ID канала
        
        Returns:
            True если успешно
        """
        if not self.bot_token:
            return False
        
        channel_id = channel_id or self.channel_id
        
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/editMessageCaption",
                    json={
                        'chat_id': channel_id,
                        'message_id': message_id,
                        'caption': text,
                        'parse_mode': 'HTML'
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Ошибка редактирования поста: {e}")
            return False
    
    async def delete_post(
        self,
        message_id: int,
        channel_id: Optional[str] = None
    ) -> bool:
        """
        Удаление поста
        
        Args:
            message_id: ID сообщения для удаления
            channel_id: ID канала
        
        Returns:
            True если успешно
        """
        if not self.bot_token:
            return False
        
        channel_id = channel_id or self.channel_id
        
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{self.bot_token}/deleteMessage",
                    json={
                        'chat_id': channel_id,
                        'message_id': message_id
                    }
                )
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Ошибка удаления поста: {e}")
            return False


# Singleton
telegram_service = TelegramService()

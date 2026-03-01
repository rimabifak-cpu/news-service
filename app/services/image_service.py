"""
Сервис для обработки изображений (наложение логотипа)
"""
import os
from PIL import Image, ImageEnhance
from typing import Optional, Tuple
from loguru import logger

from app.config import settings


class ImageService:
    """Сервис для обработки изображений"""
    
    def __init__(self):
        self.logo_path = settings.LOGO_PATH
        self.position = settings.LOGO_POSITION
        self.opacity = settings.LOGO_OPACITY
    
    async def add_logo(
        self,
        image_path: str,
        output_path: str,
        logo_path: Optional[str] = None,
        position: Optional[str] = None,
        opacity: Optional[float] = None
    ) -> Optional[str]:
        """
        Наложение логотипа на изображение
        
        Args:
            image_path: Путь к исходному изображению
            output_path: Путь для сохранения результата
            logo_path: Путь к логотипу (опционально)
            position: Позиция логотипа (опционально)
            opacity: Прозрачность логотипа (опционально)
        
        Returns:
            Путь к обработанному изображению или None
        """
        logo_path = logo_path or self.logo_path
        position = position or self.position
        opacity = opacity or self.opacity
        
        try:
            # Проверяем существование файлов
            if not os.path.exists(image_path):
                logger.error(f"Изображение не найдено: {image_path}")
                return None
            
            if not os.path.exists(logo_path):
                logger.warning(f"Логотип не найден: {logo_path}, сохраняем без логотипа")
                # Просто копируем исходное изображение
                with Image.open(image_path) as img:
                    img.save(output_path)
                return output_path
            
            # Открываем изображения
            with Image.open(image_path) as base_img:
                # Конвертируем в RGB если нужно
                if base_img.mode in ('RGBA', 'P'):
                    base_img = base_img.convert('RGB')
                
                with Image.open(logo_path) as logo:
                    # Обеспечиваем RGBA для логотипа
                    if logo.mode != 'RGBA':
                        logo = logo.convert('RGBA')
                    
                    # Применяем прозрачность
                    if opacity < 1.0:
                        alpha = logo.split()[3]
                        alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                        logo.putalpha(alpha)
                    
                    # Вычисляем размер логотипа (максимум 20% от ширины изображения)
                    base_width, base_height = base_img.size
                    logo_max_width = int(base_width * 0.2)
                    
                    # Сохраняем пропорции логотипа
                    logo_ratio = logo.height / logo.width
                    new_logo_width = min(logo.width, logo_max_width)
                    new_logo_height = int(new_logo_width * logo_ratio)
                    
                    logo = logo.resize((new_logo_width, new_logo_height), Image.Resampling.LANCZOS)
                    
                    # Вычисляем позицию
                    x, y = self._calculate_position(base_img.size, logo.size, position)
                    
                    # Создаём копию для редактирования
                    result = base_img.copy()
                    
                    # Накладываем логотип
                    result.paste(logo, (x, y), logo)
                    
                    # Сохраняем
                    result.save(output_path, quality=95)
                    
                    logger.info(f"Логотип добавлен: {output_path}")
                    return output_path
                    
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {e}")
            # При ошибке копируем исходное
            try:
                with Image.open(image_path) as img:
                    img.save(output_path)
                return output_path
            except:
                return None
    
    def _calculate_position(
        self,
        base_size: Tuple[int, int],
        logo_size: Tuple[int, int],
        position: str
    ) -> Tuple[int, int]:
        """Вычисление координат позиции логотипа"""
        base_w, base_h = base_size
        logo_w, logo_h = logo_size
        
        margin = 10  # Отступ в пикселях
        
        positions = {
            'top-left': (margin, margin),
            'top-right': (base_w - logo_w - margin, margin),
            'bottom-left': (margin, base_h - logo_h - margin),
            'bottom-right': (base_w - logo_w - margin, base_h - logo_h - margin),
        }
        
        return positions.get(position, positions['bottom-right'])
    
    async def download_image(
        self,
        url: str,
        save_path: str
    ) -> Optional[str]:
        """
        Скачивание изображения по URL
        
        Args:
            url: URL изображения
            save_path: Путь для сохранения
        
        Returns:
            Путь к сохранённому файлу или None
        """
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Изображение скачано: {save_path}")
                return save_path
                
        except Exception as e:
            logger.error(f"Ошибка скачивания изображения: {e}")
            return None


# Singleton
image_service = ImageService()

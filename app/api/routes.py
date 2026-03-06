"""
API эндпоинты для управления источниками и постами
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
from datetime import datetime

from app.database import get_db
from app.models.db_models import Source, Post, PostStatus, SourceType
from app.services.news_processor import news_processor
from app.services.telegram_service import telegram_service
from app.config import settings

router = APIRouter()


# === Pydantic модели ===

class SourceCreate(BaseModel):
    name: str
    url: str
    source_type: str = "website"
    selector_title: Optional[str] = None
    selector_content: Optional[str] = None
    selector_image: Optional[str] = None
    selector_date: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_enabled: bool = True


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    is_active: Optional[bool] = None
    selector_title: Optional[str] = None
    selector_content: Optional[str] = None
    selector_image: Optional[str] = None
    selector_date: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_enabled: Optional[bool] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    source_type: str
    is_active: bool
    last_parsed: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    source_id: int
    original_title: str
    adapted_title: Optional[str]
    adapted_content: Optional[str]
    status: str
    processed_image_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# === Источники ===

@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Получить список источников"""
    result = await db.execute(
        select(Source)
        .offset(skip)
        .limit(limit)
        .order_by(Source.created_at.desc())
    )
    return result.scalars().all()


@router.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый источник"""
    source = Source(
        name=source_data.name,
        url=source_data.url,
        source_type=source_data.source_type,
        selector_title=source_data.selector_title,
        selector_content=source_data.selector_content,
        selector_image=source_data.selector_image,
        selector_date=source_data.selector_date,
        ai_prompt=source_data.ai_prompt,
        ai_enabled=source_data.ai_enabled,
    )
    
    db.add(source)
    await db.commit()
    await db.refresh(source)
    
    return source


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить источник по ID"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    
    return source


@router.put("/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: int,
    source_data: SourceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить источник"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    
    update_data = source_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)
    
    await db.commit()
    await db.refresh(source)
    
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить источник"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    
    await db.delete(source)
    await db.commit()
    
    return None


@router.post("/sources/{source_id}/parse", response_model=dict)
async def parse_source(
    source_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Запустить парсинг источника"""
    result = await db.execute(select(Source).where(Source.id == source_id))
    source = result.scalar_one_or_none()
    
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    
    count = await news_processor.process_source(source_id)
    
    return {"message": f"Обработано {count} постов"}


@router.post("/parse-all")
async def parse_all_sources():
    """Принудительный парсинг всех источников"""
    from app.database import async_session_maker
    from sqlalchemy import select
    from app.models.db_models import Source
    
    async with async_session_maker() as session:
        try:
            result = await session.execute(select(Source).where(Source.is_active == True))
            sources = result.scalars().all()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка получения источников: {str(e)}")
    
    total_count = 0
    for source in sources:
        try:
            count = await news_processor.process_source(source.id)
            total_count += count
        except Exception as e:
            logger.error(f"Ошибка при парсинге источника {source.name}: {e}")
    
    return {"message": f"Обработано {total_count} постов из {len(sources)} источников"}


# === Посты ===

@router.get("/posts", response_model=List[PostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список постов"""
    query = select(Post).order_by(Post.created_at.desc())
    
    if status_filter:
        query = query.where(Post.status == status_filter)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить пост по ID"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    return post


@router.post("/posts/{post_id}/publish", response_model=dict)
async def publish_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Опубликовать пост в Telegram"""
    logger.info(f"Начало публикации поста {post_id}")
    
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        logger.error(f"Пост {post_id} не найден")
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    if post.status != PostStatus.READY.value:
        logger.warning(f"Пост {post_id} не готов к публикации, статус: {post.status}")
        raise HTTPException(status_code=400, detail="Пост не готов к публикации")
    
    # Формируем текст поста
    title = post.adapted_title or post.original_title or "Без заголовка"
    content = post.adapted_content or post.original_content or ""
    original_url = post.original_url or ""
    
    text = f"<b>{title}</b>\n\n{content}\n\n<a href='{original_url}'>Источник</a>"
    
    # Проверяем настройки Telegram
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token не настроен")
        raise HTTPException(status_code=500, detail="Telegram бот не настроен")
    
    if not settings.TELEGRAM_CHANNEL_ID:
        logger.error("Telegram channel ID не настроен")
        raise HTTPException(status_code=500, detail="Telegram канал не настроен")
    
    # Проверяем путь к изображению
    image_path = post.processed_image_path
    if image_path and not os.path.exists(image_path):
        logger.warning(f"Изображение не найдено: {image_path}, публикуем без него")
        image_path = None
    
    # Публикуем
    try:
        message_id = await telegram_service.publish_post(
            text=text,
            image_path=image_path
        )
    except Exception as e:
        logger.error(f"Исключение при публикации: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка публикации: {str(e)}")
    
    if message_id:
        post.status = PostStatus.PUBLISHED.value
        post.telegram_message_id = message_id
        post.published_at = datetime.utcnow()
        await db.commit()
        
        logger.info(f"Пост {post_id} успешно опубликован, message_id: {message_id}")
        return {"message": "Пост опубликован", "telegram_message_id": message_id}
    else:
        logger.error(f"Не удалось опубликовать пост {post_id}")
        raise HTTPException(status_code=500, detail="Ошибка публикации в Telegram")


@router.post("/posts/{post_id}/reject", response_model=dict)
async def reject_post(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Отклонить пост"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    post.status = PostStatus.REJECTED.value
    await db.commit()
    
    return {"message": "Пост отклонён"}


@router.get("/stats", response_model=dict)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Получить статистику"""
    # Количество источников
    sources_result = await db.execute(select(func.count(Source.id)))
    sources_count = sources_result.scalar()
    
    # Количество постов по статусам
    posts_by_status = {}
    for status_val in PostStatus:
        result = await db.execute(
            select(func.count(Post.id)).where(Post.status == status_val.value)
        )
        posts_by_status[status_val.value] = result.scalar()
    
    return {
        "sources_count": sources_count,
        "posts_by_status": posts_by_status
    }


@router.get("/settings", response_model=dict)
async def get_settings():
    """Получить текущие настройки"""
    from app.config import settings
    
    return {
        "ai_api_key": settings.AI_API_KEY[:20] + "..." if settings.AI_API_KEY else "",
        "ai_api_url": settings.AI_API_URL,
        "ai_model": settings.AI_MODEL,
        "telegram_bot_token": settings.TELEGRAM_BOT_TOKEN[:20] + "..." if settings.TELEGRAM_BOT_TOKEN else "",
        "telegram_channel_id": settings.TELEGRAM_CHANNEL_ID,
        "logo_path": settings.LOGO_PATH,
        "logo_position": settings.LOGO_POSITION,
        "logo_opacity": settings.LOGO_OPACITY,
        "parser_interval": settings.PARSER_INTERVAL,
    }

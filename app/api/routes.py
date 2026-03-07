"""
API эндпоинты для управления источниками и постами
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger
from datetime import datetime, timezone, timedelta

from app.database import get_db
from app.models.db_models import Source, Post, PostStatus, SourceType, Channel
from app.services.news_processor import news_processor
from app.services.telegram_service import telegram_service
from app.config import settings

router = APIRouter()


# === Pydantic модели ===

class SourceCreate(BaseModel):
    name: str
    url: str
    source_type: str = "website"
    channel_id: int  # Обязательный канал
    selector_title: Optional[str] = None
    selector_content: Optional[str] = None
    selector_image: Optional[str] = None
    selector_date: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_enabled: bool = True
    auto_publish: bool = False


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    channel_id: Optional[int] = None
    is_active: Optional[bool] = None
    selector_title: Optional[str] = None
    selector_content: Optional[str] = None
    selector_image: Optional[str] = None
    selector_date: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_enabled: Optional[bool] = None
    auto_publish: Optional[bool] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    url: str
    source_type: str
    channel_id: int
    is_active: bool
    auto_publish: bool
    ai_enabled: bool
    ai_prompt: Optional[str]
    last_parsed: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    source_id: int
    channel_id: Optional[int]
    original_title: str
    adapted_title: Optional[str]
    adapted_content: Optional[str]
    status: str
    is_advertisement: bool
    processed_image_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# === Каналы ===

class ChannelCreate(BaseModel):
    name: str
    bot_token: str
    channel_id: str
    ai_prompt: Optional[str] = None
    logo_path: Optional[str] = None
    logo_position: str = "bottom-right"
    logo_opacity: float = 0.7


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    bot_token: Optional[str] = None
    channel_id: Optional[str] = None
    ai_prompt: Optional[str] = None
    logo_path: Optional[str] = None
    logo_position: Optional[str] = None
    logo_opacity: Optional[float] = None
    is_active: Optional[bool] = None


class ChannelResponse(BaseModel):
    id: int
    name: str
    channel_id: str
    bot_token: str  # masked in response
    ai_prompt: Optional[str]
    logo_path: Optional[str]
    logo_position: str
    logo_opacity: float
    is_active: bool
    sources_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# === Источники ===

@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(
    skip: int = 0,
    limit: int = 50,
    channel_id: Optional[int] = None,  # Фильтр по каналу
    db: AsyncSession = Depends(get_db)
):
    """Получить список источников"""
    query = select(Source).order_by(Source.created_at.desc())
    
    if channel_id:
        query = query.where(Source.channel_id == channel_id)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    source_data: SourceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый источник"""
    # Проверяем существование канала
    channel_result = await db.execute(select(Channel).where(Channel.id == source_data.channel_id))
    channel = channel_result.scalar_one_or_none()
    
    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")
    
    source = Source(
        name=source_data.name,
        url=source_data.url,
        source_type=source_data.source_type,
        channel_id=source_data.channel_id,
        selector_title=source_data.selector_title,
        selector_content=source_data.selector_content,
        selector_image=source_data.selector_image,
        selector_date=source_data.selector_date,
        ai_prompt=source_data.ai_prompt,
        ai_enabled=source_data.ai_enabled,
        auto_publish=source_data.auto_publish,
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
    try:
        result = await db.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()

        if not source:
            raise HTTPException(status_code=404, detail="Источник не найден")

        logger.info(f"Запуск парсинга источника {source_id}: {source.name} ({source.url})")
        
        count = await news_processor.process_source(source_id)
        
        logger.info(f"Парсинг завершён: обработано {count} постов")

        return {"message": f"Обработано {count} постов"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при парсинге источника {source_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка парсинга: {str(e)}"
        )


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
    channel_id: Optional[int] = None,  # Фильтр по каналу
    is_advertisement: Optional[bool] = None,  # Фильтр реклама/не реклама
    db: AsyncSession = Depends(get_db)
):
    """Получить список постов"""
    query = select(Post).order_by(Post.created_at.desc())

    if status_filter:
        query = query.where(Post.status == status_filter)
    
    if channel_id:
        query = query.where(Post.channel_id == channel_id)
    
    if is_advertisement is not None:
        query = query.where(Post.is_advertisement == is_advertisement)

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

    result = await db.execute(
        select(Post)
        .where(Post.id == post_id)
        .options(joinedload(Post.channel))
    )
    post = result.unique().scalar_one_or_none()

    if not post:
        logger.error(f"Пост {post_id} не найден")
        raise HTTPException(status_code=404, detail="Пост не найден")

    if post.status != PostStatus.READY.value:
        logger.warning(f"Пост {post_id} не готов к публикации, статус: {post.status}")
        raise HTTPException(status_code=400, detail="Пост не готов к публикации")

    # Получаем канал из поста или источника
    channel = post.channel
    if not channel:
        # Если канал не указан в посте, получаем из источника
        source_result = await db.execute(
            select(Source)
            .where(Source.id == post.source_id)
            .options(joinedload(Source.channel))
        )
        source = source_result.unique().scalar_one_or_none()
        if source and source.channel:
            channel = source.channel

    if not channel:
        logger.error("Канал не найден для поста")
        raise HTTPException(status_code=500, detail="Канал не найден")

    # Формируем текст поста
    title = post.adapted_title or post.original_title or "Без заголовка"
    content = post.adapted_content or post.original_content or ""
    original_url = post.original_url or ""

    text = f"<b>{title}</b>\n\n{content}\n\n<a href='{original_url}'>Источник</a>"
    logger.info(f"Текст поста: {text[:200]}...")

    # Проверяем путь к изображению
    image_path = post.processed_image_path
    if image_path:
        logger.info(f"Проверка изображения: {image_path}")
        if not os.path.exists(image_path):
            logger.warning(f"Изображение не найдено: {image_path}, публикуем без него")
            image_path = None
        else:
            logger.info(f"Изображение найдено: {image_path}")
    else:
        logger.info("Изображение отсутствует, публикуем без него")

    # Публикуем
    try:
        logger.info(f"Вызов telegram_service.publish_post для канала {channel.name}")
        message_id = await telegram_service.publish_post(
            text=text,
            image_path=image_path,
            bot_token=channel.bot_token,
            channel_id=channel.channel_id
        )
        logger.info(f"Результат публикации: message_id={message_id}")
    except Exception as e:
        logger.error(f"Исключение при публикации: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка публикации: {str(e)}")

    if message_id:
        post.status = PostStatus.PUBLISHED.value
        post.telegram_message_id = message_id
        post.published_at = datetime.now(timezone.utc) + timedelta(hours=3)  # Moscow time
        post.channel_id = channel.id
        await db.commit()

        logger.info(f"Пост {post_id} успешно опубликован в {channel.channel_id}, message_id: {message_id}")
        return {"message": "Пост опубликован", "telegram_message_id": message_id}
    else:
        logger.error(f"Не удалось опубликовать пост {post_id} - telegram_service вернул None")
        raise HTTPException(status_code=500, detail="Ошибка публикации в Telegram - проверьте логи")


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


@router.post("/posts/{post_id}/toggle-ad", response_model=dict)
async def toggle_advertisement(
    post_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Переключить пометку 'Реклама'"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    post.is_advertisement = not post.is_advertisement
    await db.commit()

    return {
        "message": "Пометка обновлена",
        "is_advertisement": post.is_advertisement
    }


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


# === Эндпоинты для каналов ===

@router.get("/channels", response_model=List[ChannelResponse])
async def get_channels(db: AsyncSession = Depends(get_db)):
    """Получить список каналов"""
    result = await db.execute(select(Channel).order_by(Channel.created_at.desc()))
    channels = result.scalars().all()
    
    # Добавляем количество источников для каждого канала
    channels_with_count = []
    for channel in channels:
        sources_result = await db.execute(
            select(func.count(Source.id)).where(Source.channel_id == channel.id)
        )
        sources_count = sources_result.scalar()
        
        channel_dict = {
            "id": channel.id,
            "name": channel.name,
            "channel_id": channel.channel_id,
            "bot_token": channel.bot_token[:20] + "..." if len(channel.bot_token) > 20 else channel.bot_token,
            "ai_prompt": channel.ai_prompt,
            "logo_path": channel.logo_path,
            "logo_position": channel.logo_position,
            "logo_opacity": channel.logo_opacity,
            "is_active": channel.is_active,
            "created_at": channel.created_at,
            "sources_count": sources_count
        }
        channels_with_count.append(channel_dict)
    
    return channels_with_count


@router.post("/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_data: ChannelCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый канал"""
    channel = Channel(
        name=channel_data.name,
        bot_token=channel_data.bot_token,
        channel_id=channel_data.channel_id,
        ai_prompt=channel_data.ai_prompt,
        logo_path=channel_data.logo_path,
        logo_position=channel_data.logo_position,
        logo_opacity=channel_data.logo_opacity,
    )

    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    return channel


@router.get("/channels/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить канал по ID"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    return channel


@router.put("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    channel_data: ChannelUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить канал"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    update_data = channel_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    await db.commit()
    await db.refresh(channel)

    return channel


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить канал"""
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise HTTPException(status_code=404, detail="Канал не найден")

    # Проверяем, есть ли источники
    sources_result = await db.execute(
        select(func.count(Source.id)).where(Source.channel_id == channel_id)
    )
    sources_count = sources_result.scalar()

    if sources_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить канал с {sources_count} источниками. Сначала удалите источники."
        )

    await db.delete(channel)
    await db.commit()

    return None


@router.get("/channels/{channel_id}/sources", response_model=List[SourceResponse])
async def get_channel_sources(
    channel_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить источники канала"""
    result = await db.execute(
        select(Source).where(Source.channel_id == channel_id).order_by(Source.created_at.desc())
    )
    return result.scalars().all()


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

# Исправление проблемы со статусом PROCESSING

## Проблема
Посты застревали в статусе `PROCESSING` и не переходили в `READY` для публикации.

## Причины
1. **Отсутствие `joinedload`** при загрузке источника — связь `source.channel` не загружалась из-за ленивой загрузки в асинхронном контексте
2. **Отсутствие проверки канала** — если источник не привязан к каналу, пост не получал статус `READY`
3. **Отсутствие обработки ошибок AI** — при сбое AI адаптации пост мог остаться в `PROCESSING`

## Внесённые исправления

### 1. Добавлен `joinedload` для загрузки канала
**Файл:** `app/services/news_processor.py`

```python
# Было:
result = await session.execute(
    select(Source).where(Source.id == source_id)
)

# Стало:
result = await session.execute(
    select(Source)
    .options(joinedload(Source.channel))
    .where(Source.id == source_id)
)
```

### 2. Добавлена проверка привязки источника к каналу
```python
# Получаем канал из источника
channel = source.channel

# Проверяем, привязан ли источник к каналу
if not channel:
    logger.warning(f"  ⚠️ Источник {source.id} не привязан к каналу! Пост не может быть опубликован.")
    post.status = PostStatus.READY.value
    await session.commit()
    return
```

### 3. Добавлена обработка ошибок AI адаптации
```python
try:
    logger.info(f"  🤖 AI адаптация поста ID={post.id}...")
    adapted_content = await ai_service.adapt_text(item.content, ai_prompt)
    adapted_title = await ai_service.generate_title(item.content)
    logger.info(f"  ✓ AI адаптация завершена для поста ID={post.id}")
except Exception as e:
    logger.error(f"  ❌ Ошибка AI адаптации поста ID={post.id}: {e}")
    # При ошибке AI используем исходный текст
    adapted_content = item.content
    adapted_title = item.title
```

### 4. Упрощена логика установки статуса
```python
# Без автопубликации — устанавливаем статус READY
post.status = PostStatus.READY.value
post.channel_id = channel.id
await session.commit()
logger.info(f"  ✓ Пост {post.id} готов к публикации (статус: READY)")
```

## Инструкция по применению на сервере

### Шаг 1: Подключиться к серверу по SSH
```bash
ssh root@195.133.31.34
# Пароль: JGKja6YUUF
```

### Шаг 2: Перейти в директорию проекта
```bash
cd /opt/news_service
```

### Шаг 3: Исправить файл `app/services/news_processor.py`

Откройте файл:
```bash
nano app/services/news_processor.py
```

Внесите следующие изменения:

#### Изменение 1: Добавить импорт joinedload
В начало файла (после строки с `from sqlalchemy import select`):
```python
from sqlalchemy.orm import joinedload
```

#### Изменение 2: Исправить загрузку источника
Найти строку ~46-50 и заменить на:
```python
async with async_session_maker() as session:
    # Получаем источник с загруженной связью channel
    result = await session.execute(
        select(Source)
        .options(joinedload(Source.channel))
        .where(Source.id == source_id)
    )
    source = result.scalar_one_or_none()
```

#### Изменение 3: Добавить проверку канала
После строки `channel = source.channel` добавить:
```python
# Проверяем, привязан ли источник к каналу
if not channel:
    logger.warning(f"  ⚠️ Источник {source.id} не привязан к каналу! Пост не может быть опубликован.")
    post.status = PostStatus.READY.value
    await session.commit()
    return
```

#### Изменение 4: Обернуть AI адаптацию в try-except
Найти блок AI адаптации и обернуть в try-except:
```python
try:
    logger.info(f"  🤖 AI адаптация поста ID={post.id}...")
    adapted_content = await ai_service.adapt_text(item.content, ai_prompt)
    adapted_title = await ai_service.generate_title(item.content)
    logger.info(f"  ✓ AI адаптация завершена для поста ID={post.id}")
except Exception as e:
    logger.error(f"  ❌ Ошибка AI адаптации поста ID={post.id}: {e}")
    adapted_content = item.content
    adapted_title = item.title
```

Сохранить: `Ctrl+O → Enter`, выйти: `Ctrl+X`

### Шаг 4: Исправить застрявшие посты

Создать скрипт исправления:
```bash
nano fix_processing_posts.py
```

Вставить содержимое:
```python
"""
Скрипт для исправления постов, застрявших в статусе PROCESSING
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import async_session_maker
from app.models.db_models import Post, PostStatus


async def fix_processing_posts():
    async with async_session_maker() as session:
        result = await session.execute(
            select(Post).where(Post.status == PostStatus.PROCESSING.value)
        )
        processing_posts = result.scalars().all()
        
        if not processing_posts:
            print("✅ Постов со статусом PROCESSING не найдено")
            return
        
        print(f"Найдено постов в статусе PROCESSING: {len(processing_posts)}")
        
        fixed_count = 0
        for post in processing_posts:
            if post.channel_id:
                post.status = PostStatus.READY.value
                fixed_count += 1
                print(f"  ✓ Пост {post.id} переведён в READY")
            else:
                print(f"  ⚠️ Пост {post.id} не имеет channel_id, пропускаем")
        
        await session.commit()
        print(f"\n✅ Исправлено постов: {fixed_count}")


if __name__ == "__main__":
    asyncio.run(fix_processing_posts())
```

Сохранить: `Ctrl+O → Enter`, выйти: `Ctrl+X`

Запустить скрипт:
```bash
python fix_processing_posts.py
```

### Шаг 5: Перезапустить сервис
```bash
docker-compose restart news_service
```

### Шаг 6: Проверить логи
```bash
docker-compose logs -f news_service
```

## Результат
- ✅ Посты больше не застревают в `PROCESSING`
- ✅ Посты без привязанного канала получают статус `READY`
- ✅ Ошибки AI не блокируют обработку
- ✅ Существующие посты исправлены скриптом

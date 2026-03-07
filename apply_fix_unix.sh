#!/bin/bash
# Скрипт для автоматического применения исправлений
# Запуск на сервере: bash apply_fix.sh

set -e

echo "=========================================="
echo "Исправление проблемы со статусом PROCESSING"
echo "=========================================="

cd /opt/news_service

# Резервная копия
echo "[1/5] Создание резервной копии..."
cp app/services/news_processor.py app/services/news_processor.py.backup.$(date +%Y%m%d_%H%M%S)

# Применяем исправления через Python
echo "[2/5] Применение исправлений к news_processor.py..."
python3 << 'PYTHON_PATCH'
import re

with open('app/services/news_processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправление 1: Добавляем импорт joinedload
if 'from sqlalchemy.orm import joinedload' not in content:
    content = content.replace(
        'from sqlalchemy import select',
        'from sqlalchemy import select\nfrom sqlalchemy.orm import joinedload'
    )
    print("  ✓ Добавлен импорт joinedload")

# Исправление 2: Загрузка источника с joinedload
old_load = '''async with async_session_maker() as session:
            # Получаем источник
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )'''

new_load = '''async with async_session_maker() as session:
            # Получаем источник с загруженной связью channel
            result = await session.execute(
                select(Source)
                .options(joinedload(Source.channel))
                .where(Source.id == source_id)
            )'''

if old_load in content:
    content = content.replace(old_load, new_load)
    print("  ✓ Добавлен joinedload для загрузки канала")

# Исправление 3: Проверка канала
old_channel = '''# Получаем канал из источника
        channel = source.channel

        # Адаптируем текст через AI с промтом канала или источника'''

new_channel = '''# Получаем канал из источника
        channel = source.channel

        # Проверяем, привязан ли источник к каналу
        if not channel:
            logger.warning(f"  ⚠️ Источник {source.id} не привязан к каналу! Пост не может быть опубликован.")
            post.status = PostStatus.READY.value
            await session.commit()
            return

        # Адаптируем текст через AI с промтом канала или источника'''

if old_channel in content:
    content = content.replace(old_channel, new_channel)
    print("  ✓ Добавлена проверка привязки к каналу")

# Исправление 4: Обработка ошибок AI
old_ai = '''if source.ai_enabled:
            # Используем промт источника, если есть, иначе промт канала
            ai_prompt = source.ai_prompt or (channel.ai_prompt if channel else None)

            adapted_content = await ai_service.adapt_text(
                item.content,
                ai_prompt
            )
            adapted_title = await ai_service.generate_title(item.content)

            post.adapted_content = adapted_content
            post.adapted_title = adapted_title'''

new_ai = '''if source.ai_enabled:
            # Используем промт источника, если есть, иначе промт канала
            ai_prompt = source.ai_prompt or (channel.ai_prompt if channel else None)

            try:
                logger.info(f"  🤖 AI адаптация поста ID={post.id}...")
                adapted_content = await ai_service.adapt_text(
                    item.content,
                    ai_prompt
                )
                adapted_title = await ai_service.generate_title(item.content)
                logger.info(f"  ✓ AI адаптация завершена для поста ID={post.id}")
            except Exception as e:
                logger.error(f"  ❌ Ошибка AI адаптации поста ID={post.id}: {e}")
                # При ошибке AI используем исходный текст
                adapted_content = item.content
                adapted_title = item.title

            post.adapted_content = adapted_content
            post.adapted_title = adapted_title'''

if old_ai in content:
    content = content.replace(old_ai, new_ai)
    print("  ✓ Добавлена обработка ошибок AI")

# Исправление 5: Блок else
old_else = '''else:
            # Без автопубликации — оставляем в готовых
            post.status = PostStatus.READY.value
            if channel:
                post.channel_id = channel.id
            await session.commit()
            logger.info(f"  ✓ Пост {post.id} готов к публикации")'''

new_else = '''else:
            # Без автопубликации — устанавливаем статус READY
            post.status = PostStatus.READY.value
            post.channel_id = channel.id
            await session.commit()
            logger.info(f"  ✓ Пост {post.id} готов к публикации (статус: READY)")'''

if old_else in content:
    content = content.replace(old_else, new_else)
    print("  ✓ Исправлен блок обработки без автопубликации")

with open('app/services/news_processor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Файл news_processor.py успешно исправлен")
PYTHON_PATCH

# Создаём скрипт для исправления постов
echo "[3/5] Создание скрипта для исправления постов..."
cat > fix_processing_posts.py << 'FIX_SCRIPT'
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
FIX_SCRIPT

echo "[4/5] Запуск исправления постов..."
python3 fix_processing_posts.py

# Перезапуск сервиса
echo "[5/5] Перезапуск сервиса..."
docker-compose restart news_service

echo ""
echo "=========================================="
echo "✅ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ УСПЕШНО"
echo "=========================================="
echo ""
echo "Проверьте работу сервиса:"
echo "  http://195.133.31.34:8001"
echo ""
echo "Просмотр логов:"
echo "  docker-compose logs -f news_service"
echo ""

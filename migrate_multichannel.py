"""
Миграция: Мультиканальная система

Добавляет:
1. Таблица channels
2. Поле channel_id в sources
3. Поле channel_id в posts
4. Миграция данных: создание канала по умолчанию
"""
import asyncio
import os
from sqlalchemy import text
from app.database import engine


async def run_migration():
    """Выполнение миграции"""
    async with engine.begin() as conn:
        try:
            # 1. Создаём таблицу channels
            print("📢 Создание таблицы channels...")
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS channels (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    bot_token VARCHAR(255) NOT NULL,
                    channel_id VARCHAR(255) NOT NULL,
                    ai_prompt TEXT,
                    logo_path VARCHAR(512),
                    logo_position VARCHAR(50) DEFAULT 'bottom-right',
                    logo_opacity FLOAT DEFAULT 0.7,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            print("✅ Таблица channels создана")

            # 2. Добавляем channel_id в sources
            print("📢 Добавление channel_id в sources...")
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sources' AND column_name = 'channel_id'
            """))
            if not result.fetchone():
                await conn.execute(text("""
                    ALTER TABLE sources 
                    ADD COLUMN channel_id INTEGER REFERENCES channels(id)
                """))
                print("✅ Поле channel_id добавлено в sources")
            else:
                print("✅ Поле channel_id уже существует в sources")

            # 3. Добавляем channel_id в posts
            print("📢 Добавление channel_id в posts...")
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'posts' AND column_name = 'channel_id'
            """))
            if not result.fetchone():
                await conn.execute(text("""
                    ALTER TABLE posts 
                    ADD COLUMN channel_id INTEGER REFERENCES channels(id)
                """))
                print("✅ Поле channel_id добавлено в posts")
            else:
                print("✅ Поле channel_id уже существует в posts")

            # 4. Создаём канал по умолчанию из текущих настроек
            print("📢 Создание канала по умолчанию...")
            result = await conn.execute(text("SELECT COUNT(*) FROM channels"))
            count = result.scalar()
            
            if count == 0:
                # Получаем настройки из .env через SQL
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
                channel_id = os.getenv("TELEGRAM_CHANNEL_ID", "")
                
                if bot_token and channel_id:
                    await conn.execute(text("""
                        INSERT INTO channels (name, bot_token, channel_id, ai_prompt, is_active)
                        VALUES ('Default', :bot_token, :channel_id, '', TRUE)
                    """), {"bot_token": bot_token, "channel_id": channel_id})
                    print("✅ Канал по умолчанию создан")
                else:
                    print("⚠️ TELEGRAM_BOT_TOKEN или TELEGRAM_CHANNEL_ID не настроены")
                    print("   Создайте канал вручную через админ панель")
            else:
                print("✅ Каналы уже существуют")

            # 5. Привязываем все источники к каналу по умолчанию
            print("📢 Привязка источников к каналу...")
            await conn.execute(text("""
                UPDATE sources 
                SET channel_id = (SELECT id FROM channels LIMIT 1)
                WHERE channel_id IS NULL
            """))
            print("✅ Источники привязаны к каналу")

            # 6. Привязываем все посты к каналу через источник
            print("📢 Привязка постов к каналу...")
            await conn.execute(text("""
                UPDATE posts 
                SET channel_id = (
                    SELECT channel_id FROM sources WHERE sources.id = posts.source_id
                )
                WHERE channel_id IS NULL
            """))
            print("✅ Посты привязаны к каналу")

            print("\n" + "="*50)
            print("✅ Миграция завершена успешно!")
            print("="*50)

        except Exception as e:
            print(f"\n❌ Ошибка миграции: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())

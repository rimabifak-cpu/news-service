"""
Миграция: Добавление поля auto_publish в таблицу sources
"""
import asyncio
import sys
from sqlalchemy import text
from app.database import engine


async def run_migration():
    """Добавление колонки auto_publish"""
    async with engine.begin() as conn:
        try:
            # Проверяем, существует ли уже колонка
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'sources' AND column_name = 'auto_publish'
            """))
            
            if result.fetchone():
                print("✅ Колонка auto_publish уже существует")
                return
            
            # Добавляем колонку
            await conn.execute(text("""
                ALTER TABLE sources 
                ADD COLUMN auto_publish BOOLEAN DEFAULT FALSE
            """))
            
            print("✅ Колонка auto_publish добавлена")
            
        except Exception as e:
            print(f"❌ Ошибка миграции: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(run_migration())

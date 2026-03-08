#!/bin/bash
# Скрипт обновления и пересборки контейнера

echo "======================================"
echo "ОБНОВЛЕНИЕ NEWS SERVICE"
echo "======================================"

cd /opt/news_service

# 1. Обновление кода из Git
echo ""
echo "📦 Обновление кода из Git..."
git pull

# 2. Пересборка образа с новым кодом
echo ""
echo "🔨 Пересборка Docker образа..."
docker-compose build --no-cache news_service

# 3. Перезапуск сервисов
echo ""
echo "🔄 Перезапуск сервисов..."
docker-compose up -d

# 4. Копирование скриптов в контейнер
echo ""
echo "📋 Копирование скриптов в контейнер..."
docker cp fix_posts_sql.py news_service:/app/
docker cp test_ai.py news_service:/app/

# 5. Исправление старых постов
echo ""
echo "🔧 Исправление старых постов..."
docker exec -it news_service python fix_posts_sql.py

# 6. Проверка логов
echo ""
echo "📊 Последние логи:"
docker logs news_service --tail 20

echo ""
echo "======================================"
echo "✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО"
echo "======================================"
echo ""
echo "Для проверки парсинга выполните:"
echo "  docker exec -it news_service python -c \""
echo "  import asyncio"
echo "  from app.services.news_processor import news_processor"
echo "  asyncio.run(news_processor.process_source(1))"
echo "  \""

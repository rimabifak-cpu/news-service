#!/bin/bash
# Скрипт установки и запуска News Service на сервере
# Запускать на сервере после копирования файлов

set -e

echo "============================================"
echo "  News Service - Установка на сервер"
echo "============================================"

PROJECT_DIR="/opt/news_service"
cd $PROJECT_DIR

# Проверка Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установка..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose не найден. Установка..."
    apt-get update && apt-get install -y docker-compose
fi

# Остановка старых контейнеров
echo "[1/4] Остановка старых сервисов..."
docker-compose down || true

# Сборка
echo "[2/4] Сборка контейнеров..."
docker-compose build --no-cache

# Запуск
echo "[3/4] Запуск сервисов..."
docker-compose up -d

# Ожидание
echo "[4/4] Ожидание запуска (15 сек)..."
sleep 15

# Статус
echo ""
echo "============================================"
echo "  Статус сервисов:"
echo "============================================"
docker-compose ps

echo ""
echo "============================================"
echo "  Логи сервиса:"
echo "============================================"
docker-compose logs --tail=20 news_service

echo ""
echo "============================================"
echo "  ✅ News Service запущен!"
echo "============================================"
echo ""
echo "  Админ панель: http://$(curl -s ifconfig.me):8001"
echo ""
echo "  Полезные команды:"
echo "    docker-compose logs -f       # Логи"
echo "    docker-compose restart       # Перезапуск"
echo "    docker-compose down          # Остановка"
echo ""

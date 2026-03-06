# Исправление ошибки публикации в Telegram

## Проблема
Ошибка 500 при нажатии кнопки "Опубликовать" в админ панели.

## Причины
1. **SVG логотип** - Pillow не поддерживает SVG напрямую
2. **Недостаточное логирование** - сложно было диагностировать проблему

## Внесённые изменения

### 1. requirements.txt
Добавлена зависимость `cairosvg==2.7.1` для конвертации SVG в PNG.

### 2. app/services/image_service.py
- Добавлен метод `_get_logo()` с поддержкой SVG, PNG, JPG
- SVG конвертируется в PNG через cairosvg перед обработкой
- Улучшена обработка ошибок

### 3. app/services/telegram_service.py
- Добавлено подробное логирование процесса публикации
- Логирование статуса ответа Telegram API
- `exc_info=True` для traceback в логах

### 4. app/api/routes.py
- Добавлено логирование текста поста, пути к изображению
- Исправлено `datetime.utcnow()` → `datetime.now()`
- Улучшено сообщение об ошибке

### 5. Dockerfile
Добавлены системные зависимости для cairosvg:
- libcairo2
- libffi-dev
- libgdk-pixbuf2.0-0
- libpango1.0-0

## Применение на сервере

### Вариант 1: Через Git (рекомендуется)

```bash
cd /opt/news_service

# Получить обновления
git pull origin main

# Пересобрать и перезапустить
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Проверить логи
docker-compose logs -f news_service
```

### Вариант 2: Ручное копирование

```bash
# На локальной машине (PowerShell)
cd C:\Users\HONOR\Documents\news_service

# Копирование файлов на сервер
scp requirements.txt root@195.133.31.34:/opt/news_service/
scp Dockerfile root@195.133.31.34:/opt/news_service/
scp -r app/ root@195.133.31.34:/opt/news_service/app/

# На сервере
ssh root@195.133.31.34
cd /opt/news_service

# Пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Логи
docker-compose logs -f news_service
```

## Проверка работы

1. Откройте админ панель: http://195.133.31.34:8001
2. Перейдите в "Лента постов"
3. Нажмите "Опубликовать" на любом посте
4. Проверьте логи: должны быть сообщения:
   ```
   Начало публикации поста XX
   Текст поста: ...
   Проверка изображения: /app/static/uploads/...
   Вызов telegram_service.publish_post
   Публикация: image_path=..., exists=true/false
   Отправка текста в канал: @legaldecision_news
   Telegram response status: 200
   Пост опубликован в @legaldecision_news, message_id: XXX
   ```

## Возможные проблемы

### Ошибка "cairosvg не установлен"
```bash
docker-compose exec news_service pip install cairosvg
docker-compose restart news_service
```

### Ошибка Telegram "Unauthorized"
Проверьте токен бота в `.env`:
```bash
docker-compose exec news_service cat .env | grep TELEGRAM
```

### Ошибка "Channel not found"
Убедитесь, что:
- Бот добавлен в канал как администратор
- `TELEGRAM_CHANNEL_ID` указан правильно (например, `@legaldecision_news` или `-1001234567890`)

## Откат изменений

Если что-то пошло не так:
```bash
cd /opt/news_service
git log --oneline -5  # Найти последний рабочий коммит
git reset --hard <commit-hash>
docker-compose restart
```

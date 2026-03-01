# News Service - Автосбор и адаптация новостей

Сервис для автоматического сбора новостей из различных источников (сайты, RSS, Telegram, ВКонтакте), 
адаптации текста с помощью AI и публикации в Telegram-канал.

## 🚀 Возможности

- **Добавление источников**: веб-сайты, RSS-ленты, Telegram-каналы, ВКонтакте
- **AI адаптация текста**: стилизация под Telegram-канал с помощью GPT
- **Наложение логотипа**: автоматическое добавление логотипа на изображения
- **Веб-интерфейс**: лента готовых постов с кнопками "Опубликовать" / "Отклонить"
- **Автопарсинг**: планировщик для регулярного сбора новостей
- **Публикация в Telegram**: отправка постов в канал через бота

## 📋 Структура проекта

```
news_service/
├── app/
│   ├── api/
│   │   └── routes.py          # API эндпоинты
│   ├── models/
│   │   └── db_models.py       # SQLAlchemy модели
│   ├── parsers/
│   │   ├── base.py            # Базовый класс парсера
│   │   ├── website.py         # Парсер сайтов
│   │   ├── rss.py             # RSS парсер
│   │   ├── telegram.py        # Telegram парсер
│   │   └── vk.py              # ВКонтакте парсер
│   ├── services/
│   │   ├── ai_service.py      # AI адаптация текста
│   │   ├── image_service.py   # Обработка изображений
│   │   ├── telegram_service.py # Публикация в Telegram
│   │   └── news_processor.py  # Обработка новостей
│   ├── utils/
│   ├── config.py              # Конфигурация
│   ├── database.py            # Подключение к БД
│   └── main.py                # FastAPI приложение
├── static/
│   ├── images/                # Логотипы
│   ├── uploads/               # Загруженные файлы
│   └── app.js                 # Frontend JavaScript
├── templates/
│   └── index.html             # Админ панель
├── scheduler.py               # Планировщик парсинга
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 🔧 Установка

### 1. Клонирование и настройка

```bash
cd news_service
cp .env.example .env
```

### 2. Настройка переменных окружения

Отредактируйте `.env`:

```env
# База данных
DATABASE_URL=postgresql+asyncpg://news_user:news_password@postgres/news_db

# AI (OpenAI или совместимый API)
AI_API_KEY=sk-...
AI_API_URL=https://api.openai.com/v1
AI_MODEL=gpt-4-turbo-preview

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHANNEL_ID=@your-channel

# Логотип
LOGO_PATH=/app/static/images/logo.png
LOGO_POSITION=bottom-right
LOGO_OPACITY=0.7

# Парсинг
PARSER_INTERVAL=300  # секунд между запусками
```

### 3. Запуск через Docker

```bash
docker-compose up -d
```

Сервис будет доступен по адресу: http://localhost:8001

### 4. Локальный запуск (без Docker)

```bash
# Установка зависимостей
pip install -r requirements.txt

# Создание БД (PostgreSQL должен быть запущен)
# Установите DATABASE_URL в .env

# Запуск
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# Запуск планировщика (отдельный терминал)
python scheduler.py
```

## 📖 Использование

### 1. Добавление источника

1. Откройте админ панель: http://localhost:8001
2. Перейдите в раздел "Источники"
3. Нажмите "Добавить источник"
4. Заполните форму:
   - Название
   - URL источника
   - Тип (сайт, RSS, Telegram, VK)
   - AI промт (опционально)
   - Селекторы для парсинга (для сайтов)

### 2. Парсинг

- **Автоматически**: планировщик запускается каждые N секунд (PARSER_INTERVAL)
- **Вручную**: в админ панели нажмите кнопку обновления у источника

### 3. Публикация постов

1. Перейдите в "Лента постов"
2. Просмотрите готовые посты
3. Нажмите "Опубликовать" для отправки в Telegram
4. Или "Отклонить" для удаления

## 🔌 API

### Источники

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/sources` | Список источников |
| POST | `/api/sources` | Создать источник |
| GET | `/api/sources/{id}` | Получить источник |
| PUT | `/api/sources/{id}` | Обновить источник |
| DELETE | `/api/sources/{id}` | Удалить источник |
| POST | `/api/sources/{id}/parse` | Запустить парсинг |

### Посты

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/posts` | Список постов |
| GET | `/api/posts/{id}` | Получить пост |
| POST | `/api/posts/{id}/publish` | Опубликовать |
| POST | `/api/posts/{id}/reject` | Отклонить |

### Статистика

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/stats` | Статистика сервиса |

## 🎨 Настройка логотипа

1. Поместите файл логотипа в `static/images/logo.png`
2. Настройте параметры в `.env`:
   - `LOGO_POSITION`: top-left, top-right, bottom-left, bottom-right
   - `LOGO_OPACITY`: прозрачность от 0.0 до 1.0

## 🔐 Безопасность

- Смените пароль администратора в production
- Используйте HTTPS для продакшена
- Не храните секреты в коде

## 📝 Лицензия

MIT

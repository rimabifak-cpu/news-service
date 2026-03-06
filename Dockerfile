FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libmagic1 \
    libcairo2 \
    libffi-dev \
    libgdk-pixbuf2.0-0 \
    libpango1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание директорий
RUN mkdir -p /app/static/uploads /app/static/images

# Порт
EXPOSE 8001

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

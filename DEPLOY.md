# 🚀 Инструкция по деплою News Service

## 📋 Быстрый деплой (через PowerShell)

### Шаг 1: Откройте PowerShell в папке проекта

```powershell
cd C:\Users\HONOR\Documents\news_service
```

### Шаг 2: Запустите скрипт деплоя

```powershell
.\deploy.bat
```

Скрипт:
1. Создаст архив проекта
2. Скопирует на сервер через SCP
3. Запустит установку

**Примечание:** При копировании введите пароль: `JGKja6YUUF`

---

## 🔧 Ручной деплой (через SSH)

### Шаг 1: Подключитесь к серверу

Откройте PuTTY или PowerShell:

```powershell
ssh root@195.133.31.34
# Пароль: JGKja6YUUF
```

### Шаг 2: Создайте директорию и скопируйте файлы

**В PowerShell (локально):**
```powershell
# Создайте архив
Compress-Archive -Path .\* -DestinationPath ..\news_service_deploy.zip -Force

# Копируйте на сервер
scp ..\news_service_deploy.zip root@195.133.31.34:/tmp/
# Пароль: JGKja6YUUF
```

### Шаг 3: Установите на сервере

**На сервере (по SSH):**
```bash
cd /tmp
unzip -o news_service_deploy.zip -d /opt/news_service
cd /opt/news_service
chmod +x install.sh
bash install.sh
```

---

## ✅ Проверка работы

### 1. Откройте админ панель

```
http://195.133.31.34:8001
```

### 2. Проверьте логи

```bash
cd /opt/news_service
docker-compose logs -f
```

### 3. Проверьте статус

```bash
docker-compose ps
```

---

## ⚙️ Настройка

### 1. Отредактируйте .env

```bash
cd /opt/news_service
nano .env
```

**Важные параметры:**

```env
# AI для адаптации текста (получите на https://platform.openai.com)
AI_API_KEY=sk-...

# Telegram бот (получите у @BotFather)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHANNEL_ID=@your-channel
```

### 2. Перезапустите сервис

```bash
docker-compose restart
```

---

## 📊 Добавление источника новостей

1. Откройте http://195.133.31.34:8001
2. Перейдите в "Источники"
3. Нажмите "Добавить источник"
4. Заполните:
   - Название: например "РИА Новости"
   - Тип: "website" или "rss" или "telegram" или "vk"
   - URL: https://...
5. Нажмите "Добавить"
6. Нажмите кнопку обновления для парсинга

---

## 🔍 Управление сервисом

```bash
cd /opt/news_service

# Просмотр логов
docker-compose logs -f

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Запуск
docker-compose up -d

# Обновление из git
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

---

## 🆘 Решение проблем

### Ошибка "Connection refused" при копировании

Проверьте доступность сервера:
```powershell
Test-NetConnection -ComputerName 195.133.31.34 -Port 22
```

### Ошибка Docker

```bash
# Переустановите Docker
curl -fsSL https://get.docker.com | sh
```

### Порт 8001 занят

Измените в `docker-compose.yml`:
```yaml
ports:
  - "8002:8001"  # Используйте другой порт
```

### AI не работает

Проверьте API ключ:
```bash
docker-compose exec news_service env | grep AI
```

---

## 📞 Поддержка

При проблемах проверьте:
1. Логи: `docker-compose logs -f`
2. Статус: `docker-compose ps`
3. Конфиг: `cat .env`

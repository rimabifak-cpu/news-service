# News Service - Автодеплой

## Быстрый старт

### 1. Создайте репозиторий на GitHub

Перейдите на https://github.com/new и создайте репозиторий (например, `news-service`)

### 2. Запушьте код

```powershell
cd C:\Users\HONOR\Documents\news_service

# Добавьте remote (замените USERNAME на ваш GitHub логин)
git remote add origin https://github.com/USERNAME/news-service.git

# Отправьте код
git branch -M main
git push -u origin main
```

### 3. На сервере выполните

```bash
# Склонируйте репозиторий
git clone https://github.com/USERNAME/news-service.git /opt/news_service
cd /opt/news_service

# Запустите установку
bash install.sh
```

### 4. Откройте админ панель

```
http://195.133.31.34:8001
```

---

## Альтернатива: Прямое копирование

Если не хотите использовать GitHub, скопируйте файлы через SCP:

```powershell
# Из PowerShell на локальной машине
cd C:\Users\HONOR\Documents\news_service

# Копируйте все файлы
scp -r ./* root@195.133.31.34:/opt/news_service/
# Пароль: JGKja6YUUF

# На сервере:
ssh root@195.133.31.34
cd /opt/news_service
bash install.sh
```

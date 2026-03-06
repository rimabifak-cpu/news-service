# Обновление News Service с функцией автопубликации

## 1. Подключиться к серверу

```bash
ssh root@195.133.31.34
```

## 2. Обновить код

```bash
cd /opt/news_service
git pull origin main
```

## 3. Применить миграцию БД

```bash
python migrate_add_auto_publish.py
```

## 4. Перезапустить сервисы

```bash
docker-compose restart news_service scheduler
```

## 5. Очистить кэш браузера

Нажмите **Ctrl+F5** (Windows) или **Cmd+Shift+R** (Mac) на странице админ панели.

## 6. Проверить

1. Откройте `http://195.133.31.34:8001`
2. Перейдите в **"Источники"**
3. Нажмите **"✏️"** у любого источника
4. Должен появиться чекбокс:
   ```
   ☑ 🚀 Автопубликация — публиковать без модерации
   ```

---

## Если чекбокса всё равно нет

1. Проверьте версию файла на сервере:
```bash
grep -n "source-auto-publish" /opt/news_service/templates/index.html
```

Должно вывести:
```
429:                            <input class="form-check-input" type="checkbox" id="source-auto-publish">
```

2. Если не выводит — файл не обновился. Попробуйте:
```bash
git status
git reset --hard origin/main
docker-compose restart news_service
```

3. Очистите кэш браузера ещё раз (Ctrl+F5).

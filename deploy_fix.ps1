# Скрипт для исправления проблемы со статусом PROCESSING
# Запуск: .\deploy_fix.ps1

$serverHost = "195.133.31.34"
$serverUser = "root"
$serverPassword = "JGKja6YUUF"
$projectPath = "/opt/news_service"

Write-Host "=== Исправление проблемы PROCESSING ===" -ForegroundColor Cyan

# Создаём команду для исправления файла news_processor.py
$fixScript = @'
cd /opt/news_service

# Создаём резервную копию
cp app/services/news_processor.py app/services/news_processor.py.bak

# Исправляем файл с помощью sed
# 1. Добавляем импорт joinedload после строки с "from sqlalchemy import select"
sed -i 's/from sqlalchemy import select/from sqlalchemy import select\nfrom sqlalchemy.orm import joinedload/' app/services/news_processor.py

# 2. Исправляем загрузку источника - добавляем joinedload
# Это сложная замена, поэтому используем Python для патчинга
python3 << 'PYTHON_SCRIPT'
import re

with open('app/services/news_processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Исправление 1: Загрузка источника с joinedload
old_load = '''async with async_session_maker() as session:
            # Получаем источник
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )'''

new_load = '''async with async_session_maker() as session:
            # Получаем источник с загруженной связью channel
            result = await session.execute(
                select(Source)
                .options(joinedload(Source.channel))
                .where(Source.id == source_id)
            )'''

content = content.replace(old_load, new_load)

# Исправление 2: Проверка канала после получения channel
old_channel = '''# Получаем канал из источника
        channel = source.channel

        # Адаптируем текст через AI'''

new_channel = '''# Получаем канал из источника
        channel = source.channel

        # Проверяем, привязан ли источник к каналу
        if not channel:
            logger.warning(f"  ⚠️ Источник {source.id} не привязан к каналу! Пост не может быть опубликован.")
            post.status = PostStatus.READY.value
            await session.commit()
            return

        # Адаптируем текст через AI'''

content = content.replace(old_channel, new_channel)

# Исправление 3: Обработка ошибок AI
old_ai = '''if source.ai_enabled:
            # Используем промт источника, если есть, иначе промт канала
            ai_prompt = source.ai_prompt or (channel.ai_prompt if channel else None)

            adapted_content = await ai_service.adapt_text(
                item.content,
                ai_prompt
            )
            adapted_title = await ai_service.generate_title(item.content)

            post.adapted_content = adapted_content
            post.adapted_title = adapted_title'''

new_ai = '''if source.ai_enabled:
            # Используем промт источника, если есть, иначе промт канала
            ai_prompt = source.ai_prompt or (channel.ai_prompt if channel else None)

            try:
                logger.info(f"  🤖 AI адаптация поста ID={post.id}...")
                adapted_content = await ai_service.adapt_text(
                    item.content,
                    ai_prompt
                )
                adapted_title = await ai_service.generate_title(item.content)
                logger.info(f"  ✓ AI адаптация завершена для поста ID={post.id}")
            except Exception as e:
                logger.error(f"  ❌ Ошибка AI адаптации поста ID={post.id}: {e}")
                # При ошибке AI используем исходный текст
                adapted_content = item.content
                adapted_title = item.title

            post.adapted_content = adapted_content
            post.adapted_title = adapted_title'''

content = content.replace(old_ai, new_ai)

# Исправление 4: Упрощаем блок else
old_else = '''else:
            # Без автопубликации — оставляем в готовых
            post.status = PostStatus.READY.value
            if channel:
                post.channel_id = channel.id
            await session.commit()
            logger.info(f"  ✓ Пост {post.id} готов к публикации")'''

new_else = '''else:
            # Без автопубликации — устанавливаем статус READY
            post.status = PostStatus.READY.value
            post.channel_id = channel.id
            await session.commit()
            logger.info(f"  ✓ Пост {post.id} готов к публикации (статус: READY)")'''

content = content.replace(old_else, new_else)

with open('app/services/news_processor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Файл news_processor.py исправлён")
PYTHON_SCRIPT

# Перезапускаем сервис
docker-compose restart news_service

echo "✅ Исправления применены. Сервис перезапущен."
'@

Write-Host "Подключение к серверу $serverHost..." -ForegroundColor Yellow

# Используем ssh для выполнения команд на сервере
# Для Windows 10+ с OpenSSH клиентом
$env:SSH_ASKPASS = ""
$env:SSHPASS = $serverPassword

# Команда для выполнения
$sshCommand = "ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no -o PasswordAuthentication=no $serverUser@$serverHost `"bash -s`""

Write-Host "Выполнение исправлений на сервере..." -ForegroundColor Yellow
Write-Host "Введите пароль при запросе: $serverPassword" -ForegroundColor Green

# Альтернатива: используем plink или ручной ввод
Write-Host "`n=== ИНСТРУКЦИЯ ДЛЯ РУЧНОГО ВЫПОЛНЕНИЯ ===" -ForegroundColor Cyan
Write-Host "1. Подключитесь к серверу:" -ForegroundColor White
Write-Host "   ssh root@195.133.31.34" -ForegroundColor Gray
Write-Host "   Пароль: $serverPassword" -ForegroundColor Gray
Write-Host "`n2. Перейдите в директорию проекта:" -ForegroundColor White
Write-Host "   cd /opt/news_service" -ForegroundColor Gray
Write-Host "`n3. Примените исправления (см. FIX_INSTRUCTION.md)" -ForegroundColor White

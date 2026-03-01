@echo off
chcp 65001 >nul
echo ============================================
echo   News Service - Автодеплой на сервер
echo ============================================
echo.

cd /d %~dp0

REM Создаем архив
echo [1/3] Создание архива проекта...
powershell -Command "Compress-Archive -Path '.\*' -DestinationPath '..\news_service_deploy.zip' -Force" 2>nul
if errorlevel 1 (
    echo Ошибка создания архива!
    pause
    exit /b 1
)
echo Готово: ..\news_service_deploy.zip
echo.

REM Копирование на сервер
echo [2/3] Копирование на сервер 195.133.31.34...
echo.
echo ВВЕДИТЕ ПАРОЛЬ СЕРВЕРА: JGKja6YUUF
echo.
scp ..\news_service_deploy.zip root@195.133.31.34:/tmp/
if errorlevel 1 (
    echo.
    echo ❌ Ошибка копирования! Проверьте подключение.
    del ..\news_service_deploy.zip 2>nul
    pause
    exit /b 1
)
echo ✅ Файлы скопированы
echo.

REM Команды для сервера
echo [3/3] Команды для выполнения на сервере:
echo.
echo Подключитесь к серверу:
echo   ssh root@195.133.31.34
echo   пароль: JGKja6YUUF
echo.
echo Затем выполните:
echo   cd /tmp
echo   unzip -o news_service_deploy.zip -d /opt/news_service
echo   cd /opt/news_service
echo   bash install.sh
echo.
echo ============================================
echo  ✅ Архив готов к загрузке!
echo ============================================
echo.
del ..\news_service_deploy.zip 2>nul
echo Архив создан и готов. Выполните команды выше.
echo.
pause

@echo off
REM Скрипт деплоя News Service на сервер
REM Запускать из PowerShell с установленным OpenSSH

set SERVER=root@195.133.31.34
set REMOTE_DIR=/opt/news_service
set PASSWORD=JGKja6YUUF

echo ============================================
echo  News Service - Деплой на сервер
echo ============================================
echo.

REM Создаем архив проекта
echo [1/4] Создание архива...
powershell -Command "Compress-Archive -Path .\* -DestinationPath ..\news_service_deploy.zip -Force"

echo [2/4] Копирование на сервер...
echo.
echo Введите пароль при запросе: %PASSWORD%
echo.
scp ..\news_service_deploy.zip %SERVER%:/tmp/

if %ERRORLEVEL% neq 0 (
    echo Ошибка копирования! Проверьте подключение.
    del ..\news_service_deploy.zip
    exit /b 1
)

echo [3/4] Установка на сервере...
echo.
REM Команды для выполнения на сервере
set CMDS=^
cd /tmp && ^
unzip -o news_service_deploy.zip -d %REMOTE_DIR% && ^
cd %REMOTE_DIR% && ^
docker-compose down && ^
docker-compose build --no-cache && ^
docker-compose up -d && ^
docker-compose ps

echo [4/4] Готово!
echo.
echo Админ панель: http://195.133.31.34:8001
echo.

REM Удаляем архив
del ..\news_service_deploy.zip
echo Нажмите любую клавишу для выхода...
pause > nul

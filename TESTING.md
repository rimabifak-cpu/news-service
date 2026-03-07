# Тестирование и Мониторинг

## 📋 Запуск тестов

### Базовый запуск
```bash
# Запустить все тесты
pytest

# Запустить с отчётом о покрытии
pytest --cov=app --cov-report=html

# Запустить конкретный тест
pytest tests/test_ai_service.py::TestAIServiceAdaptText::test_adapt_text_SuccessfulAdaptation_ReturnsAdaptedText

# Запустить тесты с verbose выводом
pytest -v

# Запустить только unit-тесты
pytest -m unit

# Запустить интеграционные тесты
pytest -m integration
```

### Требования к покрытию
- **Минимальное покрытие:** 85%
- **Все публичные методы:** должны быть покрыты
- **Граничные условия:** null, пустые значения, исключения

---

## 📊 Структура тестов

```
tests/
├── conftest.py              # Fixtures и конфигурация
├── test_ai_service.py       # Тесты AI сервиса
├── test_api_routes.py       # Тесты API эндпоинтов
├── test_middleware.py       # Тесты middleware
├── test_news_processor.py   # Тесты обработчика новостей
├── test_parsers.py          # Тесты парсеров
├── test_services.py         # Тесты сервисов
└── test_models.py           # Тесты моделей
```

---

## 🔍 Логирование

### Уровни логирования

| Уровень | Описание | Пример |
|---------|----------|--------|
| `DEBUG` | Детальная отладка | `AI_ADAPT_START` |
| `INFO` | Штатная работа | `AI_ADAPT_SUCCESS` |
| `WARNING` | Предупреждения | `AI_API_KEY_NOT_CONFIGURED` |
| `ERROR` | Ошибки | `AI_TIMEOUT` |

### Формат логов

**Текстовый формат:**
```
2024-03-07 19:30:15.123 | INFO     | app.services.ai_service:adapt_text:45 | AI_ADAPT_SUCCESS | {'input_length': 500, 'output_length': 450, 'duration_ms': 1234.56}
```

**JSON формат (для продакшена):**
```json
{
  "timestamp": "2024-03-07T19:30:15.123456",
  "level": "INFO",
  "module": "app.services.ai_service",
  "function": "adapt_text",
  "line": 45,
  "message": "AI_ADAPT_SUCCESS",
  "input_length": 500,
  "output_length": 450,
  "duration_ms": 1234.56,
  "model": "openai/gpt-3.5-turbo"
}
```

### Просмотр логов

```bash
# Логи в реальном времени
docker-compose logs -f news_service

# Логи за последние 5 минут
docker-compose logs --tail=100 news_service

# Только ошибки
docker-compose logs news_service | grep ERROR

# Поиск по request_id
docker-compose logs news_service | grep "test-request-id"
```

---

## 🎯 Request Tracing

Каждый запрос получает уникальный `request_id`, который передаётся через все слои системы.

### Пример лога запроса

```
REQUEST_START:
  request_id: 550e8400-e29b-41d4-a716-446655440000
  user_id: user-123
  method: POST
  path: /api/posts
  client_ip: 192.168.1.1

REQUEST_END:
  request_id: 550e8400-e29b-41d4-a716-446655440000
  status_code: 200
  duration_ms: 145.23
```

---

## 🚨 Alerting Rules

### Критические алерты
- **>5 ошибок в минуту** → Критический алерт
- **>1% failed requests** → Предупреждение
- **Response time >2s** → Логировать медленно

### Мониторинг AI сервиса

```python
# Статистика AI запросов
{
    "total_requests": 150,
    "total_errors": 3,
    "error_rate": 0.02,  # 2%
    "avg_duration_ms": 1234.56
}
```

---

## 🧪 Написание тестов

### Шаблон теста

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

class TestMyService:
    """Tests for MyService"""
    
    @pytest.mark.asyncio
    async def test_method_Scenario_ExpectedResult(self):
        """ServiceMethod_Scenario_ExpectedResult"""
        # Arrange
        service = MyService()
        mock_dependency = AsyncMock()
        
        # Act
        result = await service.method()
        
        # Assert
        assert result == expected_value
```

### Именование тестов

Формат: `[ИмяМетода]_[Сценарий]_[ОжидаемыйРезультат]`

Примеры:
- `GetUserById_UserNotFound_ReturnsNull`
- `CalculateDiscount_AmountAboveThreshold_AppliesDiscount`
- `AIService_adapt_text_NoApiKey_ReturnsOriginalText`

---

## 📁 Health Checks

### Проверка здоровья

```bash
# HTTP запрос
curl http://localhost:8001/health

# Ответ: 200 OK
{
    "status": "ok",
    "version": "1.0.0",
    "checks": {
        "database": "ok"
    }
}

# Ответ: 503 Service Unavailable
{
    "status": "degraded",
    "version": "1.0.0",
    "checks": {
        "database": "error: connection refused"
    }
}
```

---

## 🔧 CI/CD Интеграция

### GitHub Actions workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        run: pytest --cov=app --cov-report=xml
      
      - name: Check coverage
        run: |
          coverage report --fail-under=85
```

---

## 📊 Отчёт о покрытии

После запуска тестов с `--cov-report=html`:

```bash
# Открыть отчёт в браузере
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 🐛 Поиск багов

### Алгоритм отладки

1. **Найти логи за период ошибки**
   ```bash
   docker-compose logs --since="2024-03-07T19:00:00" --until="2024-03-07T20:00:00"
   ```

2. **Определить точку первого сбоя**
   ```bash
   docker-compose logs news_service | grep ERROR | head -5
   ```

3. **Проверить request_id**
   ```bash
   docker-compose logs news_service | grep "request-id-123"
   ```

4. **Воспроизвести локально**
   ```bash
   pytest tests/test_file.py::TestClass::test_method -v
   ```

5. **Исправить + добавить тест**

6. **Добавить мониторинг**

---

## 📚 Дополнительные ресурсы

- [Pytest Documentation](https://docs.pytest.org/)
- [Loguru Documentation](https://loguru.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

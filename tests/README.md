# Тесты 1C Convert Kit

Этот каталог содержит автоматические тесты для проверки функциональности проекта.

## 🚀 Быстрый запуск

### Windows
```cmd
tests\run_tests.cmd
```

### Linux/Mac
```bash
./tests/run_tests.sh
```

## 📁 Структура тестов

```
tests/
├── unit/                    # Модульные тесты
│   ├── test_params_descriptions.py   # Тесты описаний параметров
│   └── test_details_table.py         # Тесты таблицы деталей
├── integration/             # Интеграционные тесты (пока пусто)
├── fixtures/                # Тестовые данные (пока пусто)
├── run_tests.cmd           # Запуск тестов для Windows
├── run_tests.sh            # Запуск тестов для Linux/Mac
└── README.md               # Этот файл
```

## 🧪 Доступные тесты

### Unit-тесты (8 тестов)

**test_params_descriptions.py** - Проверка работы с описаниями параметров:
- ✅ Существование JSON файла
- ✅ Валидность JSON структуры
- ✅ Наличие секций (common + скрипты)
- ✅ Общие параметры
- ✅ Специфичные параметры для скриптов
- ✅ Функция получения описаний
- ✅ Реальный сценарий использования

**test_details_table.py** - Проверка логики таблицы деталей:
- ✅ Формирование таблицы деталей проекта
- ✅ Порядок параметров (ScriptName первым)
- ✅ Объединение базового .env и .env проекта
- ✅ Отображение переопределенных значений

### Integration-тесты (4 теста)

**test_convert_integration.py** - Полный цикл конвертации с реальными инструментами 1С:
- ✅ Конвертация EDT конфигурации в CF файл
- ✅ Конвертация EDT расширения в CFE файл
- ✅ Загрузка и объединение .env файлов
- ✅ Проверка наличия исходных тестовых проектов

**Требования для integration-тестов:**
- Установленная платформа 1C:Enterprise (1cv8.exe)
- Установленная среда 1C:EDT (1cedtcli.exe)
- Корректные пути в `tests/fixtures/base_test.env`

## 📋 Требования

Для запуска тестов необходим **pytest**:

```bash
pip install pytest
```

Или установите все dev-зависимости:

```bash
pip install -r requirements-dev.txt
```

## 🔧 Запуск тестов

### Все тесты
```bash
pytest tests/
```

### Только unit-тесты
```bash
pytest tests/unit/
```

### Только integration-тесты
```bash
pytest tests/integration/
```

### Конкретный файл
```bash
pytest tests/unit/test_params_descriptions.py
```

### С подробным выводом
```bash
pytest tests/ -v
```

### С покрытием кода (если установлен pytest-cov)
```bash
pytest tests/ --cov=src --cov-report=html
```

## 📊 Ожидаемый результат

```
================================ test session starts ================================
platform win32 -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 8 items

tests/unit/test_details_table.py::test_details_table_logic PASSED              [ 12%]
tests/unit/test_params_descriptions.py::test_json_file_exists PASSED           [ 25%]
tests/unit/test_params_descriptions.py::test_json_file_valid PASSED            [ 37%]
tests/unit/test_params_descriptions.py::test_json_structure PASSED             [ 50%]
tests/unit/test_params_descriptions.py::test_common_params PASSED              [ 62%]
tests/unit/test_params_descriptions.py::test_script_specific_params PASSED     [ 75%]
tests/unit/test_params_descriptions.py::test_get_description_function PASSED   [ 87%]
tests/unit/test_params_descriptions.py::test_real_scenario PASSED              [100%]

================================= 8 passed in 0.04s =================================
```

## 🐛 Отладка тестов

### Запуск с выводом print()
```bash
pytest tests/ -v -s
```

### Остановка на первой ошибке
```bash
pytest tests/ -x
```

### Запуск только упавших тестов
```bash
pytest tests/ --lf
```

### Подробный traceback
```bash
pytest tests/ --tb=long
```

## ✍️ Написание новых тестов

### Создание нового теста

1. Создайте файл в `tests/unit/` с префиксом `test_`:
   ```python
   # tests/unit/test_my_feature.py
   
   def test_my_feature():
       """Описание теста"""
       # Arrange
       expected = "result"
       
       # Act
       actual = my_function()
       
       # Assert
       assert actual == expected
   ```

2. Запустите тест:
   ```bash
   pytest tests/unit/test_my_feature.py -v
   ```

### Использование фикстур

```python
import pytest

@pytest.fixture
def sample_data():
    """Фикстура с тестовыми данными"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Тест использующий фикстуру"""
    assert sample_data["key"] == "value"
```

## 📚 Полезные ссылки

- [Документация pytest](https://docs.pytest.org/)
- [Руководство по написанию тестов](https://docs.pytest.org/en/stable/how-to/index.html)
- [Best practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

## 🎯 TODO

- [x] Добавить интеграционные тесты для конвертации
- [x] Создать фикстуры для тестовых проектов
- [ ] Добавить тесты для GUI компонентов
- [ ] Настроить coverage reporting
- [ ] Добавить тесты для утилит
- [ ] Настроить CI/CD для автоматического запуска тестов

---

**Статус:** 12/12 тестов (8 unit + 4 integration) ✅

**Примечание:** Integration-тесты требуют установленных инструментов 1С (см. `tests/integration/README.md`)

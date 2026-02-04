# Технологический стек

## Язык и среда выполнения

- **Python 3.7+** - Основной язык
- **1С:Предприятие** - Инструменты конвертации (designer, ibcmd, 1cedtcli/ring)

## Зависимости

### Основные
- `FreeSimpleGUI>=5.2.0` - GUI фреймворк (open-source альтернатива PySimpleGUI)

### Для разработки
- `pytest>=7.0.0` - Фреймворк для тестирования
- `pytest-cov>=4.0.0` - Отчеты о покрытии кода
- `pytest-mock>=3.10.0` - Поддержка моков
- `black>=23.0.0` - Форматирование кода
- `flake8>=6.0.0` - Линтинг
- `mypy>=1.0.0` - Проверка типов
- `pylint>=2.17.0` - Анализ кода

## Система сборки

Система сборки не требуется - чистое Python приложение.

## Основные команды

### Установка
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Для разработки
```

### Запуск приложения
```bash
# Режим GUI
python src/gui/main.py
run_gui.cmd  # Ярлык для Windows
./run_gui.sh # Ярлык для Linux/Mac

# Режим CLI
python src/core/convert.py --env projects/MyProject
python src/core/convert.py --env projects/MyProject --output /path/to/output
```

### Тестирование
```bash
# Запуск всех тестов
pytest tests/

# Только юнит-тесты
pytest tests/unit/

# Только интеграционные тесты
pytest tests/integration/

# С покрытием кода
pytest --cov=src tests/
```

### Качество кода
```bash
# Форматирование кода
black src/

# Проверка форматирования
black src/ --check

# Линтинг
flake8 src/
pylint src/

# Проверка типов
mypy src/
```

## Особенности платформы

- **Основная платформа**: Windows (использует инструменты 1С для конвертаций)
- **Цвета в консоли**: ANSI escape коды с включением режима консоли Windows
- **Кодировки**: UTF-8 для Python файлов, CP1251/CP866 для вывода subprocess
- **Работа с путями**: Используется `pathlib.Path` для кроссплатформенности

## Архитектура конвертеров

### Базовые компоненты

**BaseConverter** - абстрактный базовый класс:
- Валидация параметров из .env файлов
- Управление временными файлами
- Определение типа источника (EDT/XML/InfoBase)
- Единообразное логирование на русском языке
- Обработка ошибок с сохранением временных файлов

**ConverterRegistry** - реестр конвертеров:
- Автоматическое обнаружение всех конвертеров
- Регистрация по типу конвертации (ScriptName из .env)
- Получение конвертера по имени

**Tool Wrappers** - абстракции инструментов 1С:
- `V8ToolWrapper` - работа с 1cv8.exe (designer)
- `IbcmdToolWrapper` - работа с ibcmd.exe
- `EdtToolWrapper` - работа с 1cedtcli/ring

### Специализированные конвертеры

- `ConfigurationConverter` - конфигурации (EDT/XML/IB → CF)
- `DataProcessorConverter` - обработки/отчеты (EDT/XML → EPF/ERF)
- `ExtensionConverter` - расширения (EDT/XML/IB → CFE)
- `ValidationConverter` - валидация EDT проектов

### Формат .env файлов

**Важно:** В параметре `ScriptName` указывается тип конвертации **без расширения .cmd**:

```bash
# Правильно (новый формат)
ScriptName=conf2cf
ScriptName=dp2epf
ScriptName=ext2cfe

# Неправильно (старый формат)
ScriptName=conf2cf.cmd  # Не работает!
```

### Примеры использования

**Через CLI:**
```bash
python src/core/convert.py --env projects/MyProject
```

**Через Python API:**
```python
from converters.registry import ConverterRegistry

# Получение конвертера
registry = ConverterRegistry()
converter_class = registry.get_converter('conf2cf')

# Создание и запуск
converter = converter_class(env_vars)
converter.validate()
converter.convert()
converter.cleanup()
```

**Прямое использование:**
```python
from converters.configuration.converter import ConfigurationConverter

converter = ConfigurationConverter(env_vars)
converter.validate()
result = converter.convert()
```

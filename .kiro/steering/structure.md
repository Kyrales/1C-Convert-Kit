# Структура проекта

## Корневая структура

```
1c-convert-kit/
├── src/              # Исходный код приложения
├── projects/         # Рабочие проекты пользователя с .env файлами
├── tests/            # Тесты (unit и integration)
├── docs/             # Документация
├── logs/             # Логи выполнения конвертаций
├── temp/             # Временные файлы
└── build/            # Артефакты сборки
```

## Структура src/

### src/gui/
GUI модули на базе FreeSimpleGUI:
- `main.py` - главный файл GUI с классами `CyberpunkGUI`, `ProjectScanner`, `ConversionRunner`
- Использует Cyberpunk цветовую схему
- Работает с таблицами проектов и деталями .env файлов

### src/core/
Ядро системы конвертации:
- `convert.py` - основная логика конвертации
  - Функции загрузки и объединения .env файлов
  - Интеграция с ConverterRegistry
  - Валидация путей и параметров
  - CLI интерфейс

### src/converters/
Модульная система конвертеров на Python:

#### Базовый слой (base/)
- `converter.py` - BaseConverter (абстрактный базовый класс)
  - Logger - единообразное логирование
  - SourceType - enum типов источников
  - SourceDetector - определение типа источника
  - TempFileManager - управление временными файлами
  - ToolOutputParser - парсинг вывода инструментов
- `tools.py` - абстракции инструментов 1С
  - ToolWrapper - базовый класс
  - V8ToolWrapper - работа с 1cv8.exe (designer)
  - IbcmdToolWrapper - работа с ibcmd.exe
  - EdtToolWrapper - работа с 1cedtcli/ring

#### Реестр конвертеров
- `registry.py` - ConverterRegistry
  - Автоматическое обнаружение конвертеров
  - Регистрация по типу конвертации (conf2cf, dp2epf, ext2cfe и т.д.)
  - Получение конвертера по ScriptName из .env

#### Специализированные конвертеры
- `configuration/` - конвертация конфигураций
  - `converter.py` - ConfigurationConverter (EDT/XML/IB → CF)
  - `legacy/` - устаревшие CMD скрипты (сохранены для истории)
  
- `dataprocessor/` - конвертация обработок и отчетов
  - `converter.py` - DataProcessorConverter (EDT/XML → EPF/ERF)
  - `legacy/` - устаревшие CMD скрипты
  
- `extension/` - конвертация расширений
  - `converter.py` - ExtensionConverter (EDT/XML/IB → CFE)
  - `legacy/` - устаревшие CMD скрипты
  
- `validation/` - валидация EDT проектов
  - `converter.py` - ValidationConverter
  - `legacy/` - устаревшие CMD скрипты

**Примечание:** Legacy CMD скрипты больше не используются, сохранены только для истории.

### src/config/
Конфигурационные файлы:
- `base.env.template` - шаблон базовой конфигурации
- `params_descriptions.json` - описания параметров .env файлов для GUI

### src/utils/
Утилиты (пока пустая, зарезервирована для будущего функционала)

## Структура projects/

Каждый проект - это папка с:
- `.env` файлом с параметрами конвертации
- Исходными файлами 1С (опционально)

Пример:
```
projects/
├── base_1.env                    # Базовая конфигурация (общие параметры)
├── МойПроект/
│   └── project.env               # Специфичные параметры проекта
└── ДругойПроект/
    └── config.env
```

### Приоритет конфигураций
1. Базовый .env из корня `projects/` (если есть)
2. .env файл проекта (переопределяет базовые параметры)

## Структура tests/

```
tests/
├── unit/                         # Юнит-тесты
│   ├── test_params_descriptions.py
│   └── test_details_table.py
├── integration/                  # Интеграционные тесты
│   └── test_convert_integration.py
└── fixtures/                     # Тестовые данные
    ├── cf/                       # Тестовые конфигурации
    ├── cfe/                      # Тестовые расширения
    └── *.env                     # Тестовые конфигурационные файлы
```

## Ключевые паттерны

### Импорты
- Используются относительные импорты: `from ..core.convert import load_env_file`
- Пути вычисляются относительно корня проекта через `Path(__file__).parent`

### Пути
```python
SCRIPT_DIR = Path(__file__).parent.parent.parent  # Корень проекта
PROJECTS_DIR = SCRIPT_DIR / 'projects'
CONVERT_SCRIPT = SCRIPT_DIR / 'src' / 'core' / 'convert.py'
```

### Поиск конвертеров
Система использует ConverterRegistry для автоматического обнаружения конвертеров:
```python
from converters.registry import ConverterRegistry

registry = ConverterRegistry()
converter_class = registry.get_converter('conf2cf')  # Получение по ScriptName
```

Маппинг типов конвертации:
- `conf2cf`, `conf2xml`, `conf2edt` → ConfigurationConverter
- `dp2epf`, `dp2erf`, `dp2xml`, `dp2edt` → DataProcessorConverter
- `ext2cfe`, `ext2xml`, `ext2edt` → ExtensionConverter
- `edt-validate` → ValidationConverter

### Обработка кодировок
- Файлы Python: UTF-8
- Вывод subprocess: CP1251/CP866/UTF-8 с fallback
- ANSI escape коды удаляются из вывода

## Соглашения по именованию

### Файлы
- Python модули: `snake_case.py`
- Конфигурационные файлы: `*.env`

**Примечание:** CMD скрипты больше не используются в новой архитектуре.

### Классы
- `PascalCase` (например: `CyberpunkGUI`, `ProjectScanner`)

### Функции и переменные
- `snake_case` (например: `load_env_file`, `run_conversion`)

### Константы
- `UPPER_SNAKE_CASE` (например: `SCRIPT_DIR`, `COLORS`)

## Примеры использования ConverterRegistry

### Базовое использование
```python
from converters.registry import ConverterRegistry

# Создание реестра (автоматически находит все конвертеры)
registry = ConverterRegistry()

# Получение списка доступных конвертеров
available = registry.list_converters()
print(available)  # ['conf2cf', 'conf2xml', 'dp2epf', 'ext2cfe', ...]

# Получение конвертера по типу
converter_class = registry.get_converter('conf2cf')
if converter_class:
    converter = converter_class(env_vars)
    converter.validate()
    converter.convert()
    converter.cleanup()
```

### Использование в convert.py
```python
def run_conversion(env_files, output_path=None):
    # Загрузка .env файлов
    env_vars = merge_env_files(env_files)
    
    # Получение типа конвертации из ScriptName
    script_name = env_vars.get('ScriptName')  # Например: 'conf2cf'
    
    # Получение конвертера из реестра
    registry = ConverterRegistry()
    converter_class = registry.get_converter(script_name)
    
    # Создание и запуск конвертера
    converter = converter_class(env_vars)
    converter.validate()
    exit_code = converter.convert()
    
    if exit_code == 0:
        converter.cleanup()
    
    return exit_code
```

### Прямое использование конвертера
```python
from converters.configuration.converter import ConfigurationConverter

# Подготовка параметров
env_vars = {
    'V8_SRC_PATH': '/path/to/edt/project',
    'V8_DST_PATH': '/path/to/output.cf',
    'V8_VERSION': '8.3.27.1989',
    # ... другие параметры
}

# Создание и запуск конвертера
converter = ConfigurationConverter(env_vars)
converter.validate()
result = converter.convert()

if result == 0:
    print("Конвертация успешна!")
    converter.cleanup()
else:
    print("Ошибка конвертации")
    # Временные файлы сохранены для отладки
```

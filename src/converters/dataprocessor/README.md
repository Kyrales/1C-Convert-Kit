# DataProcessorConverter

Конвертер для обработок и отчетов 1С:Предприятие.

## Назначение

Конвертирует внешние обработки (EPF) и отчеты (ERF) между форматами:
- EDT → EPF/ERF
- XML → EPF/ERF

## Особенности

- **Множественные файлы**: Автоматически находит и конвертирует все обработки и отчеты в проекте
- **Базовая ИБ**: Поддерживает использование существующей ИБ или создание новой с конфигурацией
- **Автоопределение типа**: Автоматически определяет обработки (.epf) и отчеты (.erf)

## Параметры .env файла

### Обязательные параметры

- `V8_SRC_PATH` - путь к источнику (EDT проект или XML директория)
- `V8_DST_PATH` - путь к директории для выходных файлов (не файл!)
- `ScriptName` - тип конвертации (`dp2epf`, `dp2erf`, `dp2xml`, `dp2edt`)

### Опциональные параметры

- `V8_BASE_IB` - путь к существующей базовой ИБ (если нужна конфигурация для обработок)
- `V8_BASE_CONFIG` - путь к XML конфигурации для создания базовой ИБ
- `V8_TOOL` - путь к 1cv8.exe (если не в стандартном месте)
- `V8_VERSION` - версия платформы 1С (по умолчанию 8.3.23.2040)
- `V8_TEMP` - директория для временных файлов

## Примеры использования

### Пример 1: Конвертация EDT → EPF/ERF

```env
# project.env
ScriptName=dp2epf
V8_SRC_PATH=C:/Projects/MyProject/ExternalDataProcessors
V8_DST_PATH=C:/Output/Processors
V8_BASE_IB=C:/InfoBases/BaseIB
```

Запуск:
```bash
python src/core/convert.py --env projects/MyProject/project.env
```

### Пример 2: Конвертация XML → EPF/ERF с созданием базовой ИБ

```env
# project.env
ScriptName=dp2epf
V8_SRC_PATH=C:/Projects/MyProject/XML
V8_DST_PATH=C:/Output/Processors
V8_BASE_CONFIG=C:/Configs/BaseConfig/Configuration.xml
```

### Пример 3: Конвертация без базовой конфигурации

```env
# project.env
ScriptName=dp2epf
V8_SRC_PATH=C:/Projects/MyProject/XML
V8_DST_PATH=C:/Output/Processors
```

## Структура источника

### Для EDT проектов

```
MyProject/
├── DT-INF/
├── ExternalDataProcessors/
│   ├── Processor1.xml
│   └── Processor2.xml
└── ExternalReports/
    ├── Report1.xml
    └── Report2.xml
```

### Для XML директорий

```
XML/
├── ExternalDataProcessors/
│   ├── Processor1.xml
│   └── Processor2.xml
└── ExternalReports/
    ├── Report1.xml
    └── Report2.xml
```

## Результат конвертации

Все обработки и отчеты будут сконвертированы в указанную директорию:

```
Output/
├── Processor1.epf
├── Processor2.epf
├── Report1.erf
└── Report2.erf
```

## Логика работы с базовой ИБ

Конвертер использует следующую логику для подготовки базовой ИБ:

1. **Если указан `V8_BASE_IB`**: Использует существующую ИБ
2. **Если указан `V8_BASE_CONFIG`**: Создает временную ИБ и загружает конфигурацию
3. **Иначе**: Создает пустую временную ИБ

## Обработка ошибок

При ошибке конвертации:
- Временные файлы сохраняются для отладки
- Путь к временным файлам выводится в консоль
- Возвращается код ошибки 1

## Логирование

Конвертер выводит подробную информацию о процессе:
- Тип источника
- Найденные обработки и отчеты
- Прогресс конвертации каждого файла
- Результаты создания выходных файлов

## Использование в коде

```python
from src.converters.dataprocessor import DataProcessorConverter

# Создание конвертера
env_vars = {
    'V8_SRC_PATH': '/path/to/edt/project',
    'V8_DST_PATH': '/path/to/output',
    'V8_BASE_IB': '/path/to/base/ib'
}

converter = DataProcessorConverter(env_vars, silent=False)

# Валидация параметров
converter.validate()

# Выполнение конвертации
exit_code = converter.convert()

# Очистка временных файлов (если успешно)
if exit_code == 0:
    converter.cleanup()
```

## Требования

- Python 3.7+
- Платформа 1С:Предприятие 8.3+
- EDT (для конвертации из EDT проектов)
- Достаточно места на диске для временных файлов

## См. также

- [ConfigurationConverter](../configuration/README.md) - конвертер конфигураций
- [ExtensionConverter](../extension/README.md) - конвертер расширений
- [Базовые классы](../base/README.md) - общая документация по архитектуре

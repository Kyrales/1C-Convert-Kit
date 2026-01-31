# Конвертер расширений 1С

## Описание

`ExtensionConverter` - конвертер для работы с расширениями 1С:Предприятие.

## Поддерживаемые форматы

### Входные форматы:
- **EDT** - проект 1C:Enterprise Development Tools
- **XML** - XML файлы расширения
- **InfoBase** - информационная база с расширением

### Выходной формат:
- **CFE** - файл расширения конфигурации (.cfe)

## Обязательные параметры

- `V8_SRC_PATH` - путь к источнику (EDT проект, XML файлы или ИБ)
- `V8_DST_PATH` - путь к выходному .cfe файлу
- `V8_EXT_NAME` - имя расширения (обязательно!)

## Опциональные параметры

- `V8_BASE_IB` - путь к базовой информационной базе
- `V8_BASE_CONFIG` - путь к базовой конфигурации (для создания ИБ)
- `V8_CONVERT_TOOL` - инструмент конвертации (`designer` или `ibcmd`, по умолчанию `designer`)
- `V8_TOOL` - путь к 1cv8.exe
- `V8_VERSION` - версия платформы 1С (по умолчанию `8.3.23.2040`)
- `IBCMD_TOOL` - путь к ibcmd.exe
- `RING_TOOL` - путь к ring.bat
- `EDT_TOOL` - путь к 1cedtcli.exe

## Примеры использования

### Пример 1: EDT → CFE

```env
ScriptName=ext2cfe
V8_SRC_PATH=C:/Projects/MyExtension
V8_DST_PATH=C:/Output/MyExtension.cfe
V8_EXT_NAME=МоеРасширение
V8_BASE_CONFIG=C:/Configs/BaseConfig
```

### Пример 2: XML → CFE

```env
ScriptName=ext2cfe
V8_SRC_PATH=C:/XML/MyExtension
V8_DST_PATH=C:/Output/MyExtension.cfe
V8_EXT_NAME=МоеРасширение
V8_BASE_IB=C:/InfoBases/Base
```

### Пример 3: IB → CFE

```env
ScriptName=ext2cfe
V8_SRC_PATH=/FC:/InfoBases/MyBase
V8_DST_PATH=C:/Output/MyExtension.cfe
V8_EXT_NAME=МоеРасширение
```

## Последовательность конвертации

### EDT → CFE
1. Экспорт EDT проекта в XML (через ring/edtcli)
2. Подготовка базовой ИБ (создание или использование существующей)
3. Загрузка расширения из XML в ИБ
4. Выгрузка расширения из ИБ в CFE файл

### XML → CFE
1. Подготовка базовой ИБ
2. Загрузка расширения из XML в ИБ
3. Выгрузка расширения из ИБ в CFE файл

### IB → CFE
1. Выгрузка расширения из ИБ в CFE файл

## Особенности

- **Обязательный параметр V8_EXT_NAME**: Имя расширения должно быть указано явно
- **Базовая ИБ**: Для загрузки расширения требуется базовая конфигурация. Можно указать существующую ИБ (`V8_BASE_IB`) или конфигурацию для создания новой ИБ (`V8_BASE_CONFIG`)
- **Временные файлы**: При ошибке временные файлы сохраняются для отладки
- **Логирование**: Все этапы конвертации логируются с цветным выводом

## Обработка ошибок

При возникновении ошибки:
1. Выводится подробное сообщение об ошибке
2. Временные файлы сохраняются в директории, указанной в `V8_TEMP`
3. Путь к временным файлам выводится в консоль
4. Возвращается код ошибки 1

## Использование в коде

```python
from converters.extension import ExtensionConverter

env_vars = {
    'V8_SRC_PATH': 'C:/Projects/MyExtension',
    'V8_DST_PATH': 'C:/Output/MyExtension.cfe',
    'V8_EXT_NAME': 'МоеРасширение',
    'V8_BASE_CONFIG': 'C:/Configs/BaseConfig'
}

converter = ExtensionConverter(env_vars)
converter.validate()
result = converter.convert()
converter.cleanup()
```

## См. также

- [ConfigurationConverter](../configuration/README.md) - конвертер конфигураций
- [DataProcessorConverter](../dataprocessor/README.md) - конвертер обработок/отчетов
- [ValidationConverter](../validation/README.md) - валидатор EDT проектов

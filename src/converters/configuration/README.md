# Конвертер конфигураций 1С

## Описание

`ConfigurationConverter` - конвертер для работы с конфигурациями 1С:Предприятие.

## Поддерживаемые форматы

### Входные форматы:
- **EDT** - проект 1C:Enterprise Development Tools
- **XML** - XML файлы конфигурации
- **InfoBase** - информационная база с конфигурацией

### Выходные форматы:
- **CF** - файл конфигурации (.cf)
- **XML** - XML файлы конфигурации
- **EDT** - проект EDT

## Обязательные параметры

- `V8_SRC_PATH` - путь к источнику (EDT проект, XML файлы или ИБ)
- `V8_DST_PATH` - путь к выходному файлу/директории
- `ScriptName` - тип конвертации (`conf2cf`, `conf2xml`, `conf2edt`)

## Опциональные параметры

- `V8_BASE_IB` - путь к базовой информационной базе
- `V8_BASE_CONFIG` - путь к базовой конфигурации (для создания ИБ)
- `V8_CONVERT_TOOL` - инструмент конвертации (`designer` или `ibcmd`, по умолчанию `designer`)
- `V8_TOOL` - путь к 1cv8.exe
- `V8_VERSION` - версия платформы 1С (по умолчанию `8.3.27.1989`)
- `IBCMD_TOOL` - путь к ibcmd.exe
- `RING_TOOL` - путь к ring.bat
- `EDT_TOOL` - путь к 1cedtcli.exe
- `V8_EDT_VERSION` - версия EDT (по умолчанию `2025.1.5`)
- `V8_TEMP` - директория для временных файлов

## Примеры использования

### Пример 1: EDT → CF

```env
ScriptName=conf2cf
V8_SRC_PATH=C:/Projects/MyConfiguration
V8_DST_PATH=C:/Output/MyConfiguration.cf
V8_VERSION=8.3.27.1989
```

### Пример 2: XML → CF

```env
ScriptName=conf2cf
V8_SRC_PATH=C:/XML/MyConfiguration
V8_DST_PATH=C:/Output/MyConfiguration.cf
V8_BASE_IB=C:/InfoBases/Base
```

### Пример 3: IB → CF

```env
ScriptName=conf2cf
V8_SRC_PATH=/FC:/InfoBases/MyBase
V8_DST_PATH=C:/Output/MyConfiguration.cf
```

### Пример 4: EDT → XML

```env
ScriptName=conf2xml
V8_SRC_PATH=C:/Projects/MyConfiguration
V8_DST_PATH=C:/Output/XML
```

### Пример 5: CF → EDT

```env
ScriptName=conf2edt
V8_SRC_PATH=C:/Configs/MyConfiguration.cf
V8_DST_PATH=C:/Projects/MyConfiguration
```

## Последовательность конвертации

### EDT → CF
1. Экспорт EDT проекта в XML (через 1cedtcli/ring)
2. Создание временной информационной базы
3. Загрузка конфигурации из XML в ИБ
4. Выгрузка конфигурации из ИБ в CF файл

### XML → CF
1. Создание временной информационной базы
2. Загрузка конфигурации из XML в ИБ
3. Выгрузка конфигурации из ИБ в CF файл

### IB → CF
1. Выгрузка конфигурации из ИБ в CF файл

### EDT → XML
1. Экспорт EDT проекта в XML (через 1cedtcli/ring)

### CF → EDT
1. Создание временной информационной базы
2. Загрузка конфигурации из CF в ИБ
3. Выгрузка конфигурации из ИБ в XML
4. Импорт XML в EDT проект (через 1cedtcli/ring)

## Особенности

- **Автоопределение типа источника**: Конвертер автоматически определяет формат источника (EDT/XML/IB)
- **Гибкий выбор инструмента**: Поддержка как designer (1cv8.exe), так и ibcmd для работы с ИБ
- **Временные файлы**: При ошибке временные файлы сохраняются для отладки
- **Логирование**: Все этапы конвертации логируются с цветным выводом
- **Базовая ИБ**: Можно использовать существующую ИБ или создать новую

## Выбор инструмента конвертации

Параметр `V8_CONVERT_TOOL` определяет какой инструмент использовать:

### designer (по умолчанию)
- Использует 1cv8.exe
- Более стабильный
- Поддерживает все операции
- Требует GUI (может быть проблемой на серверах)

```env
V8_CONVERT_TOOL=designer
V8_TOOL=C:/Program Files/1cv8/8.3.27.1989/bin/1cv8.exe
```

### ibcmd
- Использует ibcmd.exe
- Консольный инструмент (не требует GUI)
- Быстрее для простых операций
- Ограниченная функциональность

```env
V8_CONVERT_TOOL=ibcmd
IBCMD_TOOL=C:/Program Files/1cv8/common/ibcmd.exe
```

## Работа с базовой ИБ

Для некоторых операций требуется базовая информационная база:

### Использование существующей ИБ:
```env
V8_BASE_IB=/FC:/InfoBases/BaseIB
```

### Создание новой ИБ с конфигурацией:
```env
V8_BASE_CONFIG=C:/Configs/BaseConfig.cf
# или
V8_BASE_CONFIG=C:/Configs/BaseConfig/Configuration.xml
```

### Создание пустой ИБ:
Если не указаны `V8_BASE_IB` и `V8_BASE_CONFIG`, создается пустая временная ИБ.

## Обработка ошибок

При возникновении ошибки:
1. Выводится подробное сообщение об ошибке
2. Временные файлы сохраняются в директории, указанной в `V8_TEMP`
3. Путь к временным файлам выводится в консоль
4. Возвращается код ошибки 1

## Использование в коде

```python
from converters.configuration import ConfigurationConverter

env_vars = {
    'V8_SRC_PATH': 'C:/Projects/MyConfiguration',
    'V8_DST_PATH': 'C:/Output/MyConfiguration.cf',
    'V8_VERSION': '8.3.27.1989'
}

converter = ConfigurationConverter(env_vars)
converter.validate()
result = converter.convert()

if result == 0:
    converter.cleanup()
```

## Использование через CLI

```bash
# Конвертация одного проекта
python src/core/convert.py --env projects/MyProject/project.env

# Конвертация с базовой конфигурацией
python src/core/convert.py --env projects/base.env --env projects/MyProject/project.env

# Конвертация с указанием выходного пути
python src/core/convert.py --env projects/MyProject/project.env --output C:/Output
```

## Использование через GUI

1. Запустите GUI приложение:
   ```bash
   python src/gui/main.py
   # или
   run_gui.cmd  # Windows
   ./run_gui.sh # Linux/Mac
   ```

2. Выберите проект в таблице
3. Нажмите "Запустить конвертацию"
4. Следите за прогрессом в окне логов

## Структура проекта

### EDT проект:
```
MyConfiguration/
├── DT-INF/
│   ├── PROJECT.PMF
│   └── Configuration.xml
├── .project
└── src/
    ├── Configuration/
    ├── Catalogs/
    ├── Documents/
    └── ...
```

### XML директория:
```
MyConfiguration/
├── Configuration.xml
├── Catalogs/
├── Documents/
└── ...
```

### Информационная база:
```
/FC:/InfoBases/MyBase
# или
C:/InfoBases/MyBase/1Cv8.1CD
```

## Логирование

Конвертер выводит подробную информацию о процессе:

```
[ИНФО] Начало конвертации...
[ИНФО] Конвертация конфигурации: EDT → CF
[ИНФО] Тип источника: edt
[ИНФО] EDT проект найден: C:/Projects/MyConfiguration
[ИНФО] Экспорт EDT проекта в XML...
[ИНФО] Создание временной информационной базы...
[ИНФО] Загрузка конфигурации из XML...
[ИНФО] Выгрузка конфигурации в CF...
[УСПЕХ] Конфигурация успешно выгружена: C:/Output/MyConfiguration.cf
[УСПЕХ] Конвертация завершена успешно
```

## Требования

- Python 3.7+
- Платформа 1С:Предприятие 8.3+
- EDT (для конвертации из/в EDT проекты)
- Достаточно места на диске для временных файлов

## Производительность

Время конвертации зависит от:
- Размера конфигурации
- Типа источника и назначения
- Производительности диска
- Версии платформы 1С

Примерное время для конфигурации среднего размера:
- EDT → CF: 2-5 минут
- XML → CF: 1-3 минуты
- IB → CF: 30 секунд - 1 минута

## Отладка

При возникновении проблем:

1. Проверьте логи в директории `logs/`
2. Проверьте временные файлы (путь выводится при ошибке)
3. Убедитесь что все пути корректны
4. Проверьте версию платформы 1С
5. Попробуйте другой инструмент конвертации (designer/ibcmd)

## Известные ограничения

- Конвертация IB → EDT требует промежуточного шага через XML
- ibcmd не поддерживает все операции designer
- EDT инструменты требуют установленного EDT
- Большие конфигурации могут требовать много места для временных файлов

## См. также

- [DataProcessorConverter](../dataprocessor/README.md) - конвертер обработок/отчетов
- [ExtensionConverter](../extension/README.md) - конвертер расширений
- [ValidationConverter](../validation/README.md) - валидатор EDT проектов
- [Базовые классы](../base/README.md) - общая документация по архитектуре

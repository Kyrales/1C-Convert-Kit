# Руководство по миграции на версию 2.0

## Обзор изменений

Версия 2.0 представляет полный рефакторинг системы конвертации с переходом от CMD скриптов к объектно-ориентированной Python архитектуре.

## Критические изменения

### ⚠️ Формат .env файлов

**Это изменение ОБЯЗАТЕЛЬНО для всех пользователей!**

#### Старый формат (НЕ РАБОТАЕТ в версии 2.0):
```bash
ScriptName=conf2cf.cmd
ScriptName=dp2epf.cmd
ScriptName=ext2cfe.cmd
ScriptName=edt-validate.cmd
```

#### Новый формат (ОБЯЗАТЕЛЬНО):
```bash
ScriptName=conf2cf
ScriptName=dp2epf
ScriptName=ext2cfe
ScriptName=edt-validate
```

**Причина:** Система больше не использует CMD скрипты. Параметр `ScriptName` теперь указывает на тип конвертации, а не на файл скрипта.

## Пошаговая инструкция по миграции

### Шаг 1: Резервное копирование

Создайте резервную копию ваших .env файлов:

```bash
# Windows
xcopy projects\*.env projects_backup\ /s /e

# Linux/Mac
cp -r projects projects_backup
```

### Шаг 2: Найдите все .env файлы

```bash
# Windows
dir /s /b *.env

# Linux/Mac
find . -name "*.env"
```

### Шаг 3: Обновите каждый .env файл

Откройте каждый .env файл и удалите `.cmd` из параметра `ScriptName`:

**Примеры замены:**

| Было | Стало |
|------|-------|
| `ScriptName=conf2cf.cmd` | `ScriptName=conf2cf` |
| `ScriptName=conf2xml.cmd` | `ScriptName=conf2xml` |
| `ScriptName=conf2edt.cmd` | `ScriptName=conf2edt` |
| `ScriptName=conf2ib.cmd` | `ScriptName=conf2ib` |
| `ScriptName=dp2epf.cmd` | `ScriptName=dp2epf` |
| `ScriptName=dp2erf.cmd` | `ScriptName=dp2erf` |
| `ScriptName=dp2xml.cmd` | `ScriptName=dp2xml` |
| `ScriptName=dp2edt.cmd` | `ScriptName=dp2edt` |
| `ScriptName=ext2cfe.cmd` | `ScriptName=ext2cfe` |
| `ScriptName=ext2xml.cmd` | `ScriptName=ext2xml` |
| `ScriptName=ext2edt.cmd` | `ScriptName=ext2edt` |
| `ScriptName=ext2ib.cmd` | `ScriptName=ext2ib` |
| `ScriptName=edt-validate.cmd` | `ScriptName=edt-validate` |

### Шаг 4: Добавьте комментарии (рекомендуется)

Добавьте в начало каждого .env файла комментарий:

```bash
# ВАЖНО: ScriptName указывается БЕЗ расширения .cmd
# Правильно: ScriptName=conf2cf
# Неправильно: ScriptName=conf2cf.cmd
```

### Шаг 5: Проверьте работу

Запустите конвертацию для проверки:

```bash
python src/core/convert.py --env projects/YourProject
```

**Ожидаемый результат:** Конвертация должна работать как раньше.

**Если видите ошибку:**
```
Конвертер для 'conf2cf.cmd' не найден
```
Значит вы забыли убрать `.cmd` из ScriptName в этом .env файле.

## Изменения в архитектуре

### Что удалено

1. **CMD скрипты** - больше не используются
   - `conf2cf.cmd`, `conf2xml.cmd`, `conf2edt.cmd`, `conf2ib.cmd`
   - `dp2epf.cmd`, `dp2erf.cmd`, `dp2xml.cmd`, `dp2edt.cmd`
   - `ext2cfe.cmd`, `ext2xml.cmd`, `ext2edt.cmd`, `ext2ib.cmd`
   - `edt-validate.cmd`

2. **Функции в convert.py**
   - `find_legacy_script()` - удалена
   - Код запуска CMD через subprocess - удален

### Что добавлено

1. **BaseConverter** - абстрактный базовый класс
   - Валидация параметров
   - Управление временными файлами
   - Определение типа источника
   - Единообразное логирование
   - Обработка ошибок

2. **ConverterRegistry** - реестр конвертеров
   - Автоматическое обнаружение конвертеров
   - Регистрация по типу конвертации
   - Получение конвертера по ScriptName

3. **Tool Wrappers** - абстракции инструментов
   - `V8ToolWrapper` - работа с 1cv8.exe
   - `IbcmdToolWrapper` - работа с ibcmd.exe
   - `EdtToolWrapper` - работа с ring/edtcli

4. **Специализированные конвертеры**
   - `ConfigurationConverter` - конфигурации
   - `DataProcessorConverter` - обработки/отчеты
   - `ExtensionConverter` - расширения
   - `ValidationConverter` - валидация EDT

### Что осталось без изменений

1. **CLI интерфейс** - работает как раньше
   ```bash
   python src/core/convert.py --env projects/MyProject
   python src/core/convert.py --env projects/MyProject --output /path/to/output
   ```

2. **Структура .env файлов** - все параметры остались прежними (кроме ScriptName)
   - `V8_SRC_PATH`, `V8_DST_PATH`
   - `V8_VERSION`, `V8_EDT_VERSION`
   - `V8_TOOL`, `EDTCLI_TOOL`, `RING_TOOL`
   - `V8_EXT_NAME`, `V8_BASE_CONFIG`, `V8_BASE_IB`
   - И все остальные параметры

3. **GUI интерфейс** - работает как раньше

4. **Функции работы с .env**
   - `load_env_file()` - без изменений
   - `merge_env_files()` - без изменений

## Миграция пользовательского кода

### Если вы использовали только CLI

**Никаких изменений не требуется!** Просто обновите .env файлы как описано выше.

### Если вы импортировали convert.py в свой код

#### Старый код:
```python
from src.core.convert import run_conversion

# Это продолжает работать без изменений
result = run_conversion(['projects/base.env', 'projects/project.env'])
```

**Изменений не требуется!** Функция `run_conversion()` работает как раньше.

#### Новые возможности:

Теперь вы можете использовать конвертеры напрямую:

```python
from converters.registry import ConverterRegistry

# Получение конвертера
registry = ConverterRegistry()
converter_class = registry.get_converter('conf2cf')

# Создание и запуск
converter = converter_class(env_vars)
converter.validate()
result = converter.convert()

if result == 0:
    converter.cleanup()
```

Или напрямую:

```python
from converters.configuration.converter import ConfigurationConverter

converter = ConfigurationConverter(env_vars)
converter.validate()
result = converter.convert()
```

### Если вы вызывали CMD скрипты напрямую

#### Старый код (НЕ РАБОТАЕТ):
```python
import subprocess

subprocess.run(['cmd', '/c', 'src/converters/configuration/legacy/conf2cf.cmd'])
```

#### Новый код:
```python
from converters.configuration.converter import ConfigurationConverter

env_vars = {
    'V8_SRC_PATH': '/path/to/source',
    'V8_DST_PATH': '/path/to/output.cf',
    # ... другие параметры
}

converter = ConfigurationConverter(env_vars)
converter.validate()
result = converter.convert()

if result == 0:
    print("Успех!")
    converter.cleanup()
else:
    print("Ошибка!")
```

## Преимущества новой архитектуры

### Для пользователей

1. **Та же функциональность** - все работает как раньше
2. **Лучшая обработка ошибок** - понятные сообщения на русском
3. **Сохранение временных файлов** - при ошибке файлы сохраняются для отладки
4. **Та же производительность** - скорость не изменилась

### Для разработчиков

1. **Нет дублирования кода** - общая логика в BaseConverter
2. **Легко добавлять конвертеры** - один класс, автоматическая регистрация
3. **Лучшая тестируемость** - unit-тесты для каждого компонента
4. **Модульность** - каждый компонент независим
5. **Python API** - можно использовать конвертеры программно

## Устранение проблем

### Ошибка: "Конвертер для 'XXX.cmd' не найден"

**Причина:** В .env файле ScriptName указан с расширением .cmd

**Решение:** Удалите .cmd из ScriptName:
```bash
# Было
ScriptName=conf2cf.cmd

# Должно быть
ScriptName=conf2cf
```

### Ошибка: "Переменная ScriptName не определена"

**Причина:** В .env файле отсутствует параметр ScriptName

**Решение:** Добавьте ScriptName в .env файл:
```bash
ScriptName=conf2cf  # или другой тип конвертации
```

### Конвертация не работает

**Проверьте:**

1. Формат ScriptName (без .cmd)
2. Наличие всех обязательных параметров (V8_SRC_PATH, V8_DST_PATH)
3. Существование путей источников
4. Логи в папке `logs/`
5. Временные файлы в папке `temp/` (сохраняются при ошибках)

### Где найти помощь

1. **Документация:**
   - `README.md` - основная документация
   - `MIGRATION_COMPLETE.md` - полный отчет о рефакторинге
   - `REFACTORING_SUMMARY.md` - краткая сводка
   - `.kiro/steering/*.md` - steering файлы

2. **Примеры:**
   - `tests/fixtures/*.env` - примеры .env файлов
   - `tests/integration/test_convert_integration.py` - примеры использования

3. **Legacy код:**
   - `src/converters/*/legacy/README.md` - информация о старых скриптах

## Обратная связь

Если вы обнаружили проблему или у вас есть вопросы:

1. Проверьте эту документацию
2. Проверьте `MIGRATION_COMPLETE.md`
3. Создайте issue в репозитории проекта

## Заключение

Миграция на версию 2.0 требует только одного изменения: удаление `.cmd` из параметра `ScriptName` в .env файлах.

Все остальное работает как раньше, но с улучшенной архитектурой, лучшей обработкой ошибок и возможностью программного использования.

**Удачной миграции!** 🚀

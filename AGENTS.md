# AGENTS.md

## Назначение проекта

`1C Convert Kit` - Python-приложение для конвертации артефактов `1С:Предприятие` между форматами `CF`, `CFE`, `EPF`, `ERF`, `XML`, `EDT` и для валидации EDT-проектов. Приложение поддерживает два основных сценария:

- GUI-режим для пакетной работы с проектами и `.env`-конфигурациями
- CLI/API-режим для запуска отдельных конвертаций через `src/core/convert.py`

Проект уже мигрировал с legacy `CMD`-скриптов на Python-конвертеры. Папки `legacy/` сохранены для истории и обратной сверки, но основной путь выполнения идет через Python-классы.

## Что важно понять в первую очередь

- Основная логика запуска находится в `src/core/convert.py`
- Выбор конвертера идет через `src/converters/registry.py`
- Общая инфраструктура конвертеров живет в `src/converters/base/`
- GUI разбит на несколько модулей в `src/gui/`, а не сосредоточен в одном файле
- Конфигурация строится вокруг `.env` файлов в `projects/` и `tests/fixtures/`
- `ScriptName` в актуальном формате указывается без `.cmd`

Примеры корректных значений:

- `conf2cf`
- `dp2epf`
- `ext2cfe`
- `edt-validate`

## Архитектурная модель

Проект следует направлению, описанному в `.kiro/steering` и спецификации `.kiro/specs/python-converters-refactoring`:

- единая Python-архитектура вместо дублирующихся `.cmd`-сценариев
- общий `BaseConverter` с шаблонным методом `convert()`
- специализированные конвертеры по типам объектов 1С
- `ConverterRegistry` как точка маршрутизации по `ScriptName`
- tool wrappers для работы с `1cv8.exe`, `ibcmd.exe`, `ring`/`1cedtcli`
- единое логирование на русском языке
- сохранение временных файлов для отладки при ошибках

Ключевые классы:

- `BaseConverter` - валидация, логирование, работа с temp, прогресс, общая обработка ошибок
- `ConfigurationConverter` - конвертации конфигураций
- `DataProcessorConverter` - конвертации обработок/отчетов
- `ExtensionConverter` - конвертации расширений
- `ValidationConverter` - проверка EDT-проектов
- `ConverterRegistry` - маппинг `ScriptName -> converter class`

## Актуальная структура репозитория

### Исходный код

- `src/core/convert.py` - загрузка `.env`, merge конфигураций, CLI, запуск конвертера
- `src/converters/registry.py` - регистрация и выдача конвертеров
- `src/converters/base/converter.py` - `Logger`, `SourceType`, `SourceDetector`, `TempFileManager`, исключения, `BaseConverter`
- `src/converters/base/tools.py` - обертки над внешними инструментами 1С
- `src/converters/base/ib_utils.py` - разбор ссылок на информационные базы
- `src/converters/configuration/converter.py` - конфигурации
- `src/converters/dataprocessor/converter.py` - обработки и отчеты
- `src/converters/extension/converter.py` - расширения
- `src/converters/validation/converter.py` - EDT validation

### GUI

- `src/gui/main.py` - точка входа GUI
- `src/gui/main_window.py` - главное окно
- `src/gui/conversion_runner.py` - запуск конвертаций из GUI
- `src/gui/project_scanner.py` - поиск и чтение проектных `.env`
- `src/gui/project_editor.py` - редактирование проектов
- `src/gui/constants.py`, `src/gui/utils.py`, `src/gui/sg_import.py` - вспомогательный слой GUI

### Конфигурация

- `src/config/base.env.template` - шаблон базовой конфигурации
- `src/config/params_descriptions.json` - описания параметров для GUI
- `src/config/params_depend.json` - зависимости параметров

### Тесты

- `tests/unit/` - unit-тесты конвертеров, GUI и служебной логики
- `tests/integration/` - интеграционные сценарии для `convert.py`
- `tests/fixtures/` - реальные EDT/XML/CF/CFE/EPF фикстуры и тестовые `.env`

## Правила работы с `.env`

- Базовая конфигурация может лежать в корне `projects/` как общий `.env`
- Проектные `.env` в подпапке проекта переопределяют базовые значения
- `merge_env_files()` объединяет файлы в порядке от базовых к проектным
- Файлы читаются с поддержкой `utf-8-sig`, `utf-8`, `cp1251`
- Комментарии и кавычки в значениях поддерживаются

Критично:

- `ScriptName` должен быть без расширения `.cmd`
- Источник задается через `V8_SRC_PATH`
- Назначение задается через `V8_DST_PATH`
- Для сохранения временных файлов после успеха используется `V8_TEMP_AFTER_CLEAN=0`

## Поддерживаемые типы конвертации

Сейчас в реестре зарегистрированы:

- `conf2cf`, `conf2xml`, `conf2edt`, `conf2ib`
- `dp2epf`, `dp2erf`, `dp2xml`, `dp2edt`
- `ext2cfe`, `ext2xml`, `ext2edt`, `ext2ib`
- `edt-validate`

Если добавляется новый тип конвертации, ожидаемый путь:

1. Добавить или расширить converter class
2. Зарегистрировать новый `ScriptName` в `ConverterRegistry`
3. При необходимости обновить GUI-описания параметров
4. Добавить unit/integration tests

## Технологии и внешние зависимости

- Python, фактически проект уже ориентирован на `Python 3.8+` по спецификации
- `FreeSimpleGUI` для GUI
- `pytest` для тестов
- `black`, `flake8`, `mypy`, `pylint` как dev tooling
- внешние 1С-инструменты: `1cv8.exe`, `ibcmd.exe`, `ring` или `1cedtcli`

Проект в первую очередь Windows-ориентирован, но часть кода написана кроссплатформенно через `pathlib`.

## Практические соглашения для изменений

- Сохранять текущую Python-архитектуру и не возвращать запуск через legacy `.cmd`
- Новую общую логику выносить в `base/`, а не дублировать между конвертерами
- Логирование оставлять на русском языке и через общий `Logger`
- Ошибки конвертации должны быть понятными и с контекстом для отладки
- При изменении маршрутизации обязательно проверять `ConverterRegistry`
- При изменении формата параметров синхронизировать `src/config/*.json`, шаблоны `.env` и тестовые фикстуры
- Не считать `.pyc`, `.pytest_cache` и build-артефакты источником истины

## На что смотреть при ревью или доработках

- не сломался ли merge базового и проектного `.env`
- не использует ли новый код `ScriptName` со старым `.cmd`-форматом
- не разошлись ли CLI и GUI по логике выбора конвертера
- не потерялась ли обработка кодировок `utf-8/cp1251/cp866`
- сохраняются ли временные файлы при ошибке
- покрыт ли новый тип конвертации тестами

## Полезные команды

```powershell
python src/gui/main.py
python src/core/convert.py --env projects\MyProject
python src/core/convert.py --env projects\MyProject --output F:\Output\result.cf
pytest tests\
pytest tests\unit\
pytest tests\integration\
```

## Источники контекста

Этот файл собран по актуальному состоянию репозитория и материалам:

- `.kiro/steering/product.md`
- `.kiro/steering/structure.md`
- `.kiro/steering/tech.md`
- `.kiro/steering/python-architect.md`
- `.kiro/specs/python-converters-refactoring/requirements.md`
- `.kiro/specs/python-converters-refactoring/design.md`
- `.kiro/specs/python-converters-refactoring/tasks.md`

Если код и спецификация расходятся, ориентироваться в первую очередь на текущее рабочее состояние `src/` и тестов, а спецификацию использовать как объяснение целевой архитектуры и оставшихся направлений развития.

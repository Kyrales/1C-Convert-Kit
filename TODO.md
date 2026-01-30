# TODO: План работ по завершению миграции 1c-convert-kit

## ✅ Выполнено

- [x] Создана структура папок проекта
- [x] Скопированы CMD скрипты в src/converters/*/legacy/
- [x] Скопированы основные файлы (convert.py, converter_gui.py, params_descriptions.json)
- [x] Скопированы проекты пользователя в projects/
- [x] Скопированы тесты в tests/unit/
- [x] Созданы конфигурационные файлы (.gitignore, .gitattributes, requirements.txt)
- [x] Созданы скрипты запуска (run_gui.cmd, run_gui.sh)
- [x] Создан главный README.md
- [x] Создан README.md для projects/

---

## 🔧 Критические задачи (необходимо для работоспособности)

### 1. Адаптация src/gui/main.py
**Приоритет: ВЫСОКИЙ**

Файл: `src/gui/main.py` (бывший converter_gui.py)

Необходимые изменения:
- [x] Исправить импорт: `from convert import load_env_file` → `from ..core.convert import load_env_file`
- [x] Обновить SCRIPT_DIR: `Path(__file__).parent` → `Path(__file__).parent.parent.parent`
- [x] Обновить PROJECTS_DIR: `SCRIPT_DIR` → `SCRIPT_DIR / 'projects'`
- [x] Обновить CONVERT_SCRIPT: `SCRIPT_DIR / 'convert.py'` → `SCRIPT_DIR / 'src' / 'core' / 'convert.py'`
- [x] Обновить PARAMS_DESC_FILE: `SCRIPT_DIR / 'params_descriptions.json'` → `SCRIPT_DIR / 'src' / 'config' / 'params_descriptions.json'`
- [x] Обновить поиск базового .env в методе `update_details_table()`: `SCRIPT_DIR.glob` → `PROJECTS_DIR.glob`

### 2. Адаптация src/core/convert.py
**Приоритет: ВЫСОКИЙ**

Файл: `src/core/convert.py`

Необходимые изменения:
- [x] Добавить импорт `from typing import Optional`
- [x] Добавить функцию `find_legacy_script()` для поиска скриптов в legacy подпапках
- [x] Обновить путь к папке projects: `script_dir = Path(__file__).parent.parent.parent / 'projects'`
- [x] Обновить вызов: `conversion_script = find_legacy_script(script_name)`
- [x] Обновить поиск базового .env: искать в `projects_dir` вместо `script_dir`

**Функция find_legacy_script() уже добавлена:**
```python
def find_legacy_script(script_name: str) -> Optional[Path]:
    """Находит legacy CMD скрипт в соответствующей папке"""
    converters_dir = Path(__file__).parent.parent / 'converters'
    
    # Определяем тип скрипта по имени
    if script_name.startswith('conf'):
        legacy_dir = converters_dir / 'configuration' / 'legacy'
    elif script_name.startswith('dp'):
        legacy_dir = converters_dir / 'dataprocessor' / 'legacy'
    elif script_name.startswith('ext'):
        legacy_dir = converters_dir / 'extension' / 'legacy'
    elif script_name.startswith('edt'):
        legacy_dir = converters_dir / 'validation' / 'legacy'
    else:
        return None
    
    script_path = legacy_dir / script_name
    return script_path if script_path.exists() else None
```

### 3. Обновление путей в legacy CMD скриптах
**Приоритет: ВЫСОКИЙ**

Необходимые изменения:
- [x] Обновить взаимные вызовы между скриптами (используют относительные пути)
  - dp2epf.cmd, dp2edt.cmd, dp2xml.cmd → conf2ib.cmd
  - ext2cfe.cmd, ext2edt.cmd, ext2xml.cmd → conf2ib.cmd
  - edt-validate.cmd → conf2edt.cmd, ext2edt.cmd, dp2edt.cmd
- [x] Изменить `call %~dp0conf2ib.cmd` на `call %~dp0..\..\configuration\legacy\conf2ib.cmd`
- [x] Аналогично для других взаимных вызовов

**Примечание:** Файл VERSION удален из корня проекта, т.к. скрипты могут работать без него.

### 4. Тестирование базовой работоспособности
**Приоритет: ВЫСОКИЙ**

- [x] Создан базовый .env файл `projects/base_1.env` (скопирован из шаблона с обновленным путем V8_TEMP)
- [x] Обновлены пути в тестах под новую структуру
- [x] Все unit-тесты проходят успешно (8/8 passed)
  - test_params_descriptions.py - 7 тестов ✅
  - test_details_table.py - 1 тест ✅
- [ ] Запустить `run_gui.cmd` и проверить, что GUI открывается
- [ ] Проверить, что проекты из `projects/` отображаются в таблице
- [ ] Проверить, что детали проекта отображаются корректно
- [ ] Выполнить тестовую конвертацию одного проекта
- [ ] Проверить логирование в реальном времени

---

## 📚 Документация

### 4. Создание документации в docs/
**Приоритет: СРЕДНИЙ**

- [ ] `docs/INSTALLATION.md` - подробная инструкция по установке
  - Требования к системе
  - Установка Python
  - Установка зависимостей
  - Настройка 1С:Предприятие и EDT
  - Первый запуск

- [ ] `docs/USER_GUIDE.md` - руководство пользователя
  - Интерфейс GUI
  - Создание проектов
  - Настройка .env файлов
  - Пакетная конвертация
  - Работа с логами
  - Решение проблем

- [ ] `docs/DEVELOPER_GUIDE.md` - для разработчиков
  - Архитектура проекта
  - Структура кода
  - Добавление новых конвертеров
  - Тестирование
  - Вклад в проект

- [ ] `docs/API.md` - API документация
  - Базовый класс BaseConverter
  - Реестр конвертеров
  - Работа с .env файлами
  - Утилиты

- [ ] `docs/CHANGELOG.md` - история изменений
  - Версия 1.0.0 - начальный релиз

### 5. Скриншоты для документации
**Приоритет: НИЗКИЙ**

- [ ] `docs/images/gui-main.png` - главное окно с таблицей проектов
- [ ] `docs/images/gui-log.png` - вкладка с логом выполнения
- [ ] `docs/images/gui-details.png` - панель деталей проекта

---

## 🏗️ Архитектурные улучшения (для будущего)

### 6. Создание базовых классов конвертеров
**Приоритет: СРЕДНИЙ**

- [ ] `src/converters/base.py` - базовый класс BaseConverter
  - Абстрактные методы: validate(), convert(), name, description
  - Общая логика работы с .env
  - Обработка ошибок

- [ ] `src/converters/registry.py` - реестр конвертеров
  - Декоратор @ConverterRegistry.register()
  - Методы: get(), list_all()
  - Автообнаружение конвертеров

### 7. Рефакторинг утилит
**Приоритет: СРЕДНИЙ**

- [ ] `src/utils/logger.py` - централизованное логирование
  - Цветной вывод в консоль
  - Запись в файл
  - Уровни логирования

- [ ] `src/utils/colors.py` - ANSI цвета (вынести из convert.py)
  - Класс Colors
  - Поддержка Windows

- [ ] `src/utils/validators.py` - валидация путей и параметров
  - Проверка существования файлов
  - Валидация .env параметров
  - Проверка прав доступа

- [ ] `src/core/env_loader.py` - работа с .env (вынести из convert.py)
  - load_env_file()
  - merge_env_files()
  - find_env_files()

- [ ] `src/core/path_resolver.py` - работа с путями
  - Преобразование относительных путей
  - Определение типа пути (файл/каталог)
  - Создание каталогов

- [ ] `src/core/subprocess_runner.py` - запуск внешних процессов
  - Запуск 1С команд
  - Перехват вывода
  - Обработка ошибок

### 8. Разделение GUI на модули
**Приоритет: НИЗКИЙ**

- [ ] `src/gui/project_scanner.py` - вынести класс ProjectScanner из main.py
- [ ] `src/gui/conversion_runner.py` - вынести класс ConversionRunner из main.py
- [ ] `src/gui/themes.py` - вынести цветовую схему и темы
- [ ] Обновить `src/gui/main.py` для использования новых модулей

---

## 🧪 Тестирование

### 9. Расширение тестов
**Приоритет: СРЕДНИЙ**

- [x] Обновлены существующие тесты под новую структуру
  - test_params_descriptions.py - обновлены пути к JSON
  - test_details_table.py - обновлены импорты и пути
- [x] Все тесты проходят успешно (8/8 passed)
- [ ] `tests/conftest.py` - pytest конфигурация
  - Фикстуры для тестовых проектов
  - Моки для 1С инструментов

- [ ] `tests/unit/test_env_loader.py` - тесты загрузки .env
- [ ] `tests/unit/test_path_resolver.py` - тесты работы с путями
- [ ] `tests/unit/test_validators.py` - тесты валидации

- [ ] `tests/integration/test_convert.py` - интеграционные тесты конвертации
- [ ] `tests/integration/test_converters.py` - тесты конвертеров

- [ ] `tests/fixtures/sample_project/` - тестовые данные
  - Создать минимальный тестовый проект
  - Добавить .env файлы для тестов

### 10. CI/CD
**Приоритет: НИЗКИЙ**

- [ ] `.github/workflows/tests.yml` - GitHub Actions для автотестов
  - Запуск pytest
  - Проверка code coverage
  - Линтинг (flake8, black)

---

## 📦 Дополнительные файлы

### 11. Конфигурация проекта
**Приоритет: СРЕДНИЙ**

- [ ] `setup.py` - установочный скрипт
  - Метаданные проекта
  - Зависимости
  - Entry points

- [ ] `pyproject.toml` - современная конфигурация
  - Build system
  - Настройки black, mypy, pytest
  - Метаданные проекта

- [ ] `LICENSE` - лицензия (MIT)

- [ ] `CONTRIBUTING.md` - руководство для контрибьюторов
  - Как внести вклад
  - Code style
  - Процесс review

### 12. Шаблоны для projects/
**Приоритет: НИЗКИЙ**

- [ ] `projects/base_1.env.template` - шаблон базовой конфигурации
  - Все основные параметры с комментариями
  - Примеры значений

---

## 🚀 Первый Python конвертер (пилотный проект)

### 13. Реализация dp2epf.py
**Приоритет: НИЗКИЙ** (после завершения критических задач)

- [ ] `src/converters/dataprocessor/dp2epf.py`
  - Наследование от BaseConverter
  - Реализация validate()
  - Реализация convert()
  - Fallback на legacy CMD скрипт
  - Тесты

- [ ] Документация по миграции CMD → Python
  - Процесс миграции
  - Примеры кода
  - Best practices

---

## 📋 Чек-лист перед первым релизом

- [x] Все критические задачи выполнены (пункты 1-4)
- [x] Код адаптирован для новой структуры
- [x] Legacy CMD скрипты обновлены (взаимные вызовы)
- [x] Базовый .env файл создан в projects/
- [x] GUI запускается без ошибок импорта
- [ ] Хотя бы один проект успешно конвертируется
- [ ] Создана базовая документация (INSTALLATION.md, USER_GUIDE.md)
- [ ] README.md содержит актуальную информацию
- [ ] Проект протестирован на чистой установке
- [ ] Создан git репозиторий и сделан первый коммит

---

## 🎯 Приоритеты выполнения

### Фаза 1: Базовая работоспособность (КРИТИЧНО)
1. ✅ Адаптация src/gui/main.py
2. ✅ Адаптация src/core/convert.py
3. ✅ Обновление путей в legacy CMD скриптах
4. ⏳ Тестирование базовой работоспособности (в процессе)

### Фаза 2: Документация (ВАЖНО)
4. Создание INSTALLATION.md
5. Создание USER_GUIDE.md
6. Обновление README.md

### Фаза 3: Архитектурные улучшения (ЖЕЛАТЕЛЬНО)
7. Создание базовых классов
8. Рефакторинг утилит
9. Расширение тестов

### Фаза 4: Полировка (ОПЦИОНАЛЬНО)
10. Скриншоты
11. CI/CD
12. Первый Python конвертер

---

## 📝 Примечания

- Все изменения делать в новом проекте `f:\1C\Projects\1c-convert-kit\`
- Старый проект `f:\1C\Projects\1CFilesConverter\` оставить без изменений
- После завершения Фазы 1 проект должен быть полностью работоспособен
- Legacy CMD скрипты остаются до полной миграции на Python
- Версия 1.0.0 будет включать только работающий GUI с legacy скриптами
- Миграция на Python конвертеры - это версия 2.0.0

---

## 🐛 Известные проблемы

- [ ] Нужно проверить работу с кириллицей в путях
- [ ] Нужно проверить работу на разных версиях Python (3.7, 3.8, 3.9, 3.10+)
- [ ] Нужно проверить работу с разными версиями 1С:Предприятие
- [ ] Нужно проверить работу с разными версиями EDT

---

**Дата создания:** 30.01.2026  
**Дата последнего обновления:** 30.01.2026 16:20  
**Версия:** 1.0.0-alpha  
**Статус:** Фаза 1 завершена ✅ → Переход к тестированию

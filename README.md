<div align="center">

# 1C-Convert-Kit

<img src="docs/images/icons8-cyberpunk-gradient-96.png" alt="1C Convert Kit" width="96"/>

> Универсальный инструмент для конвертации файлов 1С:Предприятие между различными форматами

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)]()
[![Tests](https://img.shields.io/badge/unit%20tests-180%20passed-success)]()

[Возможности](#features) • [Интерфейс](#interface) • [Установка](#installation) • [Быстрый старт](#quick-start) • [Архитектура](#architecture)

</div>

---

## Для чего нужен 1C Convert Kit

- Быстро настроить конвертацию между форматами. Например, преобразовать CF из релиза вендора в EDT-проект для последующего обновления.
- Получить из отладочного лога готовые команды для CI/CD или локальных запусков.

<a id="features"></a>

## 🚀 Возможности

- 🎨 Современный GUI в стиле Cyberpunk
- 📦 Поддержка множества форматов: CF, CFE, EPF, ERF, DT, XML, EDT
- 🔄 Пакетная конвертация проектов
- 💻 Полноценный CLI-режим: запуск всех поддерживаемых сценариев конвертации и EDT-валидации из командной строки
- 🛠️ Базовый `.env` для постоянных общих параметров: версий платформы 1С и EDT, путей к инструментам и временному каталогу; проектный `.env` может переопределить любое значение
- 🖥️ Windows — основная поддерживаемая и протестированная платформа; Linux поддерживается с ограничениями и пока не тестировался
- ➕ Управление проектами в GUI: добавление, изменение, копирование, удаление
- 📊 Детальная информация о параметрах проектов
- 📝 Логирование в реальном времени
- ⚙️ Гибкая настройка через .env файлы

<a id="interface"></a>

## 🖥️ Интерфейс

<p align="center">
  <img src="docs/images/gui-projects.png" alt="Главное окно 1C Convert Kit" width="100%"/>
  <br/>
  <sub><b>Главное окно:</b> управление проектами, параметрами и запуском конвертации</sub>
</p>

<p align="center">
  <img src="docs/images/gui-execution-log.png" alt="Журнал выполнения конвертации" width="100%"/>
  <br/>
  <sub><b>Журнал выполнения</b></sub>
</p>

<p align="center">
  <img src="docs/images/gui-project-editor.png" alt="Редактор проекта" width="85%"/>
  <br/>
  <sub><b>Редактор проекта</b></sub>
</p>

<p align="center">
  <img src="docs/images/gui-parameter-help.png" alt="Встроенная подсказка параметра" width="75%"/>
  <br/>
  <sub><b>Встроенные подсказки</b> для параметров конвертации</sub>
</p>

<a id="installation"></a>

## 🛠️ Установка

```bash
# Клонировать репозиторий
git clone https://github.com/Kyrales/1C-Convert-Kit.git
cd 1c-convert-kit

# Установить зависимости Python
pip install -r requirements.txt

# Запустить GUI
python src/gui/main.py
# или
run_gui.cmd  # для Windows
./run_gui.sh # для Linux/Mac
```

<a id="quick-start"></a>

## 📖 Быстрый старт

### Вариант 1: Создание проекта через GUI (рекомендуется)

1. **Запустите GUI**
   ```bash
   run_gui.cmd  # для Windows
   # или
   run_gui.sh  # для Linux
   # или
   python src/gui/main.py
   ```

2. **Настройте базовую конфигурацию (опционально)**
   - Скопируйте `src/config/base.env.template` в `projects/base.env`
   - Укажите общие параметры (версия 1С, пути к инструментам)

3. **Создайте проект через GUI**
   - Нажмите кнопку **Добавить**
   - Заполните обязательные поля:
     - Наименование проекта
     - Тип скрипта (conf2cf, dp2epf, ext2cfe и т.д.)
     - V8_SRC_PATH - путь к источнику
     - V8_DST_PATH - путь назначения
   - Включите дополнительные параметры при необходимости
   - Нажмите **Сохранить**

4. **Запустите конвертацию**
   - Выберите проекты в таблице (клик по строке)
   - Нажмите "ВЫПОЛНИТЬ (F5)"
   - Следите за прогрессом в логе

### Вариант 2: Создание проекта вручную

1. **Настройте базовую конфигурацию**
   - Скопируйте `src/config/base.env.template` в `projects/base.env`
   - Укажите пути к 1С:Предприятие и EDT в файле настроек env

2. **Создайте проект**
   - Создайте папку в `projects/`
   - Добавьте .env файл с настройками проекта
   - Укажите `ScriptName` (например: `conf2cf`)

3. **Запустите GUI**
   - Выберите проекты для конвертации
   - Нажмите "ВЫПОЛНИТЬ"
   - Следите за прогрессом в логе

<a id="architecture"></a>

## 🏛️ Архитектура

### Схема работы системы

```mermaid
graph TB
    subgraph "GUI Layer"
        GUI[CyberpunkGUI]
        Scanner[ProjectScanner]
        Editor[ProjectEditor]
        Runner[ConversionRunner]
    end
    
    subgraph "Core Layer"
        Core[convert.py]
        Registry[ConverterRegistry]
        EnvLoader[ENV File Loader]
    end
    
    subgraph "Converter Layer"
        Base[BaseConverter]
        Config[ConfigurationConverter]
        DP[DataProcessorConverter]
        Ext[ExtensionConverter]
        Val[ValidationConverter]
    end
    
    subgraph "Tool Wrappers"
        V8[V8ToolWrapper]
        Ibcmd[IbcmdToolWrapper]
        EDT[EdtToolWrapper]
    end
    
    subgraph "1C Tools"
        Designer[1cv8.exe designer]
        IbcmdTool[ibcmd.exe]
        EdtTool[1cedtcli/ring]
    end
    
    GUI --> Core
    Scanner --> EnvLoader
    Editor --> EnvLoader
    Runner --> Core
    
    Core --> Registry
    Core --> EnvLoader
    Registry --> Config
    Registry --> DP
    Registry --> Ext
    Registry --> Val
    
    Config --> Base
    DP --> Base
    Ext --> Base
    Val --> Base
    
    Base --> V8
    Base --> Ibcmd
    Base --> EDT
    
    V8 --> Designer
    Ibcmd --> IbcmdTool
    EDT --> EdtTool
    
    style GUI fill:#ff00ff,stroke:#fff,color:#fff
    style Core fill:#00ffff,stroke:#fff,color:#000
    style Base fill:#ffff00,stroke:#000,color:#000
    style Designer fill:#00ff00,stroke:#000,color:#000
```

### Ключевые компоненты

**GUI Layer** — графический интерфейс в стиле Cyberpunk:
- Управление проектами конвертации (добавление, редактирование, копирование, удаление, изменение порядка выполнения)
- Запуск пакетной конвертации выбранных проектов
- Логи в реальном времени и замер длительности этапов
- Команды внешних инструментов в режиме отладки

**Core Layer** — ядро системы:
- Загрузка и объединение .env файлов
- Автоматический выбор конвертера через Registry
- CLI интерфейс

**Converter Layer** — модульная система конвертеров:
- Единая базовая логика (BaseConverter)
- Специализированные конвертеры для каждого типа
- Автоматическое обнаружение и регистрация

**Tool Wrappers** — обертки над инструментами 1С:
- Унифицированный интерфейс
- Обработка ошибок
- Парсинг вывода

### Преимущества архитектуры

- ✅ Автоматическое обнаружение конвертеров
- ✅ Простота добавления новых типов конвертации
- ✅ Единообразная обработка ошибок
- ✅ Расширяемость

## 🏗️ Структура проекта

```
1c-convert-kit/
├── src/
│   ├── gui/                    # GUI модули (FreeSimpleGUI)
│   │   ├── main.py            # Точка входа
│   │   ├── main_window.py     # Главное окно
│   │   ├── project_scanner.py # Сканирование проектов
│   │   ├── project_editor.py  # Редактор проектов
│   │   └── sg_import.py       # Централизованный импорт GUI
│   ├── converters/            # Модульная система конвертеров
│   │   ├── base/              # Базовые классы
│   │   │   ├── converter.py  # BaseConverter
│   │   │   └── tools.py      # Tool Wrappers
│   │   ├── registry.py        # ConverterRegistry
│   │   ├── configuration/     # Конвертер конфигураций
│   │   ├── dataprocessor/     # Конвертер обработок/отчетов
│   │   ├── extension/         # Конвертер расширений
│   │   └── validation/        # Валидатор EDT
│   ├── core/                  # Ядро системы
│   │   └── convert.py         # CLI + загрузка .env
│   ├── config/                # Конфигурация
│   │   ├── base.env.template
│   │   └── params_descriptions.json
│   └── utils/                 # Утилиты
│       └── time_utils.py      # Форматирование времени
├── projects/                  # Рабочие проекты (.env файлы)
├── tests/                     # Unit- и интеграционные тесты
├── docs/                      # Документация
└── logs/                      # Логи выполнения
```

## 🔧 Поддерживаемые конвертации

### Конфигурации
- `conf2cf` - Конфигурация → CF файл
- `conf2xml` - Конфигурация → XML
- `conf2edt` - Конфигурация → EDT проект
- `conf2ib` - Конфигурация → Информационная база
- `dt2ib` - DT-файл → Информационная база (восстановление с заменой содержимого)
- `ib2dt` - Информационная база → DT-файл

### Обработки и отчеты
- `dp2epf` - Обработка/Отчет → EPF/ERF файл
- `dp2xml` - Обработка/Отчет → XML
- `dp2edt` - Обработка/Отчет → EDT проект

### Расширения
- `ext2cfe` - Расширение → CFE файл
- `ext2xml` - Расширение → XML
- `ext2edt` - Расширение → EDT проект
- `ext2ib` - Расширение → Информационная база

### 📋 Валидация EDT проектов
- `edt-validate` - Валидация EDT проекта

## 📚 Документация

- [Быстрый старт](QUICKSTART.md) - Начало работы за 5 минут
- [Управление проектами через GUI](docs/PROJECT_MANAGEMENT.md)
- [Валидация EDT проектов](docs/VALIDATION_GUIDE.md) - Подробное руководство
- [Схема алгоритмов конвертации](CONVERSION_STATE_DIAGRAM.md)

<a id="contributing"></a>

## 🤝 Вклад в проект

Приветствуются pull requests! Для крупных изменений сначала откройте issue для обсуждения.

## 🙏 Благодарности

Проект основан на [1CFilesConverter](https://github.com/arkuznetsov/1CFilesConverter)

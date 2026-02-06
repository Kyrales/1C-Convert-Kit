# Руководство по валидации EDT проектов

ValidationConverter позволяет проверять корректность EDT проектов 1С с использованием встроенных инструментов EDT (1cedtcli или ring).

## Содержание

- [Возможности](#возможности)
- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Настройка](#настройка)
- [Примеры использования](#примеры-использования)
- [Формат отчета](#формат-отчета)
- [Устранение проблем](#устранение-проблем)

## Возможности

- ✅ Автоматический поиск EDT инструментов (1cedtcli приоритетнее ring)
- ✅ Поддержка обеих структур EDT проектов (старая и новая)
- ✅ Генерация отчета валидации в текстовом формате (TSV)
- ✅ Подсчет проблем по уровням (Критические, Значительные, Незначительные, Тривиальные)
- ✅ Вывод критических замечаний для быстрого исправления
- ✅ Сохранение временных файлов при ошибках для отладки

## Требования

### Обязательные

1. **EDT проект** с корректной структурой:
   - Директория `DT-INF`
   - Файл `.project`
   - Директория `src`
   - Метаданные конфигурации или расширения

2. **EDT инструменты** (один из):
   - 1C:EDT (1cedtcli.exe) - рекомендуется
   - ring - альтернатива

### Опциональные

- Переменная окружения `EDTCLI_TOOL` с путем к 1cedtcli.exe
- Переменная окружения `RING_TOOL` с путем к ring.bat

## Быстрый старт

### Через GUI

1. Запустите GUI:
   ```bash
   run_gui.cmd  # Windows
   ```

2. Нажмите **Добавить** для создания нового проекта

3. Заполните поля:
   - **Наименование проекта**: `МойПроект_валидация`
   - **Тип скрипта**: `edt-validate`
   - **V8_SRC_PATH**: путь к EDT проекту (например: `f:\Projects\MyEDTProject`)
   - **V8_DST_PATH**: путь к отчету или каталогу (например: `f:\Reports`)

4. Нажмите **Сохранить**

5. Выберите проект в таблице и нажмите **ВЫПОЛНИТЬ (F5)**

### Через CLI

1. Создайте .env файл в `projects/МойПроект_валидация/`:
   ```bash
   ScriptName=edt-validate
   V8_SRC_PATH=f:\Projects\MyEDTProject
   V8_DST_PATH=f:\Reports
   ```

2. Запустите конвертацию:
   ```bash
   python src/core/convert.py --env projects/МойПроект_валидация
   ```

## Настройка

### Базовая конфигурация (projects/base.env)

```bash
# Версия EDT (опционально, по умолчанию 2024.2)
V8_EDT_VERSION=2024.2

# Путь к 1cedtcli.exe (опционально, если не в PATH)
EDTCLI_TOOL=C:\Program Files\1C\1CE\components\1c-edt-2024.2\1cedtcli.exe

# Путь к ring.bat (опционально, используется если 1cedtcli не найден)
RING_TOOL=C:\Users\User\AppData\Local\Programs\ring\ring.bat

# Временная директория (опционально)
V8_TEMP=f:\temp\1c

# Удалять временные файлы после успешной конвертации (опционально)
V8_TEMP_AFTER_CLEAN=1
```

### Конфигурация проекта

```bash
# Обязательные параметры
ScriptName=edt-validate
V8_SRC_PATH=f:\Projects\MyEDTProject
V8_DST_PATH=f:\Reports\validation_report.txt

# Опциональные параметры
V8_EDT_VERSION=2024.2
EDTCLI_TOOL=C:\Program Files\1C\1CE\components\1c-edt-2024.2\1cedtcli.exe
```

## Примеры использования

### Пример 1: Валидация конфигурации

**Структура проекта:**
```
MyConfiguration/
├── DT-INF/
├── .project
└── src/
    └── Configuration/
        └── Configuration.mdo
```

**Файл .env:**
```bash
ScriptName=edt-validate
V8_SRC_PATH=f:\Projects\MyConfiguration
V8_DST_PATH=f:\Reports
```

**Результат:**
- Отчет: `f:\Reports\validation_report.txt`
- Статистика проблем в консоли
- Список критических замечаний

### Пример 2: Валидация расширения

**Структура проекта:**
```
MyExtension/
├── DT-INF/
│   └── Extension.xml
├── .project
└── src/
    └── Extension/
        └── Extension.mdo
```

**Файл .env:**
```bash
ScriptName=edt-validate
V8_SRC_PATH=f:\Projects\MyExtension
V8_DST_PATH=f:\Reports\extension_validation.txt
```

### Пример 3: Валидация с указанием версии EDT

```bash
ScriptName=edt-validate
V8_SRC_PATH=f:\Projects\MyProject
V8_DST_PATH=f:\Reports
V8_EDT_VERSION=2023.3
EDTCLI_TOOL=C:\Program Files\1C\1CE\components\1c-edt-2023.3\1cedtcli.exe
```

### Пример 4: Валидация с использованием ring

```bash
ScriptName=edt-validate
V8_SRC_PATH=f:\Projects\MyProject
V8_DST_PATH=f:\Reports
RING_TOOL=C:\Users\User\AppData\Local\Programs\ring\ring.bat
V8_EDT_VERSION=2024.2
```

## Формат отчета

Отчет валидации сохраняется в текстовом формате (TSV) со следующей структурой:

```
Дата	Уровень	Категория	Проект	Правило	Объект	Строка	Описание
```

**Пример строки отчета:**
```
2026-02-06T16:51:37+0300	Критическая	Предупреждение	MyProject	com.e1c.v8codestyle.bsl:module-self-reference	ОбщийМодуль.РаботаСПочтой.Модуль	строка 85	Избыточное обращение внутри модуля через псевдоним "ЭтотОбъект"
```

### Уровни проблем

1. **Критическая** - блокирующие проблемы, требующие немедленного исправления
2. **Значительная** - серьезные проблемы, влияющие на качество кода
3. **Незначительная** - мелкие замечания, не влияющие на работу
4. **Тривиальная** - стилистические замечания

## Вывод в консоль

### Успешная валидация

```
[ИНФО] Валидация EDT проекта
[ИНФО] Отчет валидации: F:\Reports\validation_report.txt
[ИНФО] Проверка структуры EDT проекта...
[ИНФО] [OK] Директория DT-INF найдена
[ИНФО] [OK] Файл .project найден
[ИНФО] [OK] Директория src найдена
[ИНФО] [OK] Найден Configuration.mdo в src/Configuration (конфигурация)
[ИНФО]   Найдено файлов в src: 676
[УСПЕХ] Базовая структура EDT проекта корректна
[ИНФО] Используется EDTCLI_TOOL из переменной окружения
[ИНФО] Используется инструмент: edtcli
[ИНФО] Запуск валидации EDT проекта...
[УСПЕХ] Валидация завершена успешно
[ИНФО] Отчет сохранен: F:\Reports\validation_report.txt
[ИНФО] Найдено проблем: 2266
[ИНФО]   Критических: 5
[ИНФО]   Значительных: 2237
[ИНФО]   Незначительных: 0
[ИНФО]   Тривиальных: 24
[ИНФО]
[ИНФО] Критические замечания:
[ИНФО]   1. ОбщийМодуль.РаботаСПолнотекстовымПоиском (Имя): Привилегированный модуль должен оканчиваться на суффикс "ПолныеПрава,FullAccess"
[ИНФО]   2. Справочник.Встречи.Форма.Календарь.Форма.Модуль (строка 598): Цикл содержит выполнение запроса
[ИНФО]   3. Конфигурация.СоставАвтономнойКонфигурации (): Используемые объекты содержат зависимый объект "Subsystem.ТоварныеЗапасы"
[УСПЕХ] Конвертация завершена успешно
```

### Валидация без проблем

```
[ИНФО] Валидация EDT проекта
[ИНФО] Отчет валидации: F:\Reports\validation_report.txt
[УСПЕХ] Валидация завершена успешно
[УСПЕХ] Проблем не найдено
[УСПЕХ] Конвертация завершена успешно
```

## Устранение проблем

### Проблема: EDT инструмент не найден

**Ошибка:**
```
[ОШИБКА] Инструмент не найден: EDT инструмент не найден.
Установите ring или 1C:EDT, либо укажите путь в переменных:
  - EDTCLI_TOOL - путь к 1cedtcli.exe (рекомендуется)
  - RING_TOOL - путь к ring.bat
```

**Решение:**
1. Установите 1C:EDT или ring
2. Укажите путь к инструменту в .env файле:
   ```bash
   EDTCLI_TOOL=C:\Program Files\1C\1CE\components\1c-edt-2024.2\1cedtcli.exe
   ```

### Проблема: Источник не является EDT проектом

**Ошибка:**
```
[ОШИБКА] Ошибка валидации: ValidationConverter работает только с EDT проектами.
Обнаружен тип источника: xml
```

**Решение:**
1. Убедитесь что V8_SRC_PATH указывает на EDT проект
2. Проверьте наличие директории DT-INF и файла .project
3. Для конвертации других форматов используйте:
   - `conf2edt` - для конфигураций (CF, XML, IB)
   - `ext2edt` - для расширений (CFE, XML, IB)
   - `dp2edt` - для обработок и отчетов (EPF, ERF, XML)

### Проблема: Отсутствует директория DT-INF

**Ошибка:**
```
[ОШИБКА] Ошибка валидации: EDT проект не содержит директорию DT-INF
```

**Решение:**
1. Проверьте что указан правильный путь к EDT проекту
2. Убедитесь что проект не поврежден
3. Пересоздайте проект из исходников

### Проблема: Превышено время ожидания

**Ошибка:**
```
[ОШИБКА] Превышено время ожидания валидации (5 минут)
```

**Решение:**
1. Проверьте размер проекта (большие проекты могут валидироваться дольше)
2. Убедитесь что EDT инструмент работает корректно
3. Проверьте доступность сетевых ресурсов (если проект на сетевом диске)

## Интеграция в CI/CD

### GitHub Actions

```yaml
name: Validate EDT Project

on: [push, pull_request]

jobs:
  validate:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.7'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Install EDT
        run: |
          # Установка EDT (пример)
          choco install 1c-edt
      
      - name: Validate EDT Project
        run: |
          python src/core/convert.py --env projects/MyProject_validation
      
      - name: Upload validation report
        uses: actions/upload-artifact@v2
        with:
          name: validation-report
          path: build/validation_report.txt
```

### Jenkins

```groovy
pipeline {
    agent any
    
    stages {
        stage('Validate EDT Project') {
            steps {
                bat 'python src/core/convert.py --env projects/MyProject_validation'
            }
        }
        
        stage('Archive Report') {
            steps {
                archiveArtifacts artifacts: 'build/validation_report.txt'
            }
        }
    }
}
```

## Дополнительные ресурсы

- [Документация 1C:EDT](https://releases.1c.ru/project/DevelopmentTools10)
- [Стандарты кодирования 1С](https://its.1c.ru/db/v8std)
- [Руководство по архитектуре](../README.md#архитектура)

## Поддержка

При возникновении проблем:
1. Проверьте логи в директории `logs/`
2. Проверьте временные файлы в `temp/` (если сохранены)
3. Создайте issue в репозитории проекта

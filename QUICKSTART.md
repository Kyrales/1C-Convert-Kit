# 🚀 Быстрый старт — 1C Convert Kit

Краткая инструкция по установке, настройке и запуску первой конвертации.

---

## Установка за 3 шага

### 1. Клонирование и установка зависимостей

```bash
git clone https://github.com/Kyrales/1C-Convert-Kit.git
cd 1c-convert-kit
pip install -r requirements.txt
```

### 2. Настройка базовой конфигурации (опционально)

```bash
# Windows
copy src\config\base.env.template projects\base.env

# Linux (поддержка ограничена, работа не тестировалась)
cp src/config/base.env.template projects/base.env
```

Отредактируйте `projects/base.env`:
```ini
# Версия 1С:Предприятие
V8_VERSION=8.5.1.1522

# Путь к 1cv8.exe
V8_TOOL="C:\Program Files\1cv8\8.5.1.1522\bin\1cv8.exe"

# Путь к EDT (1cedtcli или ring)
EDTCLI_TOOL="C:\Program Files\1C\1CE\components\1c-edt-2025.2.3\1cedtcli.exe"
```

### 3. Запуск

```bash
# Windows
run_gui.cmd

# Linux (поддержка ограничена, работа не тестировалась)
./run_gui.sh

# Или напрямую
python src/gui/main.py
```

---

## Первая конвертация

### Через GUI (рекомендуется)

#### Пример: Конвертация конфигурации EDT → CF

1. **Создайте проект**
   - Нажмите кнопку **"Добавить"**
   - Заполните поля:
     - **Имя проекта:** `МояКонфигурация`
     - **Тип скрипта:** `conf2cf`
     - **V8_SRC_PATH:** `C:\EDT\MyConfiguration` (путь к EDT проекту)
     - **V8_DST_PATH:** `C:\Output\MyConfiguration.cf` (путь для CF файла)
   - Нажмите **"Сохранить"**

2. **Запустите конвертацию**
   - Выберите проект в таблице (клик по строке)
   - Нажмите **"ВЫПОЛНИТЬ (F5)"** или клавишу F5
   - Следите за прогрессом в окне лога

3. **Результат**
   - При успехе: CF файл создан по указанному пути
   - При ошибке: проверьте лог и временные файлы в `temp/`

### Через CLI

```bash
# Создайте папку проекта
mkdir projects\MyConfig

# Создайте .env файл
echo ScriptName=conf2cf > projects\MyConfig\config.env
echo V8_SRC_PATH=C:\EDT\MyConfiguration >> projects\MyConfig\config.env
echo V8_DST_PATH=C:\Output\MyConfiguration.cf >> projects\MyConfig\config.env

# Запустите конвертацию
python src\core\convert.py --env projects\MyConfig\config.env
```

---

## Типы конвертаций

| Тип | Описание | Источник | Результат |
|-----|----------|----------|-----------|
| `conf2cf` | Конфигурация → CF | EDT/XML/IB | Configuration.cf |
| `conf2xml` | Конфигурация → XML | EDT/CF/IB | XML файлы |
| `conf2edt` | Конфигурация → EDT | XML/CF | EDT проект |
| `dp2epf` | Обработка → EPF | EDT/XML | Processor.epf |
| `dp2erf` | Отчет → ERF | EDT/XML | Report.erf |
| `ext2cfe` | Расширение → CFE | EDT/XML/IB | Extension.cfe |
| `edt-validate` | Валидация EDT | EDT проект | Отчет о проблемах |

---

## Структура .env файла

### Минимальный пример (conf2cf)

```ini
# Обязательные параметры
ScriptName=conf2cf
V8_SRC_PATH=C:\EDT\MyConfiguration
V8_DST_PATH=C:\Output\MyConfiguration.cf
```

### Полный пример с опциональными параметрами

```ini
# Тип конвертации
ScriptName=conf2cf

# Пути
V8_SRC_PATH=C:\EDT\MyConfiguration
V8_DST_PATH=C:\Output\MyConfiguration.cf

# Версия и инструменты (если не указаны в base.env)
V8_VERSION=8.5.1.1522
V8_TOOL=C:\Program Files\1cv8\8.5.1.1522\bin\1cv8.exe
EDTCLI_TOOL=C:\Users\YourName\edt\1cedtcli.exe

# Дополнительные параметры
V8_TEMP_AFTER_CLEAN=1             # Очистка временных файлов (1=да, 0=нет)
V8_IB_USER=Администратор          # Пользователь ИБ (если требуется)
V8_IB_PWD=password                # Пароль (если требуется)
```

---

## Управление проектами через GUI

### Добавление проекта
1. Кнопка **"Добавить"**
2. Заполните форму
3. **"Сохранить"**

### Редактирование проекта
1. Выберите проект в таблице
2. Кнопка **"Изменить"**
3. Внесите изменения
4. **"Сохранить"**

### Копирование проекта
1. Выберите проект в таблице
2. Кнопка **"Копировать"**
3. Укажите новое имя
4. **"Сохранить"**

### Удаление проекта
1. Выберите проект в таблице
2. Кнопка **"Удалить"**
3. Подтвердите удаление

### Пакетная конвертация
1. Выберите несколько проектов (клик по строкам)
2. Нажмите **"ВЫПОЛНИТЬ (F5)"**
3. Все выбранные проекты будут обработаны последовательно

---

## Полезные команды

### Запуск тестов

```bash
# Все unit-тесты
python -m pytest tests/unit/ -v

# Конкретный тест
python -m pytest tests/unit/test_registry_complete.py -v

# С покрытием кода
python -m pytest --cov=src tests/unit/
```

### Проверка кода

```bash
# Форматирование
black src/ --check

# Линтинг
flake8 src/

# Проверка типов
mypy src/
```

---

## Решение проблем

### GUI не запускается

**Ошибка:**
```
ImportError: No module named 'FreeSimpleGUI'
```

**Решение:**
```bash
pip install FreeSimpleGUI
```

---

### Конвертация не работает

**Ошибка:**
```
Ошибка: Не найден инструмент 1С
```

**Решение:**
1. Укажите `V8_TOOL` в `projects/base.env`
2. Или укажите в конкретном проекте
3. Проверьте, что путь существует и файл запускается

---

### Проекты не отображаются

**Проблема:** Таблица в GUI пустая

**Решение:**
1. Проверьте, что .env файлы находятся в `projects/` или подпапках
2. Убедитесь, что файлы содержат параметр `ScriptName`
3. Проверьте кодировку файлов (должна быть UTF-8)

---

### Ошибка при конвертации

**Проблема:** Конвертация завершается с ошибкой

**Решение:**
1. Проверьте лог в GUI (внизу окна)
2. Проверьте временные файлы в `temp/` (не удаляются при ошибке)
3. Проверьте логи в `logs/`
4. Убедитесь, что пути к источнику и назначению корректны

---

### Временные файлы не удаляются

**Проблема:** Папка `temp/` заполняется

**Решение:**
1. Добавьте в `.env`-файл: `V8_TEMP_AFTER_CLEAN=1`
2. Или удалите вручную: `rmdir /s /q temp` (Windows)
3. Временные файлы сохраняются при ошибках для отладки

---

## Дальнейшие шаги

- 📚 Изучите [полную документацию](README.md)
- 🎨 Настройте [базовую конфигурацию](docs/BASE_ENV_DISPLAY_FEATURE.md)
- 🏗️ Изучите [архитектуру проекта](README.md#architecture)
- 🧪 Запустите [тесты](tests/README.md)
- 🤝 Внесите [вклад в проект](README.md#contributing)

---

## Горячие клавиши GUI

| Клавиша | Действие |
|---------|----------|
| **F5** | Запустить конвертацию выбранных проектов |
| **Ctrl+A** | Добавить новый проект |
| **Ctrl+E** | Редактировать выбранный проект |
| **Ctrl+C** | Копировать выбранный проект |
| **Delete** | Удалить выбранный проект |
| **Ctrl+R** | Обновить список проектов |

---

Дополнительные сведения есть в [README.md](README.md). Об ошибках можно сообщить в [GitHub Issues](https://github.com/Kyrales/1C-Convert-Kit/issues).

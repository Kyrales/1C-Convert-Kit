# 1C Convert Kit

> Графический интерфейс для конвертации файлов 1С:Предприятие между различными форматами

[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

## 🚀 Возможности

- 🎨 Современный GUI в стиле Cyberpunk
- 📦 Поддержка множества форматов: CF, CFE, EPF, ERF, XML, EDT
- 🔄 Пакетная конвертация проектов
- 📊 Детальная информация о параметрах проектов
- 📝 Логирование в реальном времени
- ⚙️ Гибкая настройка через .env файлы

## 🛠️ Установка

```bash
# Клонировать репозиторий
git clone https://github.com/username/1c-convert-kit.git
cd 1c-convert-kit

# Установить зависимости
pip install -r requirements.txt

# Запустить GUI
python src/gui/main.py
# или
run_gui.cmd  # для Windows
./run_gui.sh # для Linux/Mac
```

## 📖 Быстрый старт

1. **Настройте базовую конфигурацию**
   - Скопируйте `src/config/base.env.template` в `projects/base_1.env`
   - Укажите пути к 1С:Предприятие и EDT

2. **Создайте проект**
   - Создайте папку в `projects/`
   - Добавьте .env файл с настройками проекта
   - Укажите `ScriptName` (например: `dp2epf.cmd`)

3. **Запустите GUI**
   - Выберите проекты для конвертации
   - Нажмите "ВЫПОЛНИТЬ"
   - Следите за прогрессом в логе

## 📚 Документация

- [Руководство пользователя](docs/USER_GUIDE.md)
- [Инструкция по установке](docs/INSTALLATION.md)
- [Руководство разработчика](docs/DEVELOPER_GUIDE.md)
- [API документация](docs/API.md)

## 🏗️ Структура проекта

```
1c-convert-kit/
├── src/                    # Исходный код
│   ├── gui/               # GUI модули
│   ├── converters/        # Конвертеры (Python + legacy CMD)
│   ├── core/              # Ядро системы
│   ├── config/            # Конфигурация
│   └── utils/             # Утилиты
├── projects/              # Рабочие проекты пользователя
├── tests/                 # Тесты
├── docs/                  # Документация
└── logs/                  # Логи выполнения
```

## 🔧 Поддерживаемые конвертации

### Конфигурации
- `conf2cf` - Конфигурация → CF файл
- `conf2xml` - Конфигурация → XML
- `conf2edt` - Конфигурация → EDT проект
- `conf2ib` - Конфигурация → Информационная база

### Обработки и отчеты
- `dp2epf` - Обработка/Отчет → EPF/ERF файл
- `dp2xml` - Обработка/Отчет → XML
- `dp2edt` - Обработка/Отчет → EDT проект

### Расширения
- `ext2cfe` - Расширение → CFE файл
- `ext2xml` - Расширение → XML
- `ext2edt` - Расширение → EDT проект
- `ext2ib` - Расширение → Информационная база

### Валидация
- `edt-validate` - Валидация EDT проекта

## 🤝 Вклад в проект

Приветствуются pull requests! Для крупных изменений сначала откройте issue для обсуждения.

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE)

## 🙏 Благодарности

Проект основан на [1CFilesConverter](https://github.com/1CFilesConverter)

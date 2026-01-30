# Интеграционные тесты конвертации

Этот каталог содержит интеграционные тесты для проверки полного цикла конвертации 1С проектов.

## 🎯 Что тестируется

### test_convert_integration.py

**Тест 1: test_conf2cf_conversion**
- Конвертация EDT конфигурации в CF файл
- Использует тестовый проект: `tests/fixtures/cf/otusJenkinsExampleEDT`
- Проверяет создание файла `otusJenkinsExampleEDT.cf`
- Проверяет размер выходного файла

**Тест 2: test_ext2cfe_conversion**
- Конвертация EDT расширения в CFE файл
- Использует тестовый проект: `tests/fixtures/cfe/otusJenkinsExampleEDT.Колонтитулы`
- Проверяет создание файла `otusJenkinsExampleEDT.Колонтитулы.cfe`
- Проверяет размер выходного файла

**Тест 3: test_env_files_loading**
- Загрузка и объединение .env файлов
- Проверка корректности параметров
- Проверка переопределения значений

**Тест 4: test_source_projects_exist**
- Проверка наличия исходных тестовых проектов
- Проверка структуры EDT проектов

## 📋 Требования

### Обязательные инструменты:
- **1C:Enterprise** (1cv8.exe) - версия 8.3.27.1989 или выше
- **1C:EDT** (1cedtcli.exe) - версия 2025.1.5 или выше
- **Python** 3.8+ с установленным pytest

### Настройка путей:
Отредактируйте `tests/fixtures/base_test.env` и укажите корректные пути к инструментам:
```env
V8_TOOL="C:\Program Files\1cv8\8.3.27.1989\bin\1cv8.exe"
EDTCLI_TOOL="f:\1C\Projects\EDT\installations\1C_EDT 2025.1\1cedt\1cedtcli.exe"
```

## 🚀 Запуск тестов

### Все интеграционные тесты:
```bash
pytest tests/integration/ -v
```

### Конкретный тест:
```bash
pytest tests/integration/test_convert_integration.py::TestConversionIntegration::test_conf2cf_conversion -v
```

### С подробным выводом:
```bash
pytest tests/integration/ -v -s
```

### Только проверка окружения (без конвертации):
```bash
pytest tests/integration/test_convert_integration.py::TestConversionIntegration::test_source_projects_exist -v
pytest tests/integration/test_convert_integration.py::TestConversionIntegration::test_env_files_loading -v
```

## 📊 Ожидаемый результат

```
tests/integration/test_convert_integration.py::TestConversionIntegration::test_conf2cf_conversion PASSED
✓ Конфигурация успешно сконвертирована
✓ Размер файла: 2.45 МБ

tests/integration/test_convert_integration.py::TestConversionIntegration::test_ext2cfe_conversion PASSED
✓ Расширение успешно сконвертировано
✓ Размер файла: 15.32 КБ

tests/integration/test_convert_integration.py::TestConversionIntegration::test_env_files_loading PASSED
✓ Загружено параметров из базового .env: 8
✓ Загружено параметров из проектного .env: 3
✓ Всего параметров после объединения: 10

tests/integration/test_convert_integration.py::TestConversionIntegration::test_source_projects_exist PASSED
✓ EDT проект конфигурации найден: otusJenkinsExampleEDT
✓ EDT проект расширения найден: otusJenkinsExampleEDT.Колонтитулы

================================= 4 passed in 45.23s =================================
```

## 🔧 Структура тестов

```
tests/
├── fixtures/
│   ├── base_test.env                    # Базовая конфигурация для тестов
│   ├── test_conf2cf.env                 # Настройки для теста conf2cf
│   ├── test_ext2cfe.env                 # Настройки для теста ext2cfe
│   ├── output/                          # Выходная директория (создается и удаляется автоматически)
│   ├── cf/
│   │   └── otusJenkinsExampleEDT/       # Тестовый EDT проект конфигурации
│   └── cfe/
│       └── otusJenkinsExampleEDT.Колонтитулы/  # Тестовый EDT проект расширения
└── integration/
    ├── test_convert_integration.py      # Интеграционные тесты
    └── README.md                        # Этот файл
```

## 🧹 Очистка

Тесты автоматически очищают за собой:
- Директория `tests/fixtures/output/` создается перед каждым тестом
- Директория `tests/fixtures/output/` удаляется после каждого теста
- Временные файлы 1С удаляются автоматически

## ⚠️ Важные замечания

1. **Время выполнения**: Интеграционные тесты могут занимать 30-60 секунд на каждую конвертацию
2. **Реальные инструменты**: Тесты используют реальные инструменты 1С, убедитесь что они установлены
3. **Пути**: Проверьте корректность путей в `base_test.env` перед запуском
4. **Лицензия**: Для работы 1C:Enterprise может потребоваться лицензия

## 🐛 Отладка

### Тест падает с ошибкой "Базовый .env не найден":
```bash
# Проверьте наличие файла
ls tests/fixtures/base_test.env
```

### Тест падает с ошибкой "Исходный EDT проект не найден":
```bash
# Проверьте наличие тестовых проектов
ls tests/fixtures/cf/otusJenkinsExampleEDT/.project
ls tests/fixtures/cfe/otusJenkinsExampleEDT.Колонтитулы/.project
```

### Тест падает с ошибкой конвертации:
```bash
# Запустите тест с подробным выводом
pytest tests/integration/test_convert_integration.py::TestConversionIntegration::test_conf2cf_conversion -v -s

# Проверьте пути к инструментам в base_test.env
# Проверьте наличие инструментов
"C:\Program Files\1cv8\8.3.27.1989\bin\1cv8.exe" /?
```

## 📚 Дополнительная информация

- Тесты используют модуль `src/core/convert.py`
- Конфигурационные файлы находятся в `tests/fixtures/`
- Логи конвертации выводятся в консоль при использовании флага `-s`

---

**Статус:** Готово к запуску ✅

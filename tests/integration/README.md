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

**Тест 5: test_dp2epf_conversion**
- Конвертация EDT обработки в EPF файл
- Проверяет создание выходного .epf и его размер

**Тест 6: test_dp2epf_env_config**
- Проверка корректности параметров в test_dp2epf.env
- Верификация путей и структуры исходного EDT проекта обработки

**Тест 7: test_conf2xml_conversion**
- Конвертация CF конфигурации в XML
- Проверяет наличие выходной директории и файла Configuration.xml

**Тест 8: test_conf2edt_conversion**
- Конвертация CF конфигурации в EDT проект
- Проверяет наличие .project, DT-INF и src

**Тест 9: test_ext2xml_conversion**
- Конвертация CFE расширения в XML
- Проверяет наличие выходной директории и Configuration.xml

**Тест 10: test_ext2edt_conversion**
- Конвертация CFE расширения в EDT проект
- Проверяет наличие .project, DT-INF и src

**Тест 11: test_subprocess_encoding**
- Запуск конвертации через subprocess (как в GUI)
- Проверяет корректную декодировку вывода (UTF-8/CP1251/CP866) и отсутствие ошибок кодировки

**Тест 12: test_dp2epf_xml_conversion**
- Конвертация XML обработки в EPF
- Проверяет корректное определение типа источника и создание .epf

**Тест 13: test_dp2epf_xml_with_base_ib_conversion**
- Конвертация XML обработки в EPF с использованием базовой ИБ (V8_BASE_IB)
- Проверяет создание/очистку тестовой ИБ и успешный вывод .epf

**Тест 14: test_edt_validate_conversion**
- Валидация EDT проекта конфигурации
- Создаёт отчет validation_report.txt и выводит статистику

**Тест 15: test_edt_validate_structure_check**
- Проверка структуры EDT проекта перед валидацией (обязательные каталоги/метаданные)

**Тест 16: test_edt_validate_with_explicit_report_path**
- Валидация с явным указанием пути к отчету (файл вместо каталога)

**Тест 17: test_edt_validate_subprocess_encoding**
- Валидация через subprocess с проверкой кодировок и созданием отчета

**Тест 18: test_conf2ib_from_edt**
- Конвертация EDT конфигурации в файловую ИБ (каталог)
- Проверяет создание каталога ИБ и наличие файла 1Cv8.1CD

**Тест 19: test_ib2cf_from_file_ib**
- Выгрузка конфигурации из файловой ИБ в CF
- Предварительно создаётся ИБ из XML, затем выгрузка CF

**Тест 20: test_ib2xml_from_file_ib**
- Выгрузка конфигурации из файловой ИБ в XML
- Предварительно создаётся ИБ из XML, затем выгрузка XML и наличие Configuration.xml

**Тест 21: test_ib2edt_via_conf2edt**
- Конвертация файловой ИБ в EDT через ScriptName=conf2edt
- Проверяет наличие .project, DT-INF и src в выходном проекте

**Тест 22: test_conf2xml_clean_dst_on**
- Проверка очистки каталога назначения при V8_CONF_CLEAN_DST=1 для CF → XML
- Подтверждает удаление «мусорных» файлов до выгрузки

**Тест 23: test_conf2xml_clean_dst_off**
- Проверка отсутствия очистки при V8_CONF_CLEAN_DST=0 для CF → XML
- Подтверждает сохранение «мусорных» файлов

**Тест 24: test_conf2cf_from_xml_with_ibcmd_when_available**
- Конвертация XML → CF с V8_CONVERT_TOOL=ibcmd
- Пропускается, если IBCMD_TOOL не настроен

**Тест 25: test_ib2cf_from_server_ib**
- Выгрузка конфигурации из серверной ИБ в CF (без IBCMD; используется 1cv8.exe DESIGNER)
- Этапы:
  - Формирование /IBConnectionString вида `Srvr=<server>;Ref=<base>;` из пути `/Sserver\base`
  - Выгрузка конфигурации в CF через DESIGNER (/DumpCfg)
- Проверки:
  - CF создан и его размер больше 0
- Использует V8_SRC_PATH в формате `/Sserver\base` и учетные данные

**Тест 26: test_ib2xml_from_server_ib**
- Выгрузка конфигурации из серверной ИБ в XML (без IBCMD; используется 1cv8.exe DESIGNER)
- Этапы:
  - Подготовка выходной директории; опциональная очистка при `V8_CONF_CLEAN_DST=1`
  - Выгрузка конфигурации в XML через DESIGNER (/DumpConfigToFiles)
- Проверки:
  - Наличие `Configuration.xml` и его ненулевой размер

**Тест 27: test_ib2edt_from_server_ib**
- Конвертация серверной ИБ в EDT через ScriptName=conf2edt (без IBCMD)
- Этапы:
  - ИБ → XML: выгрузка через 1cv8.exe DESIGNER в временный каталог
  - XML → EDT: импорт в EDT проект через 1cedtcli/ring, workspace создаётся автоматически
- Проверки:
  - В выходном проекте присутствуют `.project`, `DT-INF`, `src`
  - Имя каталога проекта соответствует Ref серверной базы

**Тест 28: test_ib2xml_from_server_ib_ibcmd_with_ib_server**
- Выгрузка конфигурации из серверной ИБ в XML через IBCMD при заданном `V8_IB_SERVER`
- Этапы:
  - Подготовка выходной директории; опциональная очистка при `V8_CONF_CLEAN_DST=1`
  - Выгрузка конфигурации в XML через IBCMD
- Проверки:
  - Наличие `Configuration.xml` и его ненулевой размер
- Использует IBCMD_TOOL и параметры серверной БД из base_test.env

**Тест 29: test_ib2xml_from_file_ib_ibcmd**
- Выгрузка конфигурации из файловой ИБ в XML через IBCMD
- Этапы:
  - CF → XML: подготовка XML из `tests/fixtures/edt_xml/demo_otus_edt.cf`
  - XML → IB: создание временной файловой ИБ
  - IB → XML: выгрузка конфигурации в XML через IBCMD
- Проверки:
  - Наличие `Configuration.xml` и его ненулевой размер
- Использует IBCMD_TOOL и параметры из base_test.env

**Тест 32: test_conf2ib_from_xml_to_server_ib_designer**
- Загрузка XML конфигурации в серверную ИБ через 1cv8.exe (DESIGNER)
- Этапы:
  - Очистка серверной базы загрузкой пустого CF (`tests/fixtures/edt_xml/ПустаяКонфигурация.cf`)
  - Импорт XML (`tests/fixtures/cf/ConfXML`) в `/Skantor\test_for_1c_convert_kit_2ib`
  - Верификация: выгрузка в XML через DESIGNER и проверка `Configuration.xml`

**Тест 33: test_conf2ib_from_xml_to_server_ib_ibcmd**
- Загрузка XML конфигурации в серверную ИБ через IBCMD
- Этапы:
  - Очистка серверной базы пустым CF
  - Импорт XML в `/Skantor\test_for_1c_convert_kit_2ib` через IBCMD
  - Верификация: выгрузка в XML через DESIGNER
- Примечание: пропускается, если параметры серверной БД для IBCMD не настроены или импорт недоступен

**Тест 34: test_load_cf_to_server_ib_designer**
- Загрузка CF конфигурации (`tests/fixtures/edt_xml/demo_otus_edt.cf`) в серверную ИБ через DESIGNER
- Этапы:
  - Очистка пустым CF
  - Загрузка CF
  - Верификация: выгрузка в XML через DESIGNER и проверка `Configuration.xml`

**Тест 35: test_conf2ib_from_cf_to_server_ib_ibcmd**
- Загрузка CF конфигурации в серверную ИБ через IBCMD
- Этапы:
  - Очистка серверной базы пустым CF
  - Импорт CF (`tests/fixtures/edt_xml/demo_otus_edt.cf`) в `/Skantor\test_for_1c_convert_kit_2ib` через IBCMD
  - Верификация: выгрузка в XML через DESIGNER
- Примечание: пропускается, если параметры серверной БД для IBCMD не настроены или импорт недоступен

**Тест 30: test_ib2cf_from_server_ib_ibcmd**
- Выгрузка конфигурации из серверной ИБ в CF через IBCMD
- Этапы:
  - Формирование /IBConnectionString вида `Srvr=<server>;Ref=<base>;` из пути `/Sserver\base`
  - Выгрузка конфигурации в CF через IBCMD
- Проверки:
  - CF создан и его размер больше 0
- Использует IBCMD_TOOL и параметры серверной БД из base_test.env

**Тест 31: test_ib2edt_from_server_ib_ibcmd**
- Конвертация серверной ИБ в EDT через ScriptName=conf2edt с использованием IBCMD
- Этапы:
  - ИБ → XML: выгрузка через IBCMD в временный каталог
  - XML → EDT: импорт в EDT проект через 1cedtcli/ring, workspace создаётся автоматически
- Проверки:
  - В выходном проекте присутствуют `.project`, `DT-INF`, `src`
  - Имя каталога проекта соответствует Ref серверной базы
- Использует IBCMD_TOOL и параметры серверной БД из base_test.env

### test_debug_commands.py

**Тест: test_demo_edt_cf_debug_commands**
- Запуск конвертации в режиме отладки для проекта «Демо_edt_в_cf»
- Извлечение команд из лога и поэтапное ручное выполнение
- Проверка успешного создания итогового CF

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

### Параметры для серверной ИБ:
- Укажите учетные данные для подключения:
```env
V8_IB_USER="Администратор"
V8_IB_PWD="123456"
```
- Для серверной ИБ используйте формат пути:
```env
V8_SRC_PATH="/S<server>\<base>"
# пример:
V8_SRC_PATH="/Skantor\test_for_1c_convert_kit"
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
... все тесты PASSED ...
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

**Предложенные дополнительные интеграционные тесты**

- Конфигурации:
  - conf2ib (EDT/XML → IB): создание файловой ИБ, проверка 1Cv8.1CD
  - ib2cf (IB → CF): выгрузка конфигурации из файловой ИБ в CF
  - ib2xml (IB → XML): выгрузка конфигурации из файловой ИБ в XML и наличие Configuration.xml
  - ib2edt (IB → EDT): выгрузка конфигурации из файловой ИБ в EDT-формат и проверка, что результата в формате EDT
  - Переключение инструмента (designer/ibcmd): дублирование ключевых сценариев c V8_CONVERT_TOOL=ibcmd
  - Очистка каталога назначения: проверка V8_CONF_CLEAN_DST=1/0 для XML/EDT сценариев

- Расширения:
  - ext2ib (EDT/XML/CFE → IB): загрузка расширения в тестовую ИБ и проверка наличия
  - Очистка каталога назначения: проверка V8_EXT_CLEAN_DST=1/0 для XML/EDT сценариев

- Обработки/Отчеты:
  - dp2erf (если доступно): выгрузка отчета в ERF
  - dp XML → EDT → EPF: цепочка с промежуточными форматами и проверками структуры

- Надежность и ошибки:
  - Неверные пути инструментов (V8_TOOL/EDTCLI_TOOL) → ожидаемая ошибка и код выхода
  - Некорректные значения V8_DST_PATH для разных ScriptName → валидатор выдаёт ValidationError
  - Проверка сохранения временных файлов при ошибке (preserve_on_error)

- Производительность/устойчивость:
  - Большие проекты (smoke) с замером времени и размеров результатов
  - Параллельный запуск двух конвертаций в разные выходные каталоги

**Статус:** Готово к запуску ✅

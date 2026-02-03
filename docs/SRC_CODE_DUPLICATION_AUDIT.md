# Аудит дублирования кода в `src/`

Дата: 2026-02-03

Ниже перечислены найденные случаи дублирования (идентичные/почти идентичные блоки логики) и перечень исправлений. Разделы сгруппированы по структуре `src/`, внутри — по критичности (риск рассинхронизации поведения, вероятность дефектов, стоимость сопровождения).

---

## `src/converters/`

### Высокая критичность

- **Подготовка базовой ИБ (единая бизнес-логика продублирована)**  
  Где: [_prepare_base_ib (DataProcessorConverter)](file:///f:/1C/Projects/1c-convert-kit/src/converters/dataprocessor/converter.py#L108-L223), [_prepare_base_ib (ExtensionConverter)](file:///f:/1C/Projects/1c-convert-kit/src/converters/extension/converter.py#L155-L274)  
  Почему критично: при правках формата строки подключения, проверок путей, логики создания/загрузки ИБ можно легко исправить только один конвертер и получить расхождение поведения.  
  Что сделать: вынести общую реализацию в один метод (варианты: в `BaseConverter`, в общий миксин для конвертеров, либо в утилиту уровня `converters/`), оставив различия только в сообщениях/параметрах.

- **Импорт XML → EDT (почти полностью одинаковый блок)**  
  Где: [ConfigurationConverter, блок импорта в EDT](file:///f:/1C/Projects/1c-convert-kit/src/converters/configuration/converter.py#L659-L744), [ExtensionConverter, блок импорта в EDT](file:///f:/1C/Projects/1c-convert-kit/src/converters/extension/converter.py#L765-L855)  
  Почему критично: это “критический путь” конвертации; любая доработка (например, параметры `ring/edtcli`, логирование, обработка кодировок/retcode) должна быть синхронной.  
  Что сделать: выделить общий метод “import_configuration_files_to_edt_project(...)” (например, в `EdtToolWrapper` или общий helper в `converters/base/tools.py`) и использовать его в обоих конвертерах.

### Средняя критичность

- **Дублирование цикла конвертации файлов обработок/отчетов (EDT→XML→EPF/ERF и XML→EPF/ERF)**  
  Где: [DataProcessorConverter, цикл загрузки файлов (EDT ветка)](file:///f:/1C/Projects/1c-convert-kit/src/converters/dataprocessor/converter.py#L311-L366), [DataProcessorConverter, цикл загрузки файлов (XML ветка)](file:///f:/1C/Projects/1c-convert-kit/src/converters/dataprocessor/converter.py#L394-L449)  
  Почему: дублирование поддерживается сложно, но находится внутри одного файла, поэтому риск рассинхронизации чуть ниже.  
  Что сделать: вынести общий “проход по processor_files” в приватный метод, принимающий `xml_path`, `progress_base/progress_span` и текст этапа.

- **Повторяющийся код добавления учетных данных к команде 1С в `V8ToolWrapper`**  
  Где: [tools.py, добавление `/N` и `/P` (DumpCfg)](file:///f:/1C/Projects/1c-convert-kit/src/converters/base/tools.py#L340-L347), [tools.py, добавление `/N` и `/P` (LoadExternalDataProcessorOrReportFromFiles)](file:///f:/1C/Projects/1c-convert-kit/src/converters/base/tools.py#L430-L437)  
  Почему: при изменении правил передачи учетных данных (или добавлении дополнительных параметров безопасности) придется править в нескольких местах; легко забыть одно.  
  Что сделать: выделить helper уровня класса (например, `_append_ib_credentials(cmd: list[str])`) и переиспользовать.

### Низкая критичность

- **Повторяющиеся “скользящие” блоки (пересекающиеся окна) в отчете детектора**  
  Примечание: автоматический поиск блоков фиксировал и пересечения (один и тот же участок кода в разных окнах длиной 30 строк). Это не отдельные дефекты, а эффект метода поиска; фактические точки вынесены выше.

---

## `src/core/`

### Высокая критичность

- **Дублирование инфраструктуры вывода (цвета/логирование) с разными политиками обработки кодировок**  
  Где: [core Colors](file:///f:/1C/Projects/1c-convert-kit/src/core/convert.py#L19-L37), [base Colors](file:///f:/1C/Projects/1c-convert-kit/src/converters/base/converter.py#L52-L74), а также функции печати в [convert.py](file:///f:/1C/Projects/1c-convert-kit/src/core/convert.py#L39-L57) vs методы [Logger](file:///f:/1C/Projects/1c-convert-kit/src/converters/base/converter.py#L76-L129)  
  Почему критично: при исправлениях вывода ошибок/кодировок/ANSI поведения можно легко получить два разных поведения CLI/конвертеров и повторно ловить “символы-кракозябры” или скрытые ошибки в одном из режимов.  
  Что сделать: выбрать “единственный источник истины” (либо использовать `Logger` в `core/convert.py`, либо перенести общую инфраструктуру в отдельный модуль и импортировать и оттуда).

### Средняя критичность

- **Дублирование парсинга `.env` (частичное)**  
  Где: [load_env_file](file:///f:/1C/Projects/1c-convert-kit/src/core/convert.py#L59-L89), [ProjectScanner._read_env_data](file:///f:/1C/Projects/1c-convert-kit/src/gui/project_scanner.py#L82-L109)  
  Почему: риск меньше (GUI читает только 2 поля), но изменения формата `.env` или поддержки BOM/кодировок придется вносить как минимум в 2 места.  
  Что сделать: в GUI использовать `load_env_file(..., silent=True)` и брать `ScriptName`/`V8_DST_PATH` из результата.

---

## `src/gui/`

### Средняя критичность

- **Повторяющаяся логика создания проекта и копирования проекта (создание папки, генерация `.env`, обновление таблицы, выбор строки)**  
  Где: [_add_project](file:///f:/1C/Projects/1c-convert-kit/src/gui/main_window.py#L694-L742), [_copy_project](file:///f:/1C/Projects/1c-convert-kit/src/gui/main_window.py#L809-L865)  
  Почему: высокая “стоимость сопровождения” при изменении формата `.env` или UI-логики (надо менять в двух местах); риск рассинхронизации средний (все в одном классе).  
  Что сделать: вынести общий метод наподобие `_create_project_from_dialog_result(result, success_message)` или общий “pipeline” (создать папку → записать env → пересканировать → выбрать строку → обновить таблицу).

### Низкая критичность

- **Повторяющийся импорт FreeSimpleGUI/PySimpleGUI (одинаковый try/except)**  
  Где: [main.py](file:///f:/1C/Projects/1c-convert-kit/src/gui/main.py#L9-L14), [main_window.py](file:///f:/1C/Projects/1c-convert-kit/src/gui/main_window.py#L17-L22), [project_editor.py](file:///f:/1C/Projects/1c-convert-kit/src/gui/project_editor.py#L13-L18)  
  Почему: риск дефектов низкий, но создает шум и увеличивает размер диффов при миграции GUI-библиотеки.  
  Что сделать: централизовать импорт в одном модуле GUI и импортировать `sg` оттуда.

- **Дублирование форматирования длительности**  
  Где: [gui utils.format_duration](file:///f:/1C/Projects/1c-convert-kit/src/gui/utils.py#L8-L37), [base format_duration](file:///f:/1C/Projects/1c-convert-kit/src/converters/base/converter.py#L20-L49)  
  Почему: риск низкий, но приводит к мелким рассинхронизациям формата вывода и необходимости править в двух местах.  
  Что сделать: оставить одну реализацию и переиспользовать ее (например, вынести в общий `src/utils` и импортировать из GUI и converters).

---

## `src/config/`

### Низкая критичность

- Существенных дублей кода не обнаружено (в каталоге в основном шаблоны/данные).

---

## `src/utils/`

### Низкая критичность

- Существенных дублей кода не обнаружено (пакет пока почти пустой). Потенциальная точка для консолидации общих утилит, если решите “разъезжающиеся” функции (например, `format_duration`) собрать в одном месте.


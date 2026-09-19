# Валидатор EDT-проектов 1С

`ValidationConverter` проверяет структуру EDT-проекта, запускает валидацию через `1cedtcli` или `ring` и сохраняет отчет TSV.

## Параметры

Обязательные:

- `ScriptName=edt-validate`
- `V8_SRC_PATH` — каталог EDT-проекта
- `V8_DST_PATH` — путь к отчету или каталог, в котором будет создан `validation_report.txt`

Необязательные:

- `EDTCLI_TOOL` — путь к `1cedtcli.exe`
- `RING_TOOL` — путь к `ring.bat`
- `V8_EDT_VERSION` — версия EDT для поиска инструмента

## Что проверяется

Перед запуском EDT-инструмента конвертер проверяет:

- каталог `DT-INF`;
- файл `.project`;
- каталог `src`;
- метаданные конфигурации или расширения.

Затем `1cedtcli` или `ring` записывает замечания в TSV-отчет. Конвертер подсчитывает проблемы по уровням и выводит критические замечания в лог.

## Пример

```env
ScriptName=edt-validate
V8_SRC_PATH=C:\Projects\MyConfiguration
V8_DST_PATH=C:\Reports\validation_report.txt
EDTCLI_TOOL=C:\Program Files\1C\1CE\components\1c-edt-2025.2.3\1cedtcli.exe
```

Запуск:

```bash
python src/core/convert.py --env projects/MyValidationProject
```

## Коды возврата

- `0` — валидация завершена;
- `1` — параметры или структура проекта некорректны, EDT-инструмент не найден или завершился с ошибкой.

Полная настройка, примеры отчета и разбор ошибок описаны в [руководстве по валидации](../../../docs/VALIDATION_GUIDE.md).

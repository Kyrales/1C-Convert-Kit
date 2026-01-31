# Legacy CMD скрипты валидации

## Статус: УСТАРЕЛО

Эти CMD скрипты больше **НЕ ИСПОЛЬЗУЮТСЯ** в текущей версии приложения.

## История

Ранее валидация EDT проектов выполнялась через CMD скрипт:
- `edt-validate.cmd` - валидация EDT проекта с помощью ring/edtcli

## Текущая реализация

Вся функциональность перенесена в Python класс **ValidationConverter**:
- Расположение: `src/converters/validation/converter.py`
- Использует объектно-ориентированный подход
- Интегрирован с ConverterRegistry
- Поддерживает валидацию EDT проектов

## Использование

Для валидации EDT проектов используйте:

```python
from converters.validation.converter import ValidationConverter

env_vars = {
    'V8_SRC_PATH': '/path/to/edt/project',
    'V8_EDT_VERSION': '2025.1.5',  # Опционально
    # ... другие параметры
}

converter = ValidationConverter(env_vars)
converter.validate()
result = converter.convert()  # Выполняет валидацию

if result == 0:
    print("Валидация успешна!")
else:
    print("Обнаружены ошибки валидации")
```

Или через CLI:
```bash
python src/core/convert.py --env projects/MyEDTProject
```

## Особенности

ValidationConverter:
- Проверяет что источник является EDT проектом
- Использует ring или edtcli для валидации
- Не создает выходных файлов (только валидация)
- Возвращает код ошибки при наличии проблем

## Причины миграции

1. **Устранение дублирования кода** - общая логика вынесена в BaseConverter
2. **Автоматический поиск инструментов** - EdtToolWrapper находит ring/edtcli
3. **Лучшая тестируемость** - Python код легче тестировать
4. **Единообразная обработка ошибок** - централизованная обработка
5. **Интеграция** - работает через общий ConverterRegistry

## Сохранение

Эти файлы сохранены только для истории и справки. Они не участвуют в работе приложения.

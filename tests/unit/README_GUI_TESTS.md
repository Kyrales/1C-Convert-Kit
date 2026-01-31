# GUI Тесты

Тесты для графического интерфейса приложения 1C-Convert-Kit.

## Список тестов

### test_simple_dialog.py
Простой тест открытия диалога редактирования проекта.

**Проверяет:**
- Диалог открывается без ошибок
- Все элементы создаются корректно
- Нет исключений при инициализации

**Запуск:**
```bash
cd tests/unit
python test_simple_dialog.py
```

### test_clipboard.py
Тест работы буфера обмена в диалоге редактирования проекта.

**Проверяет:**
- Контекстное меню (правый клик)
- Горячие клавиши Ctrl+C/V/X/A/Z
- Копирование/вставка текста между полями

**Запуск:**
```bash
cd tests/unit
python test_clipboard.py
```

**Тестовый сценарий:**
1. Введите текст в поле V8_VERSION: "8.3.23.2040"
2. Выделите "8.3.23" мышью
3. Нажмите Ctrl+C (или правый клик → Копировать)
4. Перейдите в другое поле
5. Нажмите Ctrl+V (или правый клик → Вставить)
6. Проверьте, что текст вставился

### test_editor_improvements.py
Комплексный тест всех улучшений диалога редактирования проекта.

**Проверяет:**
1. Кнопка "?" показывает описание параметра
2. Ctrl+C / Ctrl+V работает в полях ввода
3. Кнопка "..." открывает диалог выбора файла/папки
4. Недоступные поля имеют темный фон
5. Доступные поля имеют светлый фон

**Запуск:**
```bash
cd tests/unit
python test_editor_improvements.py
```

## Общие требования

### Зависимости
- Python 3.7+
- FreeSimpleGUI или PySimpleGUI
- src.gui модули

### Запуск из корня проекта
```bash
# Один тест
python tests/unit/test_simple_dialog.py

# Все GUI тесты
python -m pytest tests/unit/test_*dialog*.py -v
python -m pytest tests/unit/test_clipboard.py -v
python -m pytest tests/unit/test_editor_improvements.py -v
```

## Примечания

- Тесты требуют графического окружения (GUI)
- Тесты интерактивные - требуют действий пользователя
- Для автоматизированного тестирования используйте unit-тесты без GUI
- Тесты используют реальные данные из `src/config/params_descriptions.json`

## Структура тестов

```
tests/unit/
├── test_simple_dialog.py          # Базовый тест открытия диалога
├── test_clipboard.py              # Тест буфера обмена
├── test_editor_improvements.py    # Комплексный тест улучшений
└── README_GUI_TESTS.md           # Эта документация
```

## Troubleshooting

### Ошибка импорта
```
ModuleNotFoundError: No module named 'src'
```
**Решение:** Запускайте тесты из корня проекта или добавьте корень в PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%CD%          # Windows CMD
```

### Ошибка "No display"
```
_tkinter.TclError: no display name and no $DISPLAY environment variable
```
**Решение:** Тесты требуют графического окружения. Запускайте на машине с GUI или используйте Xvfb для headless режима.

### Диалог не открывается
**Решение:** Проверьте, что файл `src/config/params_descriptions.json` существует и содержит корректные данные.

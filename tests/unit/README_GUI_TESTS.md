# GUI Тесты

Тесты для графического интерфейса приложения 1C-Convert-Kit.

## Типы тестов

### 🤖 Автоматизированные тесты (рекомендуется)

Эти тесты запускаются автоматически без участия пользователя.

#### test_project_editor_unit.py
**Unit-тесты логики без GUI** - тестируют методы класса без открытия окон.

**Проверяет:**
- Создание диалога
- Получение списка скриптов
- Получение параметров скрипта
- Определение типа параметра
- Валидацию имени проекта
- Обработку недопустимых символов
- Проверку дубликатов
- Замену пробелов в именах файлов
- Получение описаний параметров

**Запуск:**
```bash
# Из корня проекта
python tests/unit/test_project_editor_unit.py

# Или через pytest
pytest tests/unit/test_project_editor_unit.py -v
```

**Преимущества:**
- ✅ Не требует GUI
- ✅ Быстрое выполнение
- ✅ Можно запускать в CI/CD
- ✅ Автоматическая проверка

#### test_project_editor_auto.py
**Автоматизированный GUI тест** - открывает форму и автоматически закрывает через 3 секунды.

**Проверяет:**
- Диалог открывается без ошибок
- Автоматическое закрытие работает
- Множественные диалоги работают корректно
- Все режимы (add, edit, copy) функционируют

**Запуск:**
```bash
# Из корня проекта
python tests/unit/test_project_editor_auto.py
```

**Преимущества:**
- ✅ Автоматическое закрытие через таймер
- ✅ Не требует ручного взаимодействия
- ✅ Проверяет реальное открытие GUI
- ✅ Тестирует все режимы

---

### 👤 Интерактивные тесты (для ручного тестирования)

Эти тесты требуют действий пользователя и ручного закрытия формы.

#### test_simple_dialog.py
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

⚠️ **Требует ручного закрытия формы**

#### test_clipboard.py
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

⚠️ **Требует ручного взаимодействия и закрытия формы**

#### test_editor_improvements.py
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

⚠️ **Требует ручного взаимодействия и закрытия формы**

---

## Рекомендуемый порядок запуска

### Для автоматизированного тестирования:
```bash
# 1. Unit-тесты (без GUI)
python tests/unit/test_project_editor_unit.py

# 2. Автоматизированный GUI тест
python tests/unit/test_project_editor_auto.py

# Или все вместе через pytest
pytest tests/unit/test_project_editor_unit.py tests/unit/test_project_editor_auto.py -v
```

### Для ручного тестирования функциональности:
```bash
# Интерактивные тесты (требуют ручного закрытия)
python tests/unit/test_simple_dialog.py
python tests/unit/test_clipboard.py
python tests/unit/test_editor_improvements.py
```

## Общие требования

### Зависимости
- Python 3.7+
- FreeSimpleGUI или PySimpleGUI
- src.gui модули

### Запуск из корня проекта
```bash
# Автоматизированные тесты
python tests/unit/test_project_editor_unit.py      # Unit-тесты
python tests/unit/test_project_editor_auto.py      # GUI с автозакрытием

# Интерактивные тесты
python tests/unit/test_simple_dialog.py
python tests/unit/test_clipboard.py
python tests/unit/test_editor_improvements.py

# Все тесты через pytest
python -m pytest tests/unit/test_project_editor_unit.py -v
```

## Примечания

- **Автоматизированные тесты** не требуют ручного взаимодействия
- **Интерактивные тесты** требуют действий пользователя и ручного закрытия
- Для CI/CD используйте только автоматизированные тесты
- Интерактивные тесты полезны для проверки UX и визуальных аспектов

### Поведение в headless режиме (без GUI)

| Тест | Headless режим | Exit code | Примечание |
|------|----------------|-----------|------------|
| `test_project_editor_unit.py` | ✅ Работает | 0 | Не требует GUI |
| `test_project_editor_auto.py` | ⊘ Пропускается | 0 | Автоматически определяет отсутствие GUI |
| `test_simple_dialog.py` | ⊘ Пропускается | 0 | Автоматически определяет отсутствие GUI |
| `test_clipboard.py` | ⊘ Пропускается | 0 | Автоматически определяет отсутствие GUI |
| `test_editor_improvements.py` | ⊘ Пропускается | 0 | Автоматически определяет отсутствие GUI |

**Для CI/CD пайплайнов:**
```yaml
# GitHub Actions / GitLab CI
- name: Run unit tests
  run: python tests/unit/test_project_editor_unit.py

# Опционально: GUI тесты с Xvfb
- name: Run GUI tests
  run: xvfb-run python tests/unit/test_project_editor_auto.py
```

## Структура тестов

```
tests/unit/
├── test_project_editor_unit.py    # 🤖 Unit-тесты (автоматические)
├── test_project_editor_auto.py    # 🤖 GUI с автозакрытием (автоматические)
├── test_simple_dialog.py          # 👤 Базовый тест (интерактивный)
├── test_clipboard.py              # 👤 Тест буфера обмена (интерактивный)
├── test_editor_improvements.py    # 👤 Комплексный тест (интерактивный)
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
**Решение:** 
- **test_project_editor_unit.py** - не требует GUI, работает в headless режиме ✅
- **test_project_editor_auto.py** - автоматически пропускается в headless режиме (exit code 0)
- **Интерактивные тесты** - требуют графическое окружение

**Для headless окружения (CI/CD):**
```bash
# Используйте только unit-тесты
python tests/unit/test_project_editor_unit.py

# Или с виртуальным дисплеем (Xvfb)
xvfb-run python tests/unit/test_project_editor_auto.py
```

**Для Windows Server без GUI:**
```bash
# Только unit-тесты
python tests/unit/test_project_editor_unit.py
```

### Диалог не открывается
**Решение:** Проверьте, что файл `src/config/params_descriptions.json` существует и содержит корректные данные.

### Тесты зависают
**Решение:** Используйте автоматизированные тесты:
- `test_project_editor_unit.py` - не открывает GUI
- `test_project_editor_auto.py` - автоматически закрывается через 3 секунды


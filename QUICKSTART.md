# 🚀 Быстрый старт - 1c-convert-kit

## Текущий статус проекта

✅ Структура создана
✅ Файлы скопированы
⚠️ Требуется адаптация кода (см. TODO.md)

---

## Что нужно сделать СЕЙЧАС

### 1. Откройте проект в редакторе
```bash
cd f:\1C\Projects\1c-convert-kit
code .  # или другой редактор
```

### 2. Выполните критические задачи из TODO.md

#### Задача 1: Адаптация src/gui/main.py

Откройте `src/gui/main.py` и замените:

```python
# БЫЛО:
from convert import load_env_file

SCRIPT_DIR = Path(__file__).parent
PROJECTS_DIR = SCRIPT_DIR
CONVERT_SCRIPT = SCRIPT_DIR / 'convert.py'
PARAMS_DESC_FILE = SCRIPT_DIR / 'params_descriptions.json'

# СТАЛО:
from ..core.convert import load_env_file

SCRIPT_DIR = Path(__file__).parent.parent.parent  # Корень проекта
PROJECTS_DIR = SCRIPT_DIR / 'projects'
CONVERT_SCRIPT = SCRIPT_DIR / 'src' / 'core' / 'convert.py'
PARAMS_DESC_FILE = SCRIPT_DIR / 'src' / 'config' / 'params_descriptions.json'
```

#### Задача 2: Адаптация src/core/convert.py

Откройте `src/core/convert.py` и найдите функцию `run_conversion()`.

Замените строку:
```python
# БЫЛО:
script_dir = Path(__file__).parent / 'scripts'

# СТАЛО:
script_dir = Path(__file__).parent.parent / 'converters'
```

Добавьте функцию поиска legacy скриптов (после импортов):
```python
def find_legacy_script(script_name: str) -> Optional[Path]:
    """Находит legacy CMD скрипт в соответствующей папке"""
    converters_dir = Path(__file__).parent.parent / 'converters'
    
    # Определяем тип скрипта по имени
    if script_name.startswith('conf'):
        legacy_dir = converters_dir / 'configuration' / 'legacy'
    elif script_name.startswith('dp'):
        legacy_dir = converters_dir / 'dataprocessor' / 'legacy'
    elif script_name.startswith('ext'):
        legacy_dir = converters_dir / 'extension' / 'legacy'
    elif script_name.startswith('edt'):
        legacy_dir = converters_dir / 'validation' / 'legacy'
    else:
        return None
    
    script_path = legacy_dir / script_name
    return script_path if script_path.exists() else None
```

Замените в функции `run_conversion()`:
```python
# БЫЛО:
conversion_script = script_dir / script_name

# СТАЛО:
conversion_script = find_legacy_script(script_name)
```

Также найдите строку с поиском базового .env:
```python
# БЫЛО:
script_dir = Path(__file__).parent

# СТАЛО:
script_dir = Path(__file__).parent.parent.parent / 'projects'
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустите GUI

```bash
run_gui.cmd
```

или

```bash
python src\gui\main.py
```

### 5. Проверьте работоспособность

- [ ] GUI открылся без ошибок
- [ ] В таблице отображаются проекты из `projects/`
- [ ] При выборе проекта отображаются детали
- [ ] Можно запустить конвертацию (выберите тестовый проект)
- [ ] Лог отображается в реальном времени

---

## Если что-то не работает

### Ошибка импорта
```
ModuleNotFoundError: No module named 'core'
```
**Решение:** Проверьте, что вы запускаете из корня проекта и исправили импорты в main.py

### Ошибка "Скрипт не найден"
```
Скрипт dp2epf.cmd не найден
```
**Решение:** Проверьте, что функция `find_legacy_script()` добавлена в convert.py

### Ошибка "Проекты не отображаются"
```
Таблица пустая
```
**Решение:** Проверьте, что путь PROJECTS_DIR указывает на `SCRIPT_DIR / 'projects'`

### Ошибка "params_descriptions.json не найден"
```
FileNotFoundError: params_descriptions.json
```
**Решение:** Проверьте путь PARAMS_DESC_FILE в main.py

---

## Следующие шаги

После успешного запуска:

1. ✅ Отметьте выполненные задачи в TODO.md
2. 📚 Создайте документацию (см. TODO.md, раздел "Документация")
3. 🧪 Добавьте тесты
4. 🏗️ Начните рефакторинг (по желанию)

---

## Полезные команды

```bash
# Запуск GUI
python src\gui\main.py

# Запуск конвертации через CLI
python src\core\convert.py --env projects\МойПроект

# Запуск тестов (когда будут готовы)
pytest tests/

# Проверка кода
flake8 src/
black src/ --check
```

---

## Структура проекта (краткая)

```
1c-convert-kit/
├── src/
│   ├── gui/main.py              ← Главный GUI (требует правки)
│   ├── core/convert.py          ← Логика конвертации (требует правки)
│   ├── config/
│   │   └── params_descriptions.json
│   └── converters/
│       ├── configuration/legacy/  ← CMD скрипты конфигураций
│       ├── dataprocessor/legacy/  ← CMD скрипты обработок
│       ├── extension/legacy/      ← CMD скрипты расширений
│       └── validation/legacy/     ← CMD скрипты валидации
├── projects/                    ← Ваши проекты (уже скопированы)
├── run_gui.cmd                  ← Быстрый запуск
└── TODO.md                      ← Полный план работ
```

---

**Удачи! 🚀**

Если возникнут вопросы - смотрите TODO.md или README.md

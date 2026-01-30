# Проекты конвертации

Эта папка содержит ваши рабочие проекты для конвертации файлов 1С.

## Структура проекта

Каждый проект должен находиться в отдельной папке и содержать:

1. **Один или несколько .env файлов** с настройками
2. **Обязательный параметр ScriptName** - имя скрипта конвертации

### Пример структуры:

```
projects/
├── base_1.env                    # Базовая конфигурация (общая для всех проектов)
└── МойПроект/                    # Папка проекта
    └── project.env               # Настройки проекта
```

## Создание нового проекта

### Шаг 1: Создайте базовую конфигурацию (если еще не создана)

Скопируйте шаблон:
```bash
copy ..\src\config\base.env.template base_1.env
```

Отредактируйте `base_1.env` и укажите:
- `V8_VERSION` - версия платформы 1С
- `V8_TOOL` - путь к 1cv8.exe
- `EDTCLI_TOOL` - путь к 1cedtcli.exe
- `V8_TEMP` - путь для временных файлов

### Шаг 2: Создайте папку проекта

```bash
mkdir МойПроект
cd МойПроект
```

### Шаг 3: Создайте .env файл проекта

Создайте файл `project.env` со следующим содержимым:

```env
# Имя скрипта конвертации (обязательно!)
ScriptName=dp2epf.cmd

# Путь к исходникам
V8_SRC_PATH=f:\1C\Sources\МояОбработка

# Путь для сохранения результата
V8_DST_PATH=f:\1C\Output
```

### Доступные скрипты конвертации:

#### Конфигурации:
- `conf2cf.cmd` - в CF файл
- `conf2xml.cmd` - в XML
- `conf2edt.cmd` - в EDT проект
- `conf2ib.cmd` - в информационную базу

#### Обработки/Отчеты:
- `dp2epf.cmd` - в EPF/ERF файл
- `dp2xml.cmd` - в XML
- `dp2edt.cmd` - в EDT проект

#### Расширения:
- `ext2cfe.cmd` - в CFE файл
- `ext2xml.cmd` - в XML
- `ext2edt.cmd` - в EDT проект
- `ext2ib.cmd` - в информационную базу

#### Валидация:
- `edt-validate.cmd` - валидация EDT проекта

## Параметры .env файлов

### Общие параметры (base_1.env):
- `V8_VERSION` - версия платформы 1С
- `V8_EDT_VERSION` - версия EDT
- `V8_TOOL` - путь к 1cv8.exe
- `EDTCLI_TOOL` - путь к 1cedtcli.exe
- `RING_TOOL` - путь к ring.cmd
- `V8_TEMP` - каталог для временных файлов
- `V8_ENCODING` - кодировка вывода (по умолчанию: 65001)

### Параметры проекта (project.env):
- `ScriptName` - имя скрипта конвертации (обязательно!)
- `V8_SRC_PATH` - путь к источнику
- `V8_DST_PATH` - путь назначения
- `V8_EXT_NAME` - имя расширения (для ext2* скриптов)

Полное описание параметров см. в `src/config/params_descriptions.json`

## Примеры

### Пример 1: Конвертация обработки из EDT в EPF

```env
ScriptName=dp2epf.cmd
V8_SRC_PATH=f:\1C\Projects\MyProject\src\DataProcessors\MyProcessor
V8_DST_PATH=f:\1C\Output
```

### Пример 2: Конвертация конфигурации из XML в CF

```env
ScriptName=conf2cf.cmd
V8_SRC_PATH=f:\1C\Configs\MyConfig\xml
V8_DST_PATH=f:\1C\Output\MyConfig.cf
```

### Пример 3: Конвертация расширения в CFE

```env
ScriptName=ext2cfe.cmd
V8_SRC_PATH=f:\1C\Extensions\MyExtension
V8_DST_PATH=f:\1C\Output\MyExtension.cfe
V8_EXT_NAME=MyExtension
```

## Использование через GUI

1. Запустите `run_gui.cmd` из корня проекта
2. В таблице отобразятся все проекты из этой папки
3. Выберите нужные проекты (кликните по строке)
4. Нажмите "ВЫПОЛНИТЬ"
5. Следите за прогрессом в логе

## Использование через командную строку

```bash
python src\core\convert.py --env projects\МойПроект
```

С переопределением пути назначения:
```bash
python src\core\convert.py --env projects\МойПроект --output f:\NewOutput
```

## Примечания

- Базовый .env файл загружается автоматически
- Параметры из project.env переопределяют параметры из base_1.env
- Пути с пробелами автоматически заключаются в кавычки
- Относительные пути преобразуются в абсолютные

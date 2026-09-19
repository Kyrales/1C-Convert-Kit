# Проекты конвертации

В этой папке хранятся общие настройки и проектные `.env`-файлы для запуска конвертаций через GUI или командную строку.

## Структура

```text
projects/
├── base.env                 # Общие настройки для всех проектов
└── МойПроект/
    └── project.env          # Настройки конкретного проекта
```

Все `.env`-файлы из корня `projects/` загружаются как базовые. Затем к ним применяются файлы выбранного проекта, поэтому проектные значения переопределяют общие.

## Создание проекта

1. Создайте базовую конфигурацию из [шаблона](../src/config/base.env.template):

   ```powershell
   Copy-Item ..\src\config\base.env.template .\base.env
   ```

2. Укажите в `base.env` общие параметры, например пути к платформе, EDT и временному каталогу:

   ```env
   V8_VERSION=8.5.1.1522
   V8_TOOL="C:\Program Files\1cv8\8.5.1.1522\bin\1cv8.exe"
   IBCMD_TOOL="C:\Program Files\1cv8\8.5.1.1522\bin\ibcmd.exe"
   EDTCLI_TOOL="C:\Program Files\1C\1CE\components\1c-edt-2025.2.3\1cedtcli.exe"
   V8_TEMP=C:\Temp\1c-convert-kit
   ```

3. Создайте каталог проекта и файл `project.env`:

   ```env
   ScriptName=dp2epf
   V8_SRC_PATH=F:\1C\Sources\МояОбработка
   V8_DST_PATH=F:\1C\Output
   ```

`ScriptName` указывается **без расширения `.cmd`**.

## Доступные сценарии

### Конфигурации и информационные базы

- `conf2cf` — конфигурация → CF
- `conf2xml` — конфигурация → проект XML
- `conf2edt` — конфигурация → проект EDT
- `conf2ib` — конфигурация → информационная база
- `dt2ib` — DT → информационная база
- `ib2dt` — информационная база → DT

### Обработки и отчеты

- `dp2epf` — обработка → EPF
- `dp2erf` — отчет → ERF
- `dp2xml` — обработка или отчет → проект XML
- `dp2edt` — обработка или отчет → проект EDT

### Расширения

- `ext2cfe` — расширение → CFE
- `ext2xml` — расширение → XML
- `ext2edt` — расширение → EDT
- `ext2ib` — расширение → информационная база

### Валидация

- `edt-validate` — проверка EDT-проекта

## Основные параметры

- `ScriptName` — сценарий конвертации.
- `V8_SRC_PATH` — источник.
- `V8_DST_PATH` — назначение.
- `V8_CONVERT_TOOL` — инструмент для операций с конфигурациями, расширениями и DT/ИБ: `designer` по умолчанию или `ibcmd`.
- `V8_IB_USER`, `V8_IB_PWD` — учетные данные пользователя информационной базы.
- `V8_EXT_NAME` — имя расширения для сценариев `ext2*`.
- `V8_TEMP_AFTER_CLEAN=0` — сохранить временные файлы после успешной конвертации; при значении `1` они удаляются.

Для `ibcmd` при необходимости задаются `IBCMD_TOOL`, `IBCMD_DATA`, `V8_DB_SRV_DBMS`, `V8_IB_SERVER`, `V8_IB_NAME`, `V8_DB_SRV_USR` и `V8_DB_SRV_PWD`.

Полный перечень и описание параметров находятся в [params_descriptions.json](../src/config/params_descriptions.json), а зависимости параметров — в [params_depend.json](../src/config/params_depend.json).

## Обновление информационной базы после загрузки

Параметр `V8_IB_UPDATE` доступен для `conf2ib`, `dt2ib` и `ext2ib`:

- `V8_IB_UPDATE=0` — не обновлять конфигурацию базы данных после загрузки; значение по умолчанию.
- `V8_IB_UPDATE=1` — выполнить обновление после загрузки.

Для `dt2ib` восстановление DT в любом случае заменяет содержимое целевой базы. `V8_IB_UPDATE` управляет только последующим обновлением конфигурации базы данных.

## Ссылки на информационные базы

Файловую базу можно задать обычным путем или строкой соединения `/F`:

```env
V8_DST_PATH=F:\1C\Bases\Demo
# или
V8_DST_PATH=/FF:\1C\Bases\Demo
```

Серверная база задается строкой `/Sсервер\база`:

```env
V8_DST_PATH=/Sserver1c\Demo
```

Для `ib2dt` ссылка на базу указывается в `V8_SRC_PATH`, а путь к DT-файлу — в `V8_DST_PATH`.

## Примеры

### Восстановление DT в базу с последующим обновлением

```env
ScriptName=dt2ib
V8_SRC_PATH=F:\1C\Backups\Demo.dt
V8_DST_PATH=/Sserver1c\Demo
V8_CONVERT_TOOL=designer
V8_IB_UPDATE=1
```

Чтобы восстановить DT без последующего обновления, удалите `V8_IB_UPDATE` или установите `0`.

### Выгрузка базы в DT через ibcmd

```env
ScriptName=ib2dt
V8_SRC_PATH=/Sserver1c\Demo
V8_DST_PATH=F:\1C\Backups\Demo.dt
V8_CONVERT_TOOL=ibcmd
```

Параметры доступа к СУБД для `ibcmd` обычно удобно хранить в `base.env`.

### Загрузка конфигурации в базу

```env
ScriptName=conf2ib
V8_SRC_PATH=F:\1C\Configs\Demo.cf
V8_DST_PATH=F:\1C\Bases\Demo
V8_IB_UPDATE=1
```

### Загрузка расширения в базу

```env
ScriptName=ext2ib
V8_SRC_PATH=F:\1C\Extensions\MyExtension.cfe
V8_DST_PATH=/Sserver1c\Demo
V8_EXT_NAME=MyExtension
V8_IB_UPDATE=1
```

## Запуск

Через GUI:

```powershell
python src\gui\main.py
```

Также можно использовать `run_gui.cmd` или `run_gui.sh` из корня репозитория.

Через командную строку:

```powershell
python src\core\convert.py --env projects\МойПроект
```

С переопределением пути назначения:

```powershell
python src\core\convert.py --env projects\МойПроект --output F:\NewOutput
```

Файлы читаются с поддержкой `utf-8-sig`, `utf-8` и `cp1251`; комментарии и значения в кавычках поддерживаются. Дополнительное описание возможностей и архитектуры см. в [основном README](../README.md).

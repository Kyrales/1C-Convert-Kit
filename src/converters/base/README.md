# Базовые классы конвертеров

## Описание

Модуль `base` содержит базовые классы и утилиты для всех конвертеров 1С:Предприятие.

## Компоненты

### BaseConverter

Абстрактный базовый класс для всех конвертеров. Предоставляет общую функциональность:

- **Валидация параметров** - проверка обязательных параметров из .env файлов
- **Управление временными файлами** - создание и очистка временных директорий
- **Определение типа источника** - автоматическое определение EDT/XML/InfoBase
- **Единообразное логирование** - цветной вывод на русском языке
- **Обработка ошибок** - сохранение временных файлов при ошибках

### Logger

Класс для единообразного логирования с цветным выводом:

```python
from converters.base.converter import Logger

logger = Logger()
logger.info("Информационное сообщение")
logger.success("Успешное выполнение")
logger.warning("Предупреждение")
logger.error("Ошибка")
```

**Цветовая схема:**
- 🔵 ИНФО - синий
- 🟢 УСПЕХ - зеленый
- 🟡 ПРЕДУПРЕЖДЕНИЕ - желтый
- 🔴 ОШИБКА - красный

### SourceType

Enum для типов источников:

```python
from converters.base.converter import SourceType

SourceType.EDT        # EDT проект
SourceType.XML        # XML файлы
SourceType.INFOBASE   # Информационная база
SourceType.UNKNOWN    # Неизвестный тип
```

### SourceDetector

Класс для определения типа источника:

```python
from converters.base.converter import SourceDetector

detector = SourceDetector()
source_type = detector.detect('/path/to/source')

if source_type == SourceType.EDT:
    print("Это EDT проект")
elif source_type == SourceType.XML:
    print("Это XML директория")
elif source_type == SourceType.INFOBASE:
    print("Это информационная база")
```

**Логика определения:**
- EDT: наличие директории `DT-INF` и файла `.project`
- InfoBase: путь начинается с `/F` или содержит файл `1Cv8.1CD`
- XML: наличие XML файлов конфигурации/расширения
- Unknown: не удалось определить тип

### TempFileManager

Класс для управления временными файлами:

```python
from converters.base.converter import TempFileManager

manager = TempFileManager(base_dir='/path/to/temp')

# Создание временной директории
temp_dir = manager.create_temp_dir('MyConverter')
# Результат: /path/to/temp/MyConverter_20260202_153045

# Очистка временных файлов
manager.cleanup()

# Сохранение временных файлов (при ошибке)
manager.preserve()
```

### ToolOutputParser

Класс для парсинга вывода инструментов 1С:

```python
from converters.base.converter import ToolOutputParser

parser = ToolOutputParser()

# Очистка ANSI escape кодов
clean_output = parser.clean_ansi(raw_output)

# Определение кодировки вывода
encoding = parser.detect_encoding(raw_bytes)

# Парсинг ошибок
errors = parser.parse_errors(output)
```

## Tool Wrappers (tools.py)

Абстракции для работы с инструментами 1С:Предприятие.

### ToolWrapper

Базовый класс для всех обёрток инструментов:

```python
from converters.base.tools import ToolWrapper

class MyTool(ToolWrapper):
    def get_command(self, *args):
        return [self.tool_path, *args]
```

### V8ToolWrapper

Обёртка для работы с 1cv8.exe (designer):

```python
from pathlib import Path

from converters.base.converter import Logger
from converters.base.tools import V8ToolWrapper

env_vars = {
    'V8_VERSION': '8.3.27.1989',
    'V8_TOOL': r'C:/Program Files/1cv8/8.3.27.1989/bin/1cv8.exe',
    'V8_IB_USER': '',
    'V8_IB_PWD': ''
}

logger = Logger()
tool = V8ToolWrapper(env_vars, logger)

# Примеры операций
log_file = Path('v8_designer.log')
ib_connection = r'File=C:/temp/tmp_db;'
xml_path = Path('C:/temp/tmp_xml')

exit_code = tool.create_infobase(ib_connection, log_file)
exit_code = tool.load_config_from_files(ib_connection, xml_path, log_file)
exit_code = tool.dump_config_to_files(ib_connection, Path('C:/Output/XML'), log_file)
```

### IbcmdToolWrapper

Обёртка для работы с ibcmd.exe:

```python
from pathlib import Path

from converters.base.converter import Logger
from converters.base.tools import IbcmdToolWrapper

env_vars = {
    'V8_VERSION': '8.3.27.1989',
    'IBCMD_TOOL': r'C:/Program Files/1cv8/8.3.27.1989/bin/ibcmd.exe',
    'IBCMD_DATA': r'C:/temp/ibcmd_data',
    'V8_TEMP': r'C:/temp'
}

logger = Logger()
tool = IbcmdToolWrapper(env_vars, logger)

exit_code = tool.create_infobase_with_config(
    db_path=Path('C:/temp/tmp_db'),
    xml_path=Path('C:/temp/tmp_xml')
)
```

### EdtToolWrapper

Обёртка для работы с 1cedtcli/ring:

```python
from pathlib import Path

from converters.base.converter import Logger
from converters.base.tools import EdtToolWrapper

env_vars = {
    'EDTCLI_TOOL': r'C:/Program Files/1C/1CE/components/1c-edt-2025.1.5/1cedtcli.exe',
    'RING_TOOL': r'C:/Program Files/1C/1CE/components/1c-enterprise-ring-*/ring.bat',
    'V8_EDT_VERSION': '2025.1.5'
}

logger = Logger()
tool = EdtToolWrapper(env_vars, logger)

exit_code = tool.export_to_xml(
    edt_project=Path('C:/Projects/MyProject'),
    xml_output=Path('C:/Output/XML'),
    workspace=Path('C:/Workspaces/temp_ws')
)
```

## Создание нового конвертера

Чтобы добавить конвертер:

1. Наследоваться от `BaseConverter`
2. Реализовать абстрактные методы
3. Зарегистрировать в `ConverterRegistry`

### Пример:

```python
from converters.base.converter import BaseConverter, SourceType

class MyConverter(BaseConverter):
    """Мой новый конвертер"""
    
    SCRIPT_NAMES = ['my-convert']  # Типы конвертации
    
    def __init__(self, env_vars, silent=False):
        super().__init__(env_vars, silent)
        self.logger.info("Инициализация MyConverter")
    
    def validate(self):
        """Валидация параметров"""
        super().validate()
        
        # Проверка обязательных параметров
        required = ['V8_SRC_PATH', 'V8_DST_PATH']
        for param in required:
            if not self.env_vars.get(param):
                raise ValueError(f"Отсутствует параметр: {param}")
        
        # Проверка типа источника
        if self.source_type not in [SourceType.EDT, SourceType.XML]:
            raise ValueError("Поддерживаются только EDT и XML")
    
    def convert(self):
        """Выполнение конвертации"""
        try:
            self.logger.info("Начало конвертации...")
            
            # Логика конвертации
            # ...
            
            self.logger.success("Конвертация завершена успешно")
            return 0
            
        except Exception as e:
            self.logger.error(f"Ошибка конвертации: {e}")
            self.temp_manager.preserve()
            return 1
```

## Общие параметры .env

Все конвертеры поддерживают следующие параметры:

### Обязательные:
- `V8_SRC_PATH` - путь к источнику
- `V8_DST_PATH` - путь к результату
- `ScriptName` - тип конвертации

### Опциональные:
- `V8_TEMP` - директория для временных файлов (по умолчанию `temp/`)
- `V8_VERSION` - версия платформы 1С (по умолчанию `8.3.27.1989`)
- `V8_TOOL` - путь к 1cv8.exe
- `IBCMD_TOOL` - путь к ibcmd.exe
- `RING_TOOL` - путь к ring.bat
- `EDTCLI_TOOL` - путь к 1cedtcli.exe
- `V8_EDT_VERSION` - версия EDT (по умолчанию `2025.1.5`)

## Обработка ошибок

Все конвертеры следуют единой логике обработки ошибок:

1. При возникновении ошибки выводится подробное сообщение
2. Временные файлы сохраняются для отладки
3. Путь к временным файлам выводится в консоль
4. Возвращается код ошибки 1

## Логирование

Все конвертеры используют единый формат логирования:

```
[ИНФО] Информационное сообщение
[УСПЕХ] Операция выполнена успешно
[ПРЕДУПРЕЖДЕНИЕ] Предупреждение о потенциальной проблеме
[ОШИБКА] Описание ошибки
```

## Тестирование

Базовые классы покрыты unit-тестами:

```bash
# Запуск тестов базовых классов
pytest tests/unit/test_base_converter.py
pytest tests/unit/test_tool_wrappers.py
```

## См. также

- [ConfigurationConverter](../configuration/README.md) - конвертер конфигураций
- [DataProcessorConverter](../dataprocessor/README.md) - конвертер обработок/отчетов
- [ExtensionConverter](../extension/README.md) - конвертер расширений
- [ValidationConverter](../validation/README.md) - валидатор EDT проектов
- [ConverterRegistry](../registry.py) - реестр конвертеров

# Дизайн: Рефакторинг конвертеров с CMD на Python

## 1. Обзор архитектуры

### 1.1 Принципы дизайна
- **DRY (Don't Repeat Yourself)**: Вся общая логика в базовом классе
- **Open/Closed**: Легко добавлять новые конвертеры без изменения существующего кода
- **Single Responsibility**: Каждый класс отвечает за одну задачу
- **Dependency Injection**: Инструменты передаются в конвертеры как зависимости

### 1.2 Архитектурные слои

```
┌─────────────────────────────────────────────────┐
│           CLI / GUI Interface Layer             │
│              (convert.py, main.py)              │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Converter Registry Layer               │
│            (registry.py)                        │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Converter Implementation Layer         │
│  (ConfigurationConverter, DataProcessorConverter│
│   ExtensionConverter, ValidationConverter)      │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│            Base Converter Layer                 │
│         (BaseConverter, SourceDetector)         │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│            Tool Abstraction Layer               │
│  (V8ToolWrapper, IbcmdToolWrapper, EdtToolWrapper)│
└─────────────────────────────────────────────────┘
```

## 2. Детальный дизайн классов

### 2.1 Базовый слой (src/converters/base/)

#### 2.1.1 BaseConverter (converter.py)

**Назначение:** Абстрактный базовый класс для всех конвертеров.

**Атрибуты:**
```python
class BaseConverter(ABC):
    def __init__(self, env_vars: Dict[str, str], silent: bool = False):
        self.env_vars = env_vars
        self.silent = silent
        self.src_path = env_vars.get('V8_SRC_PATH', '')
        self.dst_path = env_vars.get('V8_DST_PATH', '')
        self.temp_dir = None
        self.logger = Logger(silent)
        self.cleanup_on_success = True
        self.cleanup_on_error = False
```

**Методы:**
- `validate() -> None`: Валидация параметров (обязательные поля, пути)
- `convert() -> int`: Главный метод конвертации (шаблонный метод)
- `cleanup() -> None`: Очистка временных файлов
- `detect_source_type() -> SourceType`: Определение типа источника (EDT/XML/IB)
- `create_temp_dir() -> Path`: Создание временной директории
- `log_info(message: str)`: Логирование информации
- `log_error(message: str)`: Логирование ошибки
- `log_warning(message: str)`: Логирование предупреждения
- `log_success(message: str)`: Логирование успеха

**Абстрактные методы:**
- `_do_convert() -> int`: Реализация конвертации (переопределяется в наследниках)
- `_validate_specific() -> None`: Специфичная валидация (переопределяется в наследниках)
- `get_output_extension() -> str`: Расширение выходного файла (.cf, .cfe, .epf)


#### 2.1.2 Logger (converter.py)

**Назначение:** Единообразное логирование с цветным выводом.

```python
class Logger:
    def __init__(self, silent: bool = False):
        self.silent = silent
        Colors.enable_windows_colors()
    
    def info(self, message: str):
        if not self.silent:
            print(f"{Colors.GREEN}[ИНФО]{Colors.RESET} {message}")
    
    def error(self, message: str):
        if not self.silent:
            print(f"{Colors.RED}[ОШИБКА]{Colors.RESET} {message}")
    
    def warning(self, message: str):
        if not self.silent:
            print(f"{Colors.YELLOW}[ПРЕДУПРЕЖДЕНИЕ]{Colors.RESET} {message}")
    
    def success(self, message: str):
        if not self.silent:
            print(f"{Colors.GREEN}[УСПЕХ]{Colors.RESET} {message}")
```

#### 2.1.3 SourceType (converter.py)

**Назначение:** Enum для типов источников.

```python
from enum import Enum

class SourceType(Enum):
    EDT = "edt"           # 1C:EDT проект
    XML = "xml"           # 1C:Designer XML файлы
    FILE_IB = "file_ib"   # Файловая информационная база
    SERVER_IB = "server_ib"  # Серверная информационная база
    CF_FILE = "cf"        # Файл конфигурации .cf
    UNKNOWN = "unknown"
```


#### 2.1.4 SourceDetector (converter.py)

**Назначение:** Определение типа источника по пути.

```python
class SourceDetector:
    @staticmethod
    def detect(path: str) -> SourceType:
        """Определяет тип источника по пути"""
        path_obj = Path(path)
        
        # Проверка на EDT проект
        if (path_obj / 'DT-INF').exists():
            return SourceType.EDT
        
        # Проверка на XML файлы
        if (path_obj / 'Configuration.xml').exists():
            return SourceType.XML
        
        # Проверка на файловую ИБ
        if (path_obj / '1cv8.1cd').exists():
            return SourceType.FILE_IB
        
        # Проверка на серверную ИБ (формат /Sserver\basename)
        if path.startswith('/S'):
            return SourceType.SERVER_IB
        
        # Проверка на файловую ИБ (формат /Fpath)
        if path.startswith('/F'):
            return SourceType.FILE_IB
        
        # Проверка на .cf файл
        if path_obj.suffix.lower() == '.cf':
            return SourceType.CF_FILE
        
        return SourceType.UNKNOWN
```


### 2.2 Слой абстракций инструментов (src/converters/base/tools.py)

#### 2.2.1 ToolWrapper (базовый класс)

```python
class ToolWrapper(ABC):
    def __init__(self, env_vars: Dict[str, str], logger: Logger):
        self.env_vars = env_vars
        self.logger = logger
        self.tool_path = None
    
    @abstractmethod
    def find_tool(self) -> Optional[Path]:
        """Находит инструмент в системе"""
        pass
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> subprocess.CompletedProcess:
        """Выполняет команду инструмента"""
        pass
    
    def is_available(self) -> bool:
        """Проверяет доступность инструмента"""
        return self.find_tool() is not None
```

#### 2.2.2 V8ToolWrapper (1cv8.exe / Designer)

```python
class V8ToolWrapper(ToolWrapper):
    def find_tool(self) -> Optional[Path]:
        # Проверяем переменную V8_TOOL
        if 'V8_TOOL' in self.env_vars:
            tool_path = Path(self.env_vars['V8_TOOL'].strip('"'))
            if tool_path.exists():
                return tool_path
        
        # Ищем по версии V8_VERSION
        version = self.env_vars.get('V8_VERSION', '8.3.23.2040')
        default_path = Path(f"C:/Program Files/1cv8/{version}/bin/1cv8.exe")
        if default_path.exists():
            return default_path
        
        return None
    
    def create_infobase(self, ib_connection: str, log_file: Path) -> int:
        """Создает информационную базу"""
        pass
    
    def load_config_from_files(self, ib_connection: str, xml_path: Path, 
                               log_file: Path, extension_name: str = None) -> int:
        """Загружает конфигурацию из XML файлов"""
        pass
    
    def dump_config(self, ib_connection: str, output_file: Path, 
                    log_file: Path, extension_name: str = None) -> int:
        """Выгружает конфигурацию в .cf/.cfe файл"""
        pass
    
    def load_external_processor(self, ib_connection: str, xml_file: Path,
                                output_dir: Path, log_file: Path) -> int:
        """Загружает внешнюю обработку/отчет"""
        pass
```


#### 2.2.3 IbcmdToolWrapper (ibcmd.exe)

```python
class IbcmdToolWrapper(ToolWrapper):
    def find_tool(self) -> Optional[Path]:
        # Проверяем переменную IBCMD_TOOL
        if 'IBCMD_TOOL' in self.env_vars:
            tool_path = Path(self.env_vars['IBCMD_TOOL'].strip('"'))
            if tool_path.exists():
                return tool_path
        
        # Ищем по версии V8_VERSION
        version = self.env_vars.get('V8_VERSION', '8.3.23.2040')
        default_path = Path(f"C:/Program Files/1cv8/{version}/bin/ibcmd.exe")
        if default_path.exists():
            return default_path
        
        return None
    
    def create_infobase_with_config(self, db_path: Path, xml_path: Path) -> int:
        """Создает ИБ и загружает конфигурацию"""
        pass
    
    def save_config(self, db_path: Path, output_file: Path, 
                    extension_name: str = None) -> int:
        """Сохраняет конфигурацию в файл"""
        pass
```

#### 2.2.4 EdtToolWrapper (ring / edtcli)

```python
class EdtToolWrapper(ToolWrapper):
    def __init__(self, env_vars: Dict[str, str], logger: Logger):
        super().__init__(env_vars, logger)
        self.use_ring = False
        self.use_edtcli = False
    
    def find_tool(self) -> Optional[Path]:
        # Сначала ищем ring
        ring_path = self._find_ring()
        if ring_path:
            self.use_ring = True
            return ring_path
        
        # Затем ищем edtcli
        edtcli_path = self._find_edtcli()
        if edtcli_path:
            self.use_edtcli = True
            return edtcli_path
        
        return None
    
    def _find_ring(self) -> Optional[Path]:
        """Ищет ring.bat в PATH"""
        pass
    
    def _find_edtcli(self) -> Optional[Path]:
        """Ищет 1cedtcli.exe"""
        pass
    
    def export_to_xml(self, edt_project: Path, xml_output: Path, 
                      workspace: Path) -> int:
        """Экспортирует EDT проект в XML"""
        pass
```


### 2.3 Слой конвертеров

#### 2.3.1 ConfigurationConverter (src/converters/configuration/converter.py)

**Назначение:** Конвертация конфигураций (EDT/XML/IB → CF).

```python
class ConfigurationConverter(BaseConverter):
    def __init__(self, env_vars: Dict[str, str], silent: bool = False):
        super().__init__(env_vars, silent)
        self.convert_tool = env_vars.get('V8_CONVERT_TOOL', 'designer')
        self.v8_tool = V8ToolWrapper(env_vars, self.logger)
        self.ibcmd_tool = IbcmdToolWrapper(env_vars, self.logger)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        return '.cf'
    
    def _validate_specific(self) -> None:
        # Проверка что dst_path - это файл с расширением .cf
        if not self.dst_path.endswith('.cf'):
            raise ValueError("V8_DST_PATH должен указывать на файл .cf")
    
    def _do_convert(self) -> int:
        source_type = self.detect_source_type()
        
        if source_type == SourceType.EDT:
            return self._convert_from_edt()
        elif source_type == SourceType.XML:
            return self._convert_from_xml()
        elif source_type in [SourceType.FILE_IB, SourceType.SERVER_IB]:
            return self._convert_from_ib()
        else:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type}")
    
    def _convert_from_edt(self) -> int:
        """EDT → XML → IB → CF"""
        pass
    
    def _convert_from_xml(self) -> int:
        """XML → IB → CF"""
        pass
    
    def _convert_from_ib(self) -> int:
        """IB → CF"""
        pass
```


#### 2.3.2 DataProcessorConverter (src/converters/dataprocessor/converter.py)

**Назначение:** Конвертация обработок и отчетов (EDT/XML → EPF/ERF).

```python
class DataProcessorConverter(BaseConverter):
    def __init__(self, env_vars: Dict[str, str], silent: bool = False):
        super().__init__(env_vars, silent)
        self.base_ib = env_vars.get('V8_BASE_IB', '')
        self.base_config = env_vars.get('V8_BASE_CONFIG', '')
        self.v8_tool = V8ToolWrapper(env_vars, self.logger)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        # Определяется динамически (.epf или .erf)
        return '.epf'
    
    def _validate_specific(self) -> None:
        # Проверка что dst_path - это директория
        dst_path_obj = Path(self.dst_path)
        if dst_path_obj.suffix in ['.epf', '.erf']:
            raise ValueError("V8_DST_PATH должен указывать на директорию, а не файл")
    
    def _do_convert(self) -> int:
        source_type = self.detect_source_type()
        
        if source_type == SourceType.EDT:
            return self._convert_from_edt()
        elif source_type == SourceType.XML:
            return self._convert_from_xml()
        else:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type}")
    
    def _prepare_base_ib(self) -> str:
        """Подготавливает базовую ИБ для загрузки обработок"""
        pass
    
    def _convert_from_edt(self) -> int:
        """EDT → XML → EPF/ERF"""
        pass
    
    def _convert_from_xml(self) -> int:
        """XML → EPF/ERF"""
        pass
```


#### 2.3.3 ExtensionConverter (src/converters/extension/converter.py)

**Назначение:** Конвертация расширений (EDT/XML/IB → CFE).

```python
class ExtensionConverter(BaseConverter):
    def __init__(self, env_vars: Dict[str, str], silent: bool = False):
        super().__init__(env_vars, silent)
        self.ext_name = env_vars.get('V8_EXT_NAME', '')
        self.base_ib = env_vars.get('V8_BASE_IB', '')
        self.base_config = env_vars.get('V8_BASE_CONFIG', '')
        self.convert_tool = env_vars.get('V8_CONVERT_TOOL', 'designer')
        self.v8_tool = V8ToolWrapper(env_vars, self.logger)
        self.ibcmd_tool = IbcmdToolWrapper(env_vars, self.logger)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        return '.cfe'
    
    def _validate_specific(self) -> None:
        # Проверка обязательного параметра V8_EXT_NAME
        if not self.ext_name:
            raise ValueError("Не указан параметр V8_EXT_NAME (имя расширения)")
        
        # Проверка что dst_path - это файл с расширением .cfe
        if not self.dst_path.endswith('.cfe'):
            raise ValueError("V8_DST_PATH должен указывать на файл .cfe")
    
    def _do_convert(self) -> int:
        source_type = self.detect_source_type()
        
        if source_type == SourceType.EDT:
            return self._convert_from_edt()
        elif source_type == SourceType.XML:
            return self._convert_from_xml()
        elif source_type in [SourceType.FILE_IB, SourceType.SERVER_IB]:
            return self._convert_from_ib()
        else:
            raise ValueError(f"Неподдерживаемый тип источника: {source_type}")
    
    def _prepare_base_ib(self) -> str:
        """Подготавливает базовую ИБ для загрузки расширения"""
        pass
    
    def _convert_from_edt(self) -> int:
        """EDT → XML → IB → CFE"""
        pass
    
    def _convert_from_xml(self) -> int:
        """XML → IB → CFE"""
        pass
    
    def _convert_from_ib(self) -> int:
        """IB → CFE"""
        pass
```


#### 2.3.4 ValidationConverter (src/converters/validation/converter.py)

**Назначение:** Валидация EDT проектов.

```python
class ValidationConverter(BaseConverter):
    def __init__(self, env_vars: Dict[str, str], silent: bool = False):
        super().__init__(env_vars, silent)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        return ''  # Нет выходного файла
    
    def _validate_specific(self) -> None:
        # Проверка что источник - это EDT проект
        source_type = self.detect_source_type()
        if source_type != SourceType.EDT:
            raise ValueError("Источник должен быть EDT проектом")
    
    def _do_convert(self) -> int:
        """Выполняет валидацию EDT проекта"""
        self.logger.info(f"Валидация EDT проекта: {self.src_path}")
        # Здесь будет вызов EDT валидатора
        return 0
```

### 2.4 Реестр конвертеров (src/converters/registry.py)

```python
class ConverterRegistry:
    def __init__(self):
        self._converters = {}
        self._discover_converters()
    
    def _discover_converters(self):
        """Автоматически находит все конвертеры"""
        # Импортируем все модули конвертеров
        from converters.configuration.converter import ConfigurationConverter
        from converters.dataprocessor.converter import DataProcessorConverter
        from converters.extension.converter import ExtensionConverter
        from converters.validation.converter import ValidationConverter
        
        # Регистрируем конвертеры по типам конвертации
        self.register('conf2cf', ConfigurationConverter)
        self.register('conf2xml', ConfigurationConverter)
        self.register('conf2edt', ConfigurationConverter)
        
        self.register('dp2epf', DataProcessorConverter)
        self.register('dp2erf', DataProcessorConverter)
        self.register('dp2xml', DataProcessorConverter)
        self.register('dp2edt', DataProcessorConverter)
        
        self.register('ext2cfe', ExtensionConverter)
        self.register('ext2xml', ExtensionConverter)
        self.register('ext2edt', ExtensionConverter)
        
        self.register('edt-validate', ValidationConverter)
    
    def register(self, script_name: str, converter_class: Type[BaseConverter]):
        """Регистрирует конвертер"""
        self._converters[script_name] = converter_class
    
    def get_converter(self, script_name: str) -> Optional[Type[BaseConverter]]:
        """Получает класс конвертера по имени скрипта"""
        return self._converters.get(script_name)
    
    def list_converters(self) -> List[str]:
        """Возвращает список всех зарегистрированных конвертеров"""
        return list(self._converters.keys())
```


## 3. Интеграция с convert.py

### 3.1 Обновленная функция run_conversion

```python
def run_conversion(env_files, output_path=None):
    """
    Запускает конвертацию используя Python конвертеры
    
    Args:
        env_files: список путей к .env файлам
        output_path: путь для сохранения результата (опционально)
        
    Returns:
        int: код возврата (0 - успех, 1 - ошибка)
    """
    # Получаем абсолютные пути к .env файлам
    env_files = [os.path.abspath(f) for f in env_files]
    
    # Загружаем и объединяем переменные из всех .env файлов
    env_vars = merge_env_files(env_files)
    if env_vars is None:
        return 1
    
    # Переопределяем путь назначения если передан
    if output_path:
        env_vars['V8_DST_PATH'] = os.path.abspath(output_path)
    
    # Получаем тип конвертации из ScriptName
    script_name = env_vars.get('ScriptName')
    if not script_name:
        print_error("Переменная ScriptName не определена в .env файлах")
        return 1
    
    # Получаем конвертер из реестра
    registry = ConverterRegistry()
    converter_class = registry.get_converter(script_name)
    
    if not converter_class:
        print_error(f"Конвертер для '{script_name}' не найден")
        print_error(f"Доступные конвертеры: {', '.join(registry.list_converters())}")
        return 1
    
    # Создаем и запускаем конвертер
    try:
        converter = converter_class(env_vars)
        converter.validate()
        exit_code = converter.convert()
        
        if exit_code == 0:
            converter.cleanup()
        
        return exit_code
        
    except Exception as e:
        print_error(f"Ошибка при выполнении конвертации: {e}")
        return 1
```

### 3.2 Удаляемые функции

Следующие функции будут удалены из convert.py:
- `find_legacy_script()` - больше не нужна
- `get_output_file_info()` - логика перенесена в конвертеры
- Код запуска CMD скриптов через subprocess

Следующие функции остаются без изменений:
- `load_env_file()` - используется конвертерами
- `merge_env_files()` - используется конвертерами
- `find_env_files()` - используется в main()
- `Colors` класс - используется для логирования


## 4. Обработка ошибок

### 4.1 Стратегия обработки ошибок

```python
class ConversionError(Exception):
    """Базовое исключение для ошибок конвертации"""
    def __init__(self, message: str, temp_dir: Optional[Path] = None):
        super().__init__(message)
        self.temp_dir = temp_dir

class ValidationError(ConversionError):
    """Ошибка валидации параметров"""
    pass

class ToolNotFoundError(ConversionError):
    """Инструмент не найден"""
    pass

class ToolExecutionError(ConversionError):
    """Ошибка выполнения инструмента"""
    def __init__(self, message: str, tool_output: str, temp_dir: Optional[Path] = None):
        super().__init__(message, temp_dir)
        self.tool_output = tool_output
```

### 4.2 Обработка в BaseConverter

```python
def convert(self) -> int:
    """Главный метод конвертации с обработкой ошибок"""
    try:
        self.logger.info("Начало конвертации...")
        
        # Создаем временную директорию
        self.temp_dir = self.create_temp_dir()
        
        # Выполняем конвертацию
        result = self._do_convert()
        
        if result == 0:
            self.logger.success("Конвертация завершена успешно")
            if self.cleanup_on_success:
                self.cleanup()
        else:
            self.logger.error(f"Конвертация завершилась с ошибкой (код: {result})")
            if not self.cleanup_on_error:
                self.logger.warning(f"Временные файлы сохранены: {self.temp_dir}")
        
        return result
        
    except ValidationError as e:
        self.logger.error(f"Ошибка валидации: {e}")
        return 1
        
    except ToolNotFoundError as e:
        self.logger.error(f"Инструмент не найден: {e}")
        return 1
        
    except ToolExecutionError as e:
        self.logger.error(f"Ошибка выполнения инструмента: {e}")
        if e.tool_output:
            self.logger.error("Вывод инструмента:")
            for line in e.tool_output.split('\n'):
                if line.strip():
                    self.logger.error(f"  {line}")
        if e.temp_dir:
            self.logger.warning(f"Временные файлы сохранены: {e.temp_dir}")
        return 1
        
    except Exception as e:
        self.logger.error(f"Неожиданная ошибка: {e}")
        if self.temp_dir:
            self.logger.warning(f"Временные файлы сохранены: {self.temp_dir}")
        return 1
```

### 4.3 Парсинг вывода инструментов

```python
class ToolOutputParser:
    """Парсер вывода инструментов 1С"""
    
    # Список кодировок для попытки чтения (в порядке приоритета)
    ENCODINGS = ['utf-8', 'cp1251', 'cp866', 'latin-1']
    
    @staticmethod
    def read_file_with_encoding(file_path: Path) -> Optional[str]:
        """
        Читает файл, пробуя разные кодировки
        
        Args:
            file_path: путь к файлу
            
        Returns:
            str: содержимое файла или None если не удалось прочитать
        """
        if not file_path.exists():
            return None
        
        # Пробуем разные кодировки
        for encoding in ToolOutputParser.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Если ни одна кодировка не подошла, используем замену ошибочных символов
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception:
            return None
    
    @staticmethod
    def parse_designer_log(log_file: Path) -> List[str]:
        """
        Парсит лог файл designer и извлекает ошибки
        
        Args:
            log_file: путь к лог-файлу
            
        Returns:
            list: список строк с ошибками
        """
        errors = []
        content = ToolOutputParser.read_file_with_encoding(log_file)
        
        if content:
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('[INFO]'):
                    errors.append(line)
        
        return errors
    
    @staticmethod
    def has_errors(log_file: Path) -> bool:
        """
        Проверяет наличие ошибок в логе
        
        Args:
            log_file: путь к лог-файлу
            
        Returns:
            bool: True если есть ошибки
        """
        errors = ToolOutputParser.parse_designer_log(log_file)
        return len(errors) > 0
```


## 5. Управление временными файлами

### 5.1 Стратегия управления

```python
class TempFileManager:
    """Менеджер временных файлов"""
    
    def __init__(self, base_temp_dir: str, converter_name: str):
        self.base_temp_dir = Path(base_temp_dir)
        self.converter_name = converter_name
        self.temp_dir = None
    
    def create_temp_dir(self) -> Path:
        """Создает временную директорию"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.temp_dir = self.base_temp_dir / f"{self.converter_name}_{timestamp}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir
    
    def cleanup(self, force: bool = False):
        """Удаляет временные файлы"""
        if self.temp_dir and self.temp_dir.exists():
            if force:
                shutil.rmtree(self.temp_dir)
            else:
                # Проверяем, нет ли важных файлов
                pass
    
    def preserve_on_error(self):
        """Сохраняет временные файлы при ошибке"""
        if self.temp_dir:
            # Создаем файл-маркер об ошибке
            error_marker = self.temp_dir / 'ERROR.txt'
            error_marker.write_text(
                f"Конвертация завершилась с ошибкой\n"
                f"Время: {datetime.now()}\n"
                f"Конвертер: {self.converter_name}\n",
                encoding='utf-8'
            )
```

### 5.2 Интеграция в BaseConverter

```python
def create_temp_dir(self) -> Path:
    """Создает временную директорию для конвертации"""
    v8_temp = self.env_vars.get('V8_TEMP', os.path.join(tempfile.gettempdir(), '1c'))
    converter_name = self.__class__.__name__
    
    self.temp_manager = TempFileManager(v8_temp, converter_name)
    return self.temp_manager.create_temp_dir()

def cleanup(self):
    """Очистка временных файлов"""
    if hasattr(self, 'temp_manager'):
        self.temp_manager.cleanup(force=True)
        self.logger.info("Временные файлы удалены")
```


## 6. Последовательность выполнения

### 6.1 Общий поток конвертации

```
1. Пользователь запускает: python convert.py --env path/to/project
2. convert.py загружает .env файлы
3. convert.py создает ConverterRegistry
4. ConverterRegistry возвращает класс конвертера по ScriptName
5. Создается экземпляр конвертера с env_vars
6. Вызывается converter.validate():
   - Проверка обязательных параметров
   - Проверка существования путей
   - Специфичная валидация конвертера
7. Вызывается converter.convert():
   - Создание временной директории
   - Определение типа источника
   - Выполнение конвертации
   - Обработка ошибок
8. При успехе: вызывается converter.cleanup()
9. При ошибке: временные файлы сохраняются
```

### 6.2 Пример: ConfigurationConverter (EDT → CF)

```
1. Определение типа источника: EDT
2. Создание временных директорий:
   - temp_dir/tmp_xml - для XML файлов
   - temp_dir/tmp_db - для временной ИБ
   - temp_dir/edt_ws - для workspace EDT
3. Экспорт EDT → XML:
   - EdtToolWrapper.export_to_xml()
   - Проверка успешности экспорта
4. Создание временной ИБ:
   - V8ToolWrapper.create_infobase()
5. Загрузка конфигурации из XML:
   - V8ToolWrapper.load_config_from_files()
   - Проверка лог-файла на ошибки
6. Выгрузка конфигурации в CF:
   - V8ToolWrapper.dump_config()
   - Проверка создания файла
7. Проверка результата:
   - Существование выходного файла
   - Размер файла > 0
8. Очистка временных файлов
```

### 6.3 Пример: DataProcessorConverter (EDT → EPF)

```
1. Определение типа источника: EDT
2. Подготовка базовой ИБ:
   - Если V8_BASE_IB указан - использовать его
   - Если V8_BASE_CONFIG указан - создать ИБ и загрузить конфигурацию
   - Иначе - создать пустую ИБ
3. Экспорт EDT → XML:
   - EdtToolWrapper.export_to_xml()
4. Обработка каждого файла обработки/отчета:
   - Поиск XML файлов в ExternalDataProcessors/ и ExternalReports/
   - Для каждого файла:
     * V8ToolWrapper.load_external_processor()
     * Проверка создания .epf/.erf файла
5. Очистка временных файлов
```


## 7. Интеграция с GUI

### 7.1 Требования к GUI интеграции

GUI (`src/gui/main.py`) должен иметь возможность:
1. Использовать конвертеры с параметром `silent=True`
2. Получать прогресс выполнения через callback
3. Отменять выполнение конвертации

### 7.2 Расширение BaseConverter для GUI

```python
class BaseConverter(ABC):
    def __init__(self, env_vars: Dict[str, str], silent: bool = False, 
                 progress_callback: Optional[Callable] = None):
        self.env_vars = env_vars
        self.silent = silent
        self.progress_callback = progress_callback
        # ... остальные атрибуты
    
    def report_progress(self, stage: str, percent: int):
        """Отправляет информацию о прогрессе"""
        if self.progress_callback:
            self.progress_callback(stage, percent)
        if not self.silent:
            self.logger.info(f"{stage}: {percent}%")
```

### 7.3 Пример использования в GUI

```python
def on_convert_button_click(self):
    """Обработчик кнопки конвертации в GUI"""
    env_vars = self.collect_env_vars()
    script_name = env_vars.get('ScriptName')
    
    registry = ConverterRegistry()
    converter_class = registry.get_converter(script_name)
    
    if converter_class:
        converter = converter_class(
            env_vars, 
            silent=True,
            progress_callback=self.update_progress_bar
        )
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self.run_conversion, args=(converter,))
        thread.start()

def update_progress_bar(self, stage: str, percent: int):
    """Обновляет прогресс-бар в GUI"""
    self.progress_label.setText(stage)
    self.progress_bar.setValue(percent)
```

## 8. Тестирование

### 8.1 Unit-тесты

#### 8.1.1 Тесты для BaseConverter
```python
# tests/unit/test_base_converter.py
def test_validate_required_params():
    """Тест валидации обязательных параметров"""
    pass

def test_detect_source_type_edt():
    """Тест определения типа источника EDT"""
    pass

def test_detect_source_type_xml():
    """Тест определения типа источника XML"""
    pass

def test_temp_dir_creation():
    """Тест создания временной директории"""
    pass

def test_cleanup_on_success():
    """Тест очистки при успехе"""
    pass

def test_preserve_on_error():
    """Тест сохранения файлов при ошибке"""
    pass
```

#### 8.1.2 Тесты для ToolWrappers
```python
# tests/unit/test_tool_wrappers.py
def test_v8_tool_find():
    """Тест поиска 1cv8.exe"""
    pass

def test_ibcmd_tool_find():
    """Тест поиска ibcmd.exe"""
    pass

def test_edt_tool_find_ring():
    """Тест поиска ring"""
    pass

def test_edt_tool_find_edtcli():
    """Тест поиска edtcli"""
    pass
```

#### 8.1.3 Тесты для ConverterRegistry
```python
# tests/unit/test_registry.py
def test_registry_discover():
    """Тест автоматического обнаружения конвертеров"""
    pass

def test_registry_get_converter():
    """Тест получения конвертера по имени"""
    pass

def test_registry_list_converters():
    """Тест получения списка конвертеров"""
    pass
```


### 8.2 Интеграционные тесты

#### 8.2.1 Обновление существующих тестов

```python
# tests/integration/test_convert_integration.py

class TestConversionIntegration:
    """Интеграционные тесты конвертации с Python конвертерами"""
    
    def test_conf2cf_conversion(self):
        """Тест конвертации EDT конфигурации в CF файл"""
        # Подготовка
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_conf2cf.env'
        
        # Загрузка env
        env_vars = merge_env_files([str(base_env), str(project_env)], silent=True)
        
        # Получение конвертера
        registry = ConverterRegistry()
        converter_class = registry.get_converter('conf2cf')
        assert converter_class is not None
        
        # Создание и запуск конвертера
        converter = converter_class(env_vars, silent=True)
        converter.validate()
        exit_code = converter.convert()
        
        # Проверка результата
        assert exit_code == 0
        output_file = Path(env_vars['V8_DST_PATH'])
        assert output_file.exists()
        assert output_file.stat().st_size > 1024
        
        # Очистка
        converter.cleanup()
    
    def test_ext2cfe_conversion(self):
        """Тест конвертации EDT расширения в CFE файл"""
        # Аналогично test_conf2cf_conversion
        pass
    
    def test_converter_error_handling(self):
        """Тест обработки ошибок конвертации"""
        # Тест с некорректными параметрами
        env_vars = {'ScriptName': 'conf2cf'}  # Нет обязательных параметров
        
        registry = ConverterRegistry()
        converter_class = registry.get_converter('conf2cf')
        converter = converter_class(env_vars, silent=True)
        
        # Должна быть ошибка валидации
        with pytest.raises(ValidationError):
            converter.validate()
    
    def test_temp_files_preserved_on_error(self):
        """Тест сохранения временных файлов при ошибке"""
        # Создаем ситуацию с ошибкой
        # Проверяем что временные файлы сохранены
        pass
```

### 8.3 Покрытие тестами

Целевое покрытие: **80%**

Приоритетные области для тестирования:
1. BaseConverter - 90%
2. ToolWrappers - 85%
3. Специализированные конвертеры - 80%
4. ConverterRegistry - 95%
5. Обработка ошибок - 90%

## 9. Миграция и развертывание

### 9.1 План миграции

**Фаза 1: Подготовка (1-2 дня)**
- Создание структуры модулей
- Реализация BaseConverter
- Реализация ToolWrappers
- Реализация ConverterRegistry

**Фаза 2: Реализация конвертеров (3-4 дня)**
- ConfigurationConverter
- DataProcessorConverter
- ExtensionConverter
- ValidationConverter

**Фаза 3: Интеграция (1-2 дня)**
- Обновление convert.py
- Обновление GUI (если требуется)
- Обновление тестов

**Фаза 4: Тестирование (2-3 дня)**
- Unit-тесты
- Интеграционные тесты
- Тестирование на реальных проектах

**Фаза 5: Документация и очистка (1 день)**
- Обновление README.md
- Обновление QUICKSTART.md
- Перемещение legacy скриптов
- Финальная проверка

### 9.2 Критерии готовности

- [ ] Все unit-тесты проходят
- [ ] Все интеграционные тесты проходят
- [ ] Покрытие тестами >= 80%
- [ ] Документация обновлена
- [ ] Производительность не ухудшилась
- [ ] GUI работает корректно (если применимо)
- [ ] Legacy скрипты перемещены в legacy/

## 10. Риски и митигация

### 10.1 Технические риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Различия в поведении CMD vs Python | Средняя | Высокое | Тщательное тестирование, сравнение результатов |
| Проблемы с кодировками | Средняя | Среднее | Явное указание кодировок, тестирование |
| Ошибки в subprocess | Низкая | Высокое | Обработка всех исключений, логирование |
| Проблемы с путями Windows | Низкая | Среднее | Использование Path, тестирование |

### 10.2 Организационные риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Недостаточное время на тестирование | Средняя | Высокое | Приоритизация тестов, автоматизация |
| Изменение требований | Низкая | Среднее | Гибкая архитектура, модульность |

## 11. Будущие улучшения

### 11.1 Возможные расширения

1. **Параллельная конвертация**
   - Конвертация нескольких файлов одновременно
   - Использование multiprocessing

2. **Кэширование**
   - Кэширование промежуточных XML файлов
   - Переиспользование временных ИБ

3. **Расширенная валидация**
   - Проверка версий платформы 1С
   - Проверка совместимости конфигураций

4. **Плагины**
   - Система плагинов для пользовательских конвертеров
   - API для расширения функциональности

5. **Мониторинг**
   - Сбор статистики конвертаций
   - Анализ производительности

## 12. Заключение

Данный дизайн обеспечивает:
- ✅ Устранение дублирования кода
- ✅ Автоматическое обнаружение конвертеров
- ✅ Единообразную обработку ошибок
- ✅ Простоту добавления новых конвертеров
- ✅ Хорошую тестируемость
- ✅ Совместимость с существующим кодом
- ✅ Расширяемость для будущих улучшений

Архитектура следует принципам SOLID и обеспечивает чистое разделение ответственности между компонентами.

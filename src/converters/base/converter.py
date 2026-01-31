"""
Базовые классы для конвертеров 1С.

Содержит абстрактный базовый класс BaseConverter и вспомогательные классы
для логирования, определения типов источников и управления временными файлами.
"""

import os
import sys
import shutil
import tempfile
import time
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, List, Callable


def format_duration(seconds: float) -> str:
    """
    Форматирует длительность в читаемый вид
    
    Args:
        seconds: количество секунд
        
    Returns:
        str: отформатированная строка (например: "2 ч 15 мин 30 сек" или "45 сек")
    """
    if seconds < 60:
        return f"{int(seconds)} сек"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes < 60:
        if secs > 0:
            return f"{minutes} мин {secs} сек"
        return f"{minutes} мин"
    
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    if mins > 0 and secs > 0:
        return f"{hours} ч {mins} мин {secs} сек"
    elif mins > 0:
        return f"{hours} ч {mins} мин"
    else:
        return f"{hours} ч"


class Colors:
    """Цветовые коды ANSI для консольного вывода."""
    
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    
    @staticmethod
    def enable_windows_colors():
        """Включает поддержку ANSI цветов в Windows консоли."""
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass


class Logger:
    """
    Логгер для единообразного вывода сообщений с цветовым кодированием.
    
    Args:
        silent: Если True, подавляет вывод сообщений
        debug: Если True, выводит отладочную информацию
    """
    
    def __init__(self, silent: bool = False, debug: bool = False):
        self.silent = silent
        self.debug = debug
        Colors.enable_windows_colors()
    
    def info(self, message: str):
        """Выводит информационное сообщение."""
        if not self.silent:
            print(f"{Colors.GREEN}[ИНФО]{Colors.RESET} {message}")
    
    def error(self, message: str):
        """Выводит сообщение об ошибке."""
        if not self.silent:
            # Удаляем BOM и другие проблемные Unicode символы для Windows консоли
            clean_message = message.encode('ascii', errors='ignore').decode('ascii')
            if not clean_message.strip():
                # Если после очистки ничего не осталось, используем замену
                clean_message = message.encode('cp1251', errors='replace').decode('cp1251')
            print(f"{Colors.RED}[ОШИБКА]{Colors.RESET} {clean_message}")
    
    def warning(self, message: str):
        """Выводит предупреждение."""
        if not self.silent:
            print(f"{Colors.YELLOW}[ПРЕДУПРЕЖДЕНИЕ]{Colors.RESET} {message}")
    
    def success(self, message: str):
        """Выводит сообщение об успехе."""
        if not self.silent:
            print(f"{Colors.GREEN}[УСПЕХ]{Colors.RESET} {message}")
    
    def debug_msg(self, message: str):
        """Выводит отладочное сообщение."""
        if not self.silent and self.debug:
            print(f"{Colors.CYAN}[ОТЛАДКА]{Colors.RESET} {message}")


class SourceType(Enum):
    """Типы источников конвертации 1С."""
    
    EDT = "edt"              # 1C:EDT проект
    XML = "xml"              # 1C:Designer XML файлы
    FILE_IB = "file_ib"      # Файловая информационная база
    SERVER_IB = "server_ib"  # Серверная информационная база
    CF_FILE = "cf"           # Файл конфигурации .cf
    CFE_FILE = "cfe"         # Файл расширения .cfe
    UNKNOWN = "unknown"


class SourceDetector:
    """Определяет тип источника по пути."""
    
    @staticmethod
    def detect(path: str) -> SourceType:
        """
        Определяет тип источника по пути.
        
        Args:
            path: Путь к источнику
            
        Returns:
            SourceType: Тип источника
        """
        path_obj = Path(path)
        
        # Проверка на EDT проект
        if path_obj.is_dir() and (path_obj / 'DT-INF').exists():
            return SourceType.EDT
        
        # Проверка на XML файлы
        if path_obj.is_dir() and (path_obj / 'Configuration.xml').exists():
            return SourceType.XML
        
        # Проверка на файловую ИБ
        if path_obj.is_dir() and (path_obj / '1cv8.1cd').exists():
            return SourceType.FILE_IB
        
        # Проверка на серверную ИБ (формат /Sserver\basename)
        if isinstance(path, str) and path.startswith('/S'):
            return SourceType.SERVER_IB
        
        # Проверка на файловую ИБ (формат /Fpath)
        if isinstance(path, str) and path.startswith('/F'):
            return SourceType.FILE_IB
        
        # Проверка на .cf файл
        if path_obj.is_file() and path_obj.suffix.lower() == '.cf':
            return SourceType.CF_FILE
        
        # Проверка на .cfe файл
        if path_obj.is_file() and path_obj.suffix.lower() == '.cfe':
            return SourceType.CFE_FILE
        
        return SourceType.UNKNOWN


class TempFileManager:
    """
    Менеджер временных файлов для конвертации.
    
    Args:
        base_temp_dir: Базовая директория для временных файлов
        converter_name: Имя конвертера (для создания уникальной папки)
    """
    
    def __init__(self, base_temp_dir: str, converter_name: str):
        self.base_temp_dir = Path(base_temp_dir)
        self.converter_name = converter_name
        self.temp_dir: Optional[Path] = None
    
    def create_temp_dir(self) -> Path:
        """
        Создает временную директорию.
        
        Returns:
            Path: Путь к созданной временной директории
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.temp_dir = self.base_temp_dir / f"{self.converter_name}_{timestamp}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        return self.temp_dir
    
    def cleanup(self, force: bool = False):
        """
        Удаляет временные файлы.
        
        Args:
            force: Если True, удаляет без проверок
        """
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                # Игнорируем ошибки при удалении
                pass
    
    def preserve_on_error(self):
        """Сохраняет временные файлы при ошибке с маркером."""
        if self.temp_dir and self.temp_dir.exists():
            error_marker = self.temp_dir / 'ERROR.txt'
            try:
                error_marker.write_text(
                    f"Конвертация завершилась с ошибкой\n"
                    f"Время: {datetime.now()}\n"
                    f"Конвертер: {self.converter_name}\n",
                    encoding='utf-8'
                )
            except Exception:
                pass


class ToolOutputParser:
    """Парсер вывода инструментов 1С."""
    
    # Список кодировок для попытки чтения (в порядке приоритета)
    ENCODINGS = ['utf-8', 'cp1251', 'cp866', 'latin-1']
    
    @staticmethod
    def read_file_with_encoding(file_path: Path) -> Optional[str]:
        """
        Читает файл, пробуя разные кодировки.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str или None: Содержимое файла или None если не удалось прочитать
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
        Парсит лог файл designer и извлекает ошибки.
        
        Args:
            log_file: Путь к лог-файлу
            
        Returns:
            list: Список строк с ошибками
        """
        errors = []
        content = ToolOutputParser.read_file_with_encoding(log_file)
        
        # Ключевые слова, указывающие на успешное завершение
        success_keywords = [
            'успешно завершено',
            'успешно выполнено',
            'successfully completed',
            'Создание информационной базы',
        ]
        
        # Ключевые слова, указывающие на ошибку
        error_keywords = [
            'ошибка',
            'error',
            'неверн',
            'отсутствующ',
            'не найден',
            'не удалось',
            'failed',
        ]
        
        if content:
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Пропускаем информационные сообщения
                if line.startswith('[INFO]'):
                    continue
                
                # Пропускаем сообщения об успешном завершении
                line_lower = line.lower()
                if any(kw.lower() in line_lower for kw in success_keywords):
                    continue
                
                # Добавляем строку как ошибку, если она содержит ключевые слова ошибки
                # или если это непустая строка (для обратной совместимости)
                if any(kw.lower() in line_lower for kw in error_keywords):
                    errors.append(line)
        
        return errors
    
    @staticmethod
    def has_errors(log_file: Path) -> bool:
        """
        Проверяет наличие ошибок в логе.
        
        Args:
            log_file: Путь к лог-файлу
            
        Returns:
            bool: True если есть ошибки
        """
        errors = ToolOutputParser.parse_designer_log(log_file)
        return len(errors) > 0


# Исключения

class ConversionError(Exception):
    """Базовое исключение для ошибок конвертации."""
    
    def __init__(self, message: str, temp_dir: Optional[Path] = None):
        super().__init__(message)
        self.temp_dir = temp_dir


class ValidationError(ConversionError):
    """Ошибка валидации параметров."""
    pass


class ToolNotFoundError(ConversionError):
    """Инструмент не найден."""
    pass


class ToolExecutionError(ConversionError):
    """Ошибка выполнения инструмента."""
    
    def __init__(self, message: str, tool_output: str = "", temp_dir: Optional[Path] = None):
        super().__init__(message, temp_dir)
        self.tool_output = tool_output


# Базовый класс конвертера

class BaseConverter(ABC):
    """
    Абстрактный базовый класс для всех конвертеров 1С.
    
    Предоставляет общую логику для валидации, логирования,
    управления временными файлами и обработки ошибок.
    
    Args:
        env_vars: Словарь переменных окружения из .env файлов
        silent: Если True, подавляет вывод в консоль
        progress_callback: Опциональный callback для отчета о прогрессе
        debug: Если True, выводит отладочную информацию
    """
    
    def __init__(
        self, 
        env_vars: Dict[str, str], 
        silent: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        debug: bool = False
    ):
        self.env_vars = env_vars
        self.silent = silent
        self.progress_callback = progress_callback
        self.debug = debug
        self.src_path = env_vars.get('V8_SRC_PATH', '')
        self.dst_path = env_vars.get('V8_DST_PATH', '')
        self.temp_dir: Optional[Path] = None
        self.logger = Logger(silent, debug)
        self.cleanup_on_success = True
        self.cleanup_on_error = False
        self.temp_manager: Optional[TempFileManager] = None
        
        # Отслеживание времени
        self.stage_start_time: Optional[float] = None
        self.conversion_start_time: Optional[float] = None
    
    def validate(self) -> None:
        """
        Валидирует параметры конвертации.
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Проверка обязательных параметров
        if not self.src_path:
            raise ValidationError("Не указан параметр V8_SRC_PATH (путь к источнику)")
        
        if not self.dst_path:
            raise ValidationError("Не указан параметр V8_DST_PATH (путь назначения)")
        
        # Проверка существования источника
        src_path_obj = Path(self.src_path)
        if not src_path_obj.exists() and not self.src_path.startswith('/S') and not self.src_path.startswith('/F'):
            raise ValidationError(f"Источник не найден: {self.src_path}")
        
        # Специфичная валидация конвертера
        self._validate_specific()
    
    @abstractmethod
    def _validate_specific(self) -> None:
        """
        Специфичная валидация для конкретного конвертера.
        Переопределяется в наследниках.
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        pass
    
    def convert(self) -> int:
        """
        Главный метод конвертации (шаблонный метод).
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
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
                if not self.cleanup_on_error and self.temp_dir:
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
    
    @abstractmethod
    def _do_convert(self) -> int:
        """
        Реализация конвертации. Переопределяется в наследниках.
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        pass
    
    @abstractmethod
    def get_output_extension(self) -> str:
        """
        Возвращает расширение выходного файла.
        Переопределяется в наследниках.
        
        Returns:
            str: Расширение файла (например, '.cf', '.cfe', '.epf')
        """
        pass
    
    def detect_source_type(self) -> SourceType:
        """
        Определяет тип источника.
        
        Returns:
            SourceType: Тип источника
        """
        return SourceDetector.detect(self.src_path)
    
    def create_temp_dir(self) -> Path:
        """
        Создает временную директорию для конвертации.
        
        Returns:
            Path: Путь к временной директории
        """
        v8_temp = self.env_vars.get('V8_TEMP', os.path.join(tempfile.gettempdir(), '1c'))
        converter_name = self.__class__.__name__
        
        self.temp_manager = TempFileManager(v8_temp, converter_name)
        return self.temp_manager.create_temp_dir()
    
    def cleanup(self):
        """Очистка временных файлов."""
        if self.temp_manager:
            self.temp_manager.cleanup(force=True)
            self.logger.info("Временные файлы удалены")
    
    def report_progress(self, stage: str, percent: int):
        """
        Отправляет информацию о прогрессе.
        
        Args:
            stage: Название текущего этапа
            percent: Процент выполнения (0-100)
        """
        if self.progress_callback:
            self.progress_callback(stage, percent)
        if not self.silent:
            self.logger.info(f"{stage}: {percent}%")
    
    # Методы логирования для удобства
    
    def log_info(self, message: str):
        """Логирует информационное сообщение."""
        self.logger.info(message)
    
    def log_error(self, message: str):
        """Логирует сообщение об ошибке."""
        self.logger.error(message)
    
    def log_warning(self, message: str):
        """Логирует предупреждение."""
        self.logger.warning(message)
    
    def log_success(self, message: str):
        """Логирует сообщение об успехе."""
        self.logger.success(message)
    
    def start_stage(self, stage_name: str):
        """
        Начинает новый этап с измерением времени.
        
        Args:
            stage_name: название этапа
        """
        self.stage_start_time = time.time()
        self.log_info(stage_name)
    
    def end_stage(self, success_message: str):
        """
        Завершает этап и выводит время выполнения.
        
        Args:
            success_message: сообщение об успешном завершении
        """
        if self.stage_start_time is not None:
            duration = time.time() - self.stage_start_time
            duration_str = format_duration(duration)
            self.log_success(f"{success_message}. Время выполнения: {duration_str}")
            self.stage_start_time = None
        else:
            self.log_success(success_message)

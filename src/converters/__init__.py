"""
Модуль конвертеров 1С.

Предоставляет единый интерфейс для работы с конвертерами различных типов
объектов 1С (конфигурации, обработки, расширения).
"""

# Базовые классы и утилиты
from .base import (
    BaseConverter,
    Logger,
    SourceType,
    SourceDetector,
    TempFileManager,
    ToolOutputParser,
    Colors,
    ConversionError,
    ValidationError,
    ToolNotFoundError,
    ToolExecutionError,
    ToolWrapper,
    V8ToolWrapper,
    IbcmdToolWrapper,
    EdtToolWrapper,
)

# Реестр конвертеров
from .registry import ConverterRegistry

# Специализированные конвертеры будут импортированы после их реализации
# from .configuration.converter import ConfigurationConverter
# from .dataprocessor.converter import DataProcessorConverter
# from .extension.converter import ExtensionConverter
# from .validation.converter import ValidationConverter

__all__ = [
    # Базовые классы
    'BaseConverter',
    'Logger',
    'SourceType',
    'SourceDetector',
    'TempFileManager',
    'ToolOutputParser',
    'Colors',
    
    # Исключения
    'ConversionError',
    'ValidationError',
    'ToolNotFoundError',
    'ToolExecutionError',
    
    # Обертки инструментов
    'ToolWrapper',
    'V8ToolWrapper',
    'IbcmdToolWrapper',
    'EdtToolWrapper',
    
    # Реестр
    'ConverterRegistry',
    
    # Специализированные конвертеры (будут добавлены позже)
    # 'ConfigurationConverter',
    # 'DataProcessorConverter',
    # 'ExtensionConverter',
    # 'ValidationConverter',
]

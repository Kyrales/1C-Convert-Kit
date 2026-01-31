"""
Базовые классы для конвертеров 1С.

Этот модуль содержит абстрактные базовые классы и утилиты,
используемые всеми специализированными конвертерами.
"""

from .converter import (
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
)

from .tools import (
    ToolWrapper,
    V8ToolWrapper,
    IbcmdToolWrapper,
    EdtToolWrapper,
)

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
]

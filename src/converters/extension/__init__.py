"""
Модуль конвертации расширений 1С.

Предоставляет ExtensionConverter для конвертации расширений между форматами
EDT, XML, InfoBase и CFE.
"""

from .converter import ExtensionConverter

__all__ = ['ExtensionConverter']

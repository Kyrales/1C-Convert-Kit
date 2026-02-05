"""
Конвертеры для конфигураций 1С.

Поддерживает конвертацию конфигураций между форматами:
- EDT -> CF
- XML -> CF
- IB -> CF
"""

from .converter import ConfigurationConverter

__all__ = ['ConfigurationConverter']

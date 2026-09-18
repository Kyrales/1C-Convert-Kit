"""
Реестр конвертеров 1С.

Обеспечивает автоматическое обнаружение и регистрацию конвертеров,
а также получение нужного конвертера по типу конвертации.
"""

from typing import Dict, Optional, Type, List

from .base.converter import BaseConverter


class ConverterRegistry:
    """
    Реестр конвертеров для автоматического обнаружения и управления.
    
    Реестр автоматически находит все доступные конвертеры и предоставляет
    единый интерфейс для получения нужного конвертера по типу конвертации
    (например, 'conf2cf', 'dp2epf', 'ext2cfe').
    """
    
    def __init__(self):
        self._converters: Dict[str, Type[BaseConverter]] = {}
        self._discover_converters()
    
    def _discover_converters(self):
        """
        Автоматически находит и регистрирует все конвертеры.
        
        Импортирует модули конвертеров и регистрирует их по типам конвертации.
        """
        # Импортируем все конвертеры
        from .configuration.converter import ConfigurationConverter
        from .dataprocessor.converter import DataProcessorConverter
        from .extension.converter import ExtensionConverter
        from .validation.converter import ValidationConverter
        
        # Регистрируем конвертеры конфигураций
        self.register('conf2cf', ConfigurationConverter)
        self.register('conf2xml', ConfigurationConverter)
        self.register('conf2edt', ConfigurationConverter)
        self.register('conf2ib', ConfigurationConverter)
        self.register('dt2ib', ConfigurationConverter)
        self.register('ib2dt', ConfigurationConverter)
        
        # Регистрируем конвертеры обработок/отчетов
        self.register('dp2epf', DataProcessorConverter)
        self.register('dp2erf', DataProcessorConverter)
        self.register('dp2xml', DataProcessorConverter)
        self.register('dp2edt', DataProcessorConverter)
        
        # Регистрируем конвертеры расширений
        self.register('ext2cfe', ExtensionConverter)
        self.register('ext2xml', ExtensionConverter)
        self.register('ext2edt', ExtensionConverter)
        self.register('ext2ib', ExtensionConverter)
        
        # Регистрируем конвертер валидации
        self.register('edt-validate', ValidationConverter)
    
    def register(self, script_name: str, converter_class: Type[BaseConverter]):
        """
        Регистрирует конвертер в реестре.
        
        Args:
            script_name: Имя типа конвертации (например, 'conf2cf', 'dp2epf')
            converter_class: Класс конвертера
            
        Raises:
            ValueError: Если converter_class не является наследником BaseConverter
        """
        # Type hint гарантирует что это Type[BaseConverter], просто регистрируем
        self._converters[script_name] = converter_class
    
    def get_converter(self, script_name: str) -> Optional[Type[BaseConverter]]:
        """
        Получает класс конвертера по имени типа конвертации.
        
        Args:
            script_name: Имя типа конвертации (например, 'conf2cf', 'dp2epf')
            
        Returns:
            Type[BaseConverter] или None: Класс конвертера или None если не найден
        """
        return self._converters.get(script_name)
    
    def list_converters(self) -> List[str]:
        """
        Возвращает список всех зарегистрированных типов конвертации.
        
        Returns:
            list: Список имен типов конвертации
        """
        return list(self._converters.keys())
    
    def is_registered(self, script_name: str) -> bool:
        """
        Проверяет, зарегистрирован ли конвертер.
        
        Args:
            script_name: Имя типа конвертации
            
        Returns:
            bool: True если конвертер зарегистрирован
        """
        return script_name in self._converters

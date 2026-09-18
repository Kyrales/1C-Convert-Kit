"""
Unit-тесты для ConverterRegistry с полным набором конвертеров.
"""

import pytest

from src.converters.registry import ConverterRegistry
from src.converters.configuration.converter import ConfigurationConverter
from src.converters.dataprocessor.converter import DataProcessorConverter
from src.converters.extension.converter import ExtensionConverter
from src.converters.validation.converter import ValidationConverter


class TestConverterRegistryComplete:
    """Тесты для полного реестра конвертеров."""
    
    def test_registry_initialization(self):
        """Тест инициализации реестра."""
        registry = ConverterRegistry()
        assert registry is not None
    
    def test_registry_discovers_all_converters(self):
        """Тест автоматического обнаружения всех конвертеров."""
        registry = ConverterRegistry()
        converters = registry.list_converters()
        
        # Проверяем что все типы конвертации зарегистрированы
        expected_converters = [
            # Конфигурации
            'conf2cf', 'conf2xml', 'conf2edt', 'conf2ib', 'dt2ib', 'ib2dt',
            # Обработки/отчеты
            'dp2epf', 'dp2erf', 'dp2xml', 'dp2edt',
            # Расширения
            'ext2cfe', 'ext2xml', 'ext2edt', 'ext2ib',
            # Валидация
            'edt-validate'
        ]
        
        for converter_type in expected_converters:
            assert converter_type in converters, f"Конвертер {converter_type} не зарегистрирован"
    
    def test_get_configuration_converter(self):
        """Тест получения конвертера конфигураций."""
        registry = ConverterRegistry()
        
        converter_class = registry.get_converter('conf2cf')
        assert converter_class is ConfigurationConverter
        
        converter_class = registry.get_converter('conf2xml')
        assert converter_class is ConfigurationConverter
    
    def test_get_dataprocessor_converter(self):
        """Тест получения конвертера обработок/отчетов."""
        registry = ConverterRegistry()
        
        converter_class = registry.get_converter('dp2epf')
        assert converter_class is DataProcessorConverter
        
        converter_class = registry.get_converter('dp2erf')
        assert converter_class is DataProcessorConverter
    
    def test_get_extension_converter(self):
        """Тест получения конвертера расширений."""
        registry = ConverterRegistry()
        
        converter_class = registry.get_converter('ext2cfe')
        assert converter_class is ExtensionConverter
        
        converter_class = registry.get_converter('ext2xml')
        assert converter_class is ExtensionConverter
    
    def test_get_validation_converter(self):
        """Тест получения конвертера валидации."""
        registry = ConverterRegistry()
        
        converter_class = registry.get_converter('edt-validate')
        assert converter_class is ValidationConverter
    
    def test_get_nonexistent_converter(self):
        """Тест получения несуществующего конвертера."""
        registry = ConverterRegistry()
        
        converter_class = registry.get_converter('nonexistent')
        assert converter_class is None
    
    def test_is_registered(self):
        """Тест проверки регистрации конвертера."""
        registry = ConverterRegistry()
        
        assert registry.is_registered('conf2cf') is True
        assert registry.is_registered('ext2cfe') is True
        assert registry.is_registered('edt-validate') is True
        assert registry.is_registered('nonexistent') is False
    
    def test_list_converters_count(self):
        """Тест количества зарегистрированных конвертеров."""
        registry = ConverterRegistry()
        converters = registry.list_converters()
        
        # Должно быть 15 типов конвертации
        assert len(converters) == 15

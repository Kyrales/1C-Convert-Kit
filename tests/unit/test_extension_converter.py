"""
Unit-тесты для ExtensionConverter.
"""

import pytest
from pathlib import Path

from src.converters.extension.converter import ExtensionConverter
from src.converters.base.converter import ValidationError, SourceType


class TestExtensionConverter:
    """Тесты для конвертера расширений."""
    
    def test_get_output_extension(self):
        """Тест получения расширения выходного файла."""
        env_vars = {
            'V8_SRC_PATH': 'test',
            'V8_DST_PATH': 'test.cfe',
            'V8_EXT_NAME': 'TestExtension'
        }
        converter = ExtensionConverter(env_vars, silent=True)
        assert converter.get_output_extension() == '.cfe'
    
    def test_validate_missing_ext_name(self):
        """Тест валидации без указания имени расширения."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'test_ext'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': str(Path(tmpdir) / 'test.cfe')
                # V8_EXT_NAME отсутствует
            }
            converter = ExtensionConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter.validate()
            
            assert 'V8_EXT_NAME' in str(exc_info.value)
    
    def test_validate_wrong_dst_extension(self):
        """Тест валидации с неправильным расширением выходного файла."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'test_ext'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': str(Path(tmpdir) / 'test.cf'),  # Должно быть .cfe
                'V8_EXT_NAME': 'TestExtension'
            }
            converter = ExtensionConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter.validate()
            
            assert '.cfe' in str(exc_info.value)
    
    def test_init_attributes(self):
        """Тест инициализации атрибутов конвертера."""
        env_vars = {
            'V8_SRC_PATH': 'test',
            'V8_DST_PATH': 'test.cfe',
            'V8_EXT_NAME': 'TestExtension',
            'V8_BASE_IB': 'C:/Base',
            'V8_BASE_CONFIG': 'C:/Config',
            'V8_CONVERT_TOOL': 'ibcmd'
        }
        converter = ExtensionConverter(env_vars, silent=True)
        
        assert converter.ext_name == 'TestExtension'
        assert converter.base_ib == 'C:/Base'
        assert converter.base_config == 'C:/Config'
        assert converter.convert_tool == 'ibcmd'
    
    def test_init_default_convert_tool(self):
        """Тест инициализации с инструментом по умолчанию."""
        env_vars = {
            'V8_SRC_PATH': 'test',
            'V8_DST_PATH': 'test.cfe',
            'V8_EXT_NAME': 'TestExtension'
        }
        converter = ExtensionConverter(env_vars, silent=True)
        
        assert converter.convert_tool == 'designer'
    
    def test_tools_initialization(self):
        """Тест инициализации инструментов."""
        env_vars = {
            'V8_SRC_PATH': 'test',
            'V8_DST_PATH': 'test.cfe',
            'V8_EXT_NAME': 'TestExtension'
        }
        converter = ExtensionConverter(env_vars, silent=True)
        
        assert converter.v8_tool is not None
        assert converter.ibcmd_tool is not None
        assert converter.edt_tool is not None


class TestExtensionConverterValidation:
    """Тесты валидации параметров ExtensionConverter."""
    
    def test_validate_success_with_cfe_extension(self):
        """Тест успешной валидации с правильным расширением."""
        # Создаем временную директорию для теста
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'test_ext'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': str(Path(tmpdir) / 'output.cfe'),
                'V8_EXT_NAME': 'TestExtension'
            }
            converter = ExtensionConverter(env_vars, silent=True)
            
            # Валидация должна пройти без исключений
            # (кроме проверки типа источника, которая требует DT-INF)
            try:
                converter.validate()
            except ValidationError as e:
                # Ожидаем ошибку о типе источника, но не о параметрах
                assert 'V8_EXT_NAME' not in str(e)
                assert '.cfe' not in str(e)
    
    def test_validate_cfe_extension_case_insensitive(self):
        """Тест валидации с расширением .CFE в верхнем регистре."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'test_ext'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': str(Path(tmpdir) / 'output.CFE'),
                'V8_EXT_NAME': 'TestExtension'
            }
            converter = ExtensionConverter(env_vars, silent=True)
            
            # Валидация должна пройти (расширение проверяется без учета регистра)
            try:
                converter.validate()
            except ValidationError as e:
                # Не должно быть ошибки о расширении
                assert '.cfe' not in str(e).lower()

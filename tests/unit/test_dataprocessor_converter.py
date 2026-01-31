"""
Unit-тесты для DataProcessorConverter.
"""

import pytest
from pathlib import Path
from src.converters.dataprocessor import DataProcessorConverter
from src.converters.base.converter import ValidationError


class TestDataProcessorConverter:
    """Тесты для конвертера обработок и отчетов."""
    
    def test_init(self):
        """Тест инициализации конвертера."""
        env_vars = {
            'V8_SRC_PATH': '/path/to/source',
            'V8_DST_PATH': '/path/to/destination'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        assert converter.src_path == '/path/to/source'
        assert converter.dst_path == '/path/to/destination'
        assert converter.base_ib == ''
        assert converter.base_config == ''
    
    def test_init_with_base_ib(self):
        """Тест инициализации с базовой ИБ."""
        env_vars = {
            'V8_SRC_PATH': '/path/to/source',
            'V8_DST_PATH': '/path/to/destination',
            'V8_BASE_IB': '/path/to/base/ib',
            'V8_BASE_CONFIG': '/path/to/base/config'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        assert converter.base_ib == '/path/to/base/ib'
        assert converter.base_config == '/path/to/base/config'
    
    def test_get_output_extension(self):
        """Тест получения расширения выходного файла."""
        env_vars = {
            'V8_SRC_PATH': '/path/to/source',
            'V8_DST_PATH': '/path/to/destination'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        assert converter.get_output_extension() == '.epf'
    
    def test_validate_specific_directory(self):
        """Тест валидации - dst_path должен быть директорией."""
        env_vars = {
            'V8_SRC_PATH': '/path/to/source',
            'V8_DST_PATH': '/path/to/output'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        # Не должно быть ошибки для директории
        converter._validate_specific()
    
    def test_validate_specific_file_error(self):
        """Тест валидации - ошибка если dst_path указывает на файл."""
        env_vars = {
            'V8_SRC_PATH': '/path/to/source',
            'V8_DST_PATH': '/path/to/output.epf'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        # Должна быть ошибка для файла .epf
        with pytest.raises(ValidationError) as exc_info:
            converter._validate_specific()
        
        assert 'директорию' in str(exc_info.value)
    
    def test_validate_specific_erf_file_error(self):
        """Тест валидации - ошибка если dst_path указывает на .erf файл."""
        env_vars = {
            'V8_SRC_PATH': '/path/to/source',
            'V8_DST_PATH': '/path/to/output.erf'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        # Должна быть ошибка для файла .erf
        with pytest.raises(ValidationError) as exc_info:
            converter._validate_specific()
        
        assert 'директорию' in str(exc_info.value)
    
    def test_find_processor_files_empty(self, tmp_path):
        """Тест поиска файлов обработок - пустая директория."""
        env_vars = {
            'V8_SRC_PATH': str(tmp_path),
            'V8_DST_PATH': '/path/to/output'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        files = converter._find_processor_files(tmp_path)
        
        assert files == []
    
    def test_find_processor_files_with_processors(self, tmp_path):
        """Тест поиска файлов обработок - с обработками."""
        # Создаем структуру директорий
        processors_dir = tmp_path / 'ExternalDataProcessors'
        processors_dir.mkdir()
        
        # Создаем тестовые XML файлы
        (processors_dir / 'TestProcessor1.xml').write_text('test')
        (processors_dir / 'TestProcessor2.xml').write_text('test')
        
        env_vars = {
            'V8_SRC_PATH': str(tmp_path),
            'V8_DST_PATH': '/path/to/output'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        files = converter._find_processor_files(tmp_path)
        
        assert len(files) == 2
        assert all(ext == '.epf' for _, ext, _ in files)
        names = [name for _, _, name in files]
        assert 'TestProcessor1' in names
        assert 'TestProcessor2' in names
    
    def test_find_processor_files_with_reports(self, tmp_path):
        """Тест поиска файлов обработок - с отчетами."""
        # Создаем структуру директорий
        reports_dir = tmp_path / 'ExternalReports'
        reports_dir.mkdir()
        
        # Создаем тестовые XML файлы
        (reports_dir / 'TestReport1.xml').write_text('test')
        (reports_dir / 'TestReport2.xml').write_text('test')
        
        env_vars = {
            'V8_SRC_PATH': str(tmp_path),
            'V8_DST_PATH': '/path/to/output'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        files = converter._find_processor_files(tmp_path)
        
        assert len(files) == 2
        assert all(ext == '.erf' for _, ext, _ in files)
        names = [name for _, _, name in files]
        assert 'TestReport1' in names
        assert 'TestReport2' in names
    
    def test_find_processor_files_mixed(self, tmp_path):
        """Тест поиска файлов - смешанные обработки и отчеты."""
        # Создаем структуру директорий
        processors_dir = tmp_path / 'ExternalDataProcessors'
        processors_dir.mkdir()
        reports_dir = tmp_path / 'ExternalReports'
        reports_dir.mkdir()
        
        # Создаем тестовые XML файлы
        (processors_dir / 'Processor1.xml').write_text('test')
        (reports_dir / 'Report1.xml').write_text('test')
        
        env_vars = {
            'V8_SRC_PATH': str(tmp_path),
            'V8_DST_PATH': '/path/to/output'
        }
        
        converter = DataProcessorConverter(env_vars, silent=True)
        
        files = converter._find_processor_files(tmp_path)
        
        assert len(files) == 2
        
        # Проверяем что есть и .epf и .erf
        extensions = [ext for _, ext, _ in files]
        assert '.epf' in extensions
        assert '.erf' in extensions

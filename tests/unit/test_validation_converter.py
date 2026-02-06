"""
Unit-тесты для ValidationConverter.
"""

import pytest
from pathlib import Path

from src.converters.validation.converter import ValidationConverter
from src.converters.base.converter import ValidationError, SourceType


class TestValidationConverter:
    """Тесты для конвертера валидации."""
    
    def test_get_output_extension(self):
        """Тест получения расширения выходного файла."""
        env_vars = {
            'V8_SRC_PATH': 'test',
            'V8_DST_PATH': 'report.txt'
        }
        converter = ValidationConverter(env_vars, silent=True)
        assert converter.get_output_extension() == '.txt'
    
    def test_init_attributes(self):
        """Тест инициализации атрибутов конвертера."""
        env_vars = {
            'V8_SRC_PATH': 'test',
            'V8_DST_PATH': 'report.json'
        }
        converter = ValidationConverter(env_vars, silent=True)
        
        # ValidationConverter больше не имеет edt_tool атрибута
        assert converter.src_path == 'test'
        assert converter.dst_path == 'report.json'
    
    def test_validate_missing_dst_path(self):
        """Тест валидации без указания V8_DST_PATH."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем DT-INF
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': ''  # Пустой путь
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter.validate()
            
            assert 'V8_DST_PATH' in str(exc_info.value)
    
    def test_validate_non_edt_source(self):
        """Тест валидации с источником, который не является EDT проектом."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Создаем директорию без DT-INF
            src_path = Path(tmpdir) / 'not_edt'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter.validate()
            
            assert 'ValidationConverter работает только с EDT проектами' in str(exc_info.value)
    
    def test_validate_missing_dt_inf(self):
        """Тест валидации EDT проекта без директории DT-INF."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter.validate()
            
            assert 'ValidationConverter работает только с EDT проектами' in str(exc_info.value)
    
    def test_validate_success_with_dt_inf(self):
        """Тест успешной валидации EDT проекта с DT-INF."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем директорию DT-INF
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            # Валидация должна пройти без исключений
            converter.validate()


class TestValidationConverterStructureCheck:
    """Тесты проверки структуры EDT проекта."""
    
    def test_validate_structure_missing_dt_inf(self):
        """Тест проверки структуры без DT-INF."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter._validate_edt_structure(src_path)
            
            assert 'DT-INF' in str(exc_info.value)
    
    def test_validate_structure_missing_project_file(self):
        """Тест проверки структуры без файла .project."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем DT-INF
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter._validate_edt_structure(src_path)
            
            assert '.project' in str(exc_info.value)
    
    def test_validate_structure_missing_src_directory(self):
        """Тест проверки структуры без директории src."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем DT-INF и .project
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            project_file = src_path / '.project'
            project_file.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter._validate_edt_structure(src_path)
            
            assert 'src' in str(exc_info.value)
    
    def test_validate_structure_missing_metadata_files(self):
        """Тест проверки структуры без файлов метаданных."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем DT-INF, .project и src
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            project_file = src_path / '.project'
            project_file.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            src_dir = src_path / 'src'
            src_dir.mkdir()
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            with pytest.raises(ValidationError) as exc_info:
                converter._validate_edt_structure(src_path)
            
            error_msg = str(exc_info.value)
            assert 'метаданных' in error_msg or 'Configuration' in error_msg or 'Extension' in error_msg
    
    def test_validate_structure_success_with_old_configuration(self):
        """Тест успешной проверки структуры с Configuration.xml (старая структура)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем полную структуру (старая)
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            project_file = src_path / '.project'
            project_file.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            src_dir = src_path / 'src'
            src_dir.mkdir()
            
            config_xml = dt_inf / 'Configuration.xml'
            config_xml.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            # Не должно быть исключений
            converter._validate_edt_structure(src_path)
    
    def test_validate_structure_success_with_new_configuration(self):
        """Тест успешной проверки структуры с Configuration.mdo (новая структура)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем полную структуру (новая)
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            project_file = src_path / '.project'
            project_file.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            src_dir = src_path / 'src'
            src_dir.mkdir()
            
            config_dir = src_dir / 'Configuration'
            config_dir.mkdir()
            
            config_mdo = config_dir / 'Configuration.mdo'
            config_mdo.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            # Не должно быть исключений
            converter._validate_edt_structure(src_path)
    
    def test_validate_structure_success_with_extension(self):
        """Тест успешной проверки структуры с Extension.xml."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем полную структуру
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            project_file = src_path / '.project'
            project_file.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            src_dir = src_path / 'src'
            src_dir.mkdir()
            
            extension_xml = dt_inf / 'Extension.xml'
            extension_xml.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            # Не должно быть исключений
            converter._validate_edt_structure(src_path)
    
    def test_validate_structure_with_src_directory(self):
        """Тест проверки структуры с директорией src и файлами."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            src_path = Path(tmpdir) / 'edt_project'
            src_path.mkdir()
            
            # Создаем полную структуру
            dt_inf = src_path / 'DT-INF'
            dt_inf.mkdir()
            
            project_file = src_path / '.project'
            project_file.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            src_dir = src_path / 'src'
            src_dir.mkdir()
            
            config_dir = src_dir / 'Configuration'
            config_dir.mkdir()
            
            config_mdo = config_dir / 'Configuration.mdo'
            config_mdo.write_text('<?xml version="1.0" encoding="UTF-8"?>')
            
            # Создаем файлы в src
            (src_dir / 'test1.bsl').write_text('// Test file 1')
            (src_dir / 'test2.bsl').write_text('// Test file 2')
            
            env_vars = {
                'V8_SRC_PATH': str(src_path),
                'V8_DST_PATH': 'report.json'
            }
            converter = ValidationConverter(env_vars, silent=True)
            
            # Не должно быть исключений
            converter._validate_edt_structure(src_path)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты для проверки параметра V8_TEMP_AFTER_CLEAN
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.converters.base.converter import BaseConverter


class TestConverter(BaseConverter):
    """Тестовый конвертер для проверки базовой функциональности"""
    
    def _validate_specific(self):
        """Специфичная валидация"""
        pass
    
    def _do_convert(self):
        """Реализация конвертации"""
        return 0
    
    def get_output_extension(self):
        """Возвращает расширение выходного файла"""
        return '.test'


class TestTempCleanup:
    """Тесты для параметра V8_TEMP_AFTER_CLEAN"""
    
    def test_cleanup_enabled_by_default(self, tmp_path):
        """Проверяет что по умолчанию очистка включена (если параметр не указан)"""
        env_vars = {
            'V8_SRC_PATH': str(tmp_path / 'src'),
            'V8_DST_PATH': str(tmp_path / 'dst.test'),
            'V8_TEMP': str(tmp_path / 'temp')
        }
        
        # Создаем источник
        (tmp_path / 'src').mkdir()
        
        converter = TestConverter(env_vars, silent=True)
        
        # По умолчанию (без параметра) cleanup_on_success должен быть False
        assert converter.cleanup_on_success == False
    
    def test_cleanup_when_param_is_1(self, tmp_path):
        """Проверяет что очистка включается когда V8_TEMP_AFTER_CLEAN=1"""
        env_vars = {
            'V8_SRC_PATH': str(tmp_path / 'src'),
            'V8_DST_PATH': str(tmp_path / 'dst.test'),
            'V8_TEMP': str(tmp_path / 'temp'),
            'V8_TEMP_AFTER_CLEAN': '1'
        }
        
        # Создаем источник
        (tmp_path / 'src').mkdir()
        
        converter = TestConverter(env_vars, silent=True)
        
        # С параметром V8_TEMP_AFTER_CLEAN=1 cleanup_on_success должен быть True
        assert converter.cleanup_on_success == True
    
    def test_cleanup_when_param_is_0(self, tmp_path):
        """Проверяет что очистка отключена когда V8_TEMP_AFTER_CLEAN=0"""
        env_vars = {
            'V8_SRC_PATH': str(tmp_path / 'src'),
            'V8_DST_PATH': str(tmp_path / 'dst.test'),
            'V8_TEMP': str(tmp_path / 'temp'),
            'V8_TEMP_AFTER_CLEAN': '0'
        }
        
        # Создаем источник
        (tmp_path / 'src').mkdir()
        
        converter = TestConverter(env_vars, silent=True)
        
        # С параметром V8_TEMP_AFTER_CLEAN=0 cleanup_on_success должен быть False
        assert converter.cleanup_on_success == False
    
    def test_temp_dir_cleaned_on_success_when_enabled(self, tmp_path):
        """Проверяет что временная директория удаляется при успешной конвертации если V8_TEMP_AFTER_CLEAN=1"""
        env_vars = {
            'V8_SRC_PATH': str(tmp_path / 'src'),
            'V8_DST_PATH': str(tmp_path / 'dst.test'),
            'V8_TEMP': str(tmp_path / 'temp'),
            'V8_TEMP_AFTER_CLEAN': '1'
        }
        
        # Создаем источник
        (tmp_path / 'src').mkdir()
        
        converter = TestConverter(env_vars, silent=True)
        converter.validate()
        
        # Запускаем конвертацию
        result = converter.convert()
        
        assert result == 0
        
        # Проверяем что временная директория была создана и затем удалена
        temp_base = tmp_path / 'temp'
        if temp_base.exists():
            # Проверяем что нет директорий TestConverter_*
            test_dirs = list(temp_base.glob('TestConverter_*'))
            assert len(test_dirs) == 0, "Временная директория не была удалена"
    
    def test_temp_dir_preserved_on_success_when_disabled(self, tmp_path):
        """Проверяет что временная директория сохраняется при успешной конвертации если V8_TEMP_AFTER_CLEAN=0"""
        env_vars = {
            'V8_SRC_PATH': str(tmp_path / 'src'),
            'V8_DST_PATH': str(tmp_path / 'dst.test'),
            'V8_TEMP': str(tmp_path / 'temp'),
            'V8_TEMP_AFTER_CLEAN': '0'
        }
        
        # Создаем источник
        (tmp_path / 'src').mkdir()
        
        converter = TestConverter(env_vars, silent=True)
        converter.validate()
        
        # Запускаем конвертацию
        result = converter.convert()
        
        assert result == 0
        
        # Проверяем что временная директория была создана и НЕ удалена
        temp_base = tmp_path / 'temp'
        assert temp_base.exists(), "Базовая временная директория не существует"
        
        # Проверяем что есть директория TestConverter_*
        test_dirs = list(temp_base.glob('TestConverter_*'))
        assert len(test_dirs) > 0, "Временная директория была удалена, хотя не должна была"
    
    def test_temp_dir_preserved_on_error(self, tmp_path):
        """Проверяет что временная директория всегда сохраняется при ошибке"""
        
        class FailingConverter(TestConverter):
            """Конвертер который всегда падает с ошибкой"""
            
            def _do_convert(self):
                """Возвращает ошибку"""
                return 1
        
        env_vars = {
            'V8_SRC_PATH': str(tmp_path / 'src'),
            'V8_DST_PATH': str(tmp_path / 'dst.test'),
            'V8_TEMP': str(tmp_path / 'temp'),
            'V8_TEMP_AFTER_CLEAN': '1'  # Даже с включенной очисткой
        }
        
        # Создаем источник
        (tmp_path / 'src').mkdir()
        
        converter = FailingConverter(env_vars, silent=True)
        converter.validate()
        
        # Запускаем конвертацию (должна завершиться с ошибкой)
        result = converter.convert()
        
        assert result == 1
        
        # Проверяем что временная директория была создана и НЕ удалена
        temp_base = tmp_path / 'temp'
        assert temp_base.exists(), "Базовая временная директория не существует"
        
        # Проверяем что есть директория FailingConverter_*
        test_dirs = list(temp_base.glob('FailingConverter_*'))
        assert len(test_dirs) > 0, "Временная директория была удалена при ошибке"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

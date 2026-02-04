#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты для функции load_env_file с поддержкой BOM и различных кодировок
"""

import sys
from pathlib import Path
import tempfile
import pytest

# Добавляем корневую директорию проекта в sys.path
_SCRIPT_DIR = Path(__file__).parent.parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from src.core.convert import load_env_file  # type: ignore


class TestEnvFileLoading:
    """Тесты загрузки .env файлов с различными кодировками"""
    
    def test_load_utf8_without_bom(self):
        """Тест чтения UTF-8 файла без BOM"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.env', delete=False) as f:
            f.write('ScriptName=conf2cf\n')
            f.write('V8_DST_PATH=C:\\output\\test.cf\n')
            f.write('# Комментарий\n')
            f.write('V8_VERSION=8.3.27.1989\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert result['ScriptName'] == 'conf2cf'
            assert result['V8_DST_PATH'] == 'C:\\output\\test.cf'
            assert result['V8_VERSION'] == '8.3.27.1989'
            assert '# Комментарий' not in result
        finally:
            Path(temp_path).unlink()
    
    def test_load_utf8_with_bom(self):
        """Тест чтения UTF-8 файла с BOM"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8-sig', suffix='.env', delete=False) as f:
            f.write('ScriptName=dp2epf\n')
            f.write('V8_DST_PATH=D:\\projects\\output\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert result['ScriptName'] == 'dp2epf'
            assert result['V8_DST_PATH'] == 'D:\\projects\\output'
        finally:
            Path(temp_path).unlink()
    
    def test_load_cp1251_encoding(self):
        """Тест чтения файла в кодировке CP1251"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='cp1251', suffix='.env', delete=False) as f:
            f.write('ScriptName=ext2cfe\n')
            f.write('V8_DST_PATH=C:\\Проекты\\расширение.cfe\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert result['ScriptName'] == 'ext2cfe'
            assert 'V8_DST_PATH' in result
        finally:
            Path(temp_path).unlink()
    
    def test_load_with_quotes(self):
        """Тест чтения значений в кавычках"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.env', delete=False) as f:
            f.write('ScriptName="conf2cf"\n')
            f.write("V8_DST_PATH='C:\\output\\test.cf'\n")
            f.write('V8_VERSION=8.3.27.1989\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert result['ScriptName'] == 'conf2cf'
            assert result['V8_DST_PATH'] == 'C:\\output\\test.cf'
            assert result['V8_VERSION'] == '8.3.27.1989'
        finally:
            Path(temp_path).unlink()
    
    def test_load_with_comments(self):
        """Тест игнорирования комментариев"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.env', delete=False) as f:
            f.write('# Это комментарий\n')
            f.write('ScriptName=conf2cf\n')
            f.write('# Еще комментарий\n')
            f.write('V8_DST_PATH=C:\\output\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert len(result) == 2
            assert result['ScriptName'] == 'conf2cf'
            assert result['V8_DST_PATH'] == 'C:\\output'
        finally:
            Path(temp_path).unlink()
    
    def test_load_empty_lines(self):
        """Тест игнорирования пустых строк"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.env', delete=False) as f:
            f.write('\n')
            f.write('ScriptName=conf2cf\n')
            f.write('\n')
            f.write('V8_DST_PATH=C:\\output\n')
            f.write('\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert len(result) == 2
        finally:
            Path(temp_path).unlink()
    
    def test_load_nonexistent_file(self):
        """Тест обработки несуществующего файла"""
        result = load_env_file('/nonexistent/path/file.env', silent=True)
        
        assert result is None
    
    def test_load_with_spaces(self):
        """Тест обработки пробелов вокруг ключей и значений"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.env', delete=False) as f:
            f.write('  ScriptName  =  conf2cf  \n')
            f.write('V8_DST_PATH=  C:\\output  \n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert result['ScriptName'] == 'conf2cf'
            assert result['V8_DST_PATH'] == 'C:\\output'
        finally:
            Path(temp_path).unlink()
    
    def test_load_multiline_value(self):
        """Тест обработки значений с символом = внутри"""
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.env', delete=False) as f:
            f.write('ScriptName=conf2cf\n')
            f.write('V8_COMMAND=/C "echo test=value"\n')
            temp_path = f.name
        
        try:
            result = load_env_file(temp_path, silent=True)
            
            assert result is not None
            assert result['ScriptName'] == 'conf2cf'
            assert result['V8_COMMAND'] == '/C "echo test=value"'
        finally:
            Path(temp_path).unlink()

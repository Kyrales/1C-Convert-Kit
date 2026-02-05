#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты для проверки наличия иконок
"""

import pytest
from pathlib import Path


def test_icon_files_exist():
    """Проверяет наличие файлов иконок"""
    # Определяем корень проекта
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent
    
    # Проверяем иконку 16px
    icon_16 = project_root / 'docs' / 'images' / 'icons8-cyberpunk-gradient-16.png'
    assert icon_16.exists(), f"Иконка 16px не найдена: {icon_16}"
    
    # Проверяем иконку 96px
    icon_96 = project_root / 'docs' / 'images' / 'icons8-cyberpunk-gradient-96.png'
    assert icon_96.exists(), f"Иконка 96px не найдена: {icon_96}"


def test_icon_files_are_readable():
    """Проверяет, что файлы иконок можно прочитать"""
    test_dir = Path(__file__).parent
    project_root = test_dir.parent.parent
    
    icon_16 = project_root / 'docs' / 'images' / 'icons8-cyberpunk-gradient-16.png'
    icon_96 = project_root / 'docs' / 'images' / 'icons8-cyberpunk-gradient-96.png'
    
    # Проверяем, что файлы можно открыть
    with open(icon_16, 'rb') as f:
        data_16 = f.read()
        assert len(data_16) > 0, "Иконка 16px пустая"
        # Проверяем PNG сигнатуру
        assert data_16[:8] == b'\x89PNG\r\n\x1a\n', "Иконка 16px не является PNG файлом"
    
    with open(icon_96, 'rb') as f:
        data_96 = f.read()
        assert len(data_96) > 0, "Иконка 96px пустая"
        # Проверяем PNG сигнатуру
        assert data_96[:8] == b'\x89PNG\r\n\x1a\n', "Иконка 96px не является PNG файлом"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

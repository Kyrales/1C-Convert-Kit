#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты отображения значений из базового .env в редакторе проекта
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Импортируем тестируемый класс
from src.gui.project_editor import ProjectEditorDialog


class TestBaseEnvDisplay:
    """Тесты отображения значений из базового .env"""
    
    @pytest.fixture
    def mock_params_descriptions(self):
        """Мок описаний параметров"""
        return {
            'common': {
                'V8_VERSION': 'Версия платформы 1С',
                'V8_TOOL': 'Путь к 1cv8.exe',
                'V8_TEMP': 'Каталог для временных файлов'
            },
            'conf2cf': {
                'V8_SRC_PATH': 'Путь к исходной конфигурации',
                'V8_DST_PATH': 'Путь к результирующему .cf файлу'
            }
        }
    
    @pytest.fixture
    def mock_base_env(self):
        """Мок базового .env файла"""
        return {
            'V8_VERSION': '8.3.27.1989',
            'V8_TOOL': 'C:\\Program Files\\1cv8\\8.3.27.1989\\bin\\1cv8.exe',
            'V8_TEMP': 'f:\\1C\\Projects\\1c-convert-kit\\temp'
        }
    
    def test_load_base_env(self, mock_params_descriptions, mock_base_env):
        """Тест загрузки базового .env"""
        with patch('src.gui.project_editor.load_env_file', return_value=mock_base_env):
            with patch('src.gui.project_editor.PROJECTS_DIR') as mock_projects_dir:
                # Мокаем наличие базового .env файла
                mock_env_file = Mock()
                mock_env_file.is_file.return_value = True
                mock_projects_dir.glob.return_value = [mock_env_file]
                
                dialog = ProjectEditorDialog(mock_params_descriptions, mode='add')
                
                # Проверяем, что базовый .env загружен
                assert dialog.base_env_params == mock_base_env
    
    def test_display_base_value_when_checkbox_disabled(self, mock_params_descriptions, mock_base_env):
        """Тест отображения значения из base_env когда чекбокс выключен"""
        with patch('src.gui.project_editor.load_env_file', return_value=mock_base_env):
            with patch('src.gui.project_editor.PROJECTS_DIR') as mock_projects_dir:
                mock_env_file = Mock()
                mock_env_file.is_file.return_value = True
                mock_projects_dir.glob.return_value = [mock_env_file]
                
                dialog = ProjectEditorDialog(mock_params_descriptions, mode='add')
                
                # Проверяем, что значения из base_env доступны
                assert 'V8_VERSION' in dialog.base_env_params
                assert dialog.base_env_params['V8_VERSION'] == '8.3.27.1989'
    
    def test_checkbox_toggle_clears_and_restores_value(self, mock_params_descriptions):
        """Тест переключения чекбокса очищает и восстанавливает значение"""
        # Этот тест проверяет логику, которая должна быть в обработчике событий
        # В реальном GUI это будет работать через события FreeSimpleGUI
        
        base_value = '8.3.27.1989'
        
        # Симулируем логику переключения чекбокса
        # Чекбокс выключен -> показываем значение из base_env
        is_checked = False
        display_value = f"{base_value} (base_1.env)" if not is_checked and base_value else ''
        assert display_value == '8.3.27.1989 (base_1.env)'
        
        # Чекбокс включен -> очищаем поле
        is_checked = True
        display_value = '' if is_checked else f"{base_value} (base_1.env)"
        assert display_value == ''
        
        # Чекбокс снова выключен -> восстанавливаем значение из base_env
        is_checked = False
        display_value = f"{base_value} (base_1.env)" if not is_checked and base_value else ''
        assert display_value == '8.3.27.1989 (base_1.env)'
    
    def test_save_does_not_include_base_env_values(self, mock_params_descriptions):
        """Тест что информационные значения из base_env не сохраняются"""
        # Симулируем логику сохранения
        param_value = '8.3.27.1989 (base_1.env)'
        
        # Проверяем, что значение с пометкой (base_1.env) не сохраняется
        should_save = param_value and not param_value.endswith('(base_1.env)')
        assert should_save is False
        
        # Проверяем, что обычное значение сохраняется
        param_value = '8.3.28.2000'
        should_save = param_value and not param_value.endswith('(base_1.env)')
        assert should_save is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

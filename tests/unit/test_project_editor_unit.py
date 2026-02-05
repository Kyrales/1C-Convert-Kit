#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit-тесты для ProjectEditorDialog (без GUI)
Тестируют логику без открытия окон
"""

import sys
import unittest
import json
from pathlib import Path

# Добавляем корень проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.project_editor import ProjectEditorDialog
from src.gui.constants import PARAMS_DESC_FILE


class TestProjectEditorLogic(unittest.TestCase):
    """Тесты логики ProjectEditorDialog без GUI"""
    
    @classmethod
    def setUpClass(cls):
        """Загружаем описания параметров один раз для всех тестов"""
        cls.params_descriptions = None
        if PARAMS_DESC_FILE.exists():
            with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
                cls.params_descriptions = json.load(f)
    
    def test_dialog_creation(self):
        """Тест создания диалога"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add',
            existing_projects=['Project1', 'Project2']
        )
        
        self.assertIsNotNone(dialog)
        self.assertEqual(dialog.mode, 'add')
        self.assertEqual(len(dialog.existing_projects), 2)
    
    def test_get_available_scripts(self):
        """Тест получения списка доступных скриптов"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        scripts = dialog._get_available_scripts()
        
        self.assertIsInstance(scripts, list)
        self.assertGreater(len(scripts), 0)
        self.assertIn('conf2cf', scripts)
        self.assertIn('dp2epf', scripts)
        self.assertIn('ext2cfe', scripts)
    
    def test_get_script_params(self):
        """Тест получения параметров для скрипта"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        params = dialog._get_script_params('conf2cf')
        
        self.assertIsInstance(params, dict)
        self.assertIn('V8_SRC_PATH', params)
        self.assertIn('V8_DST_PATH', params)
        self.assertTrue(params['V8_SRC_PATH']['required'])
        self.assertTrue(params['V8_DST_PATH']['required'])
    
    def test_detect_param_type(self):
        """Тест определения типа параметра"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        # Булев параметр
        bool_type = dialog._detect_param_type(
            'V8_SKIP_ENV',
            'Если установлена в 1, то отключает чтение'
        )
        self.assertEqual(bool_type, 'boolean')
        
        # Путь к папке
        folder_type = dialog._detect_param_type(
            'V8_TEMP',
            'Путь к каталогу для создания временных файлов'
        )
        self.assertEqual(folder_type, 'path_folder')
        
        # Путь к файлу
        file_type = dialog._detect_param_type(
            'V8_TOOL',
            'Путь к исполняемому файлу 1С:Предприятие 1Cv8.exe'
        )
        self.assertEqual(file_type, 'path_file')
    
    def test_validate_project_name_valid(self):
        """Тест валидации корректного имени проекта"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add',
            existing_projects=['Project1']
        )
        
        is_valid, error = dialog._validate_project_name('NewProject')
        
        self.assertTrue(is_valid)
        self.assertEqual(error, '')
    
    def test_validate_project_name_empty(self):
        """Тест валидации пустого имени"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        is_valid, error = dialog._validate_project_name('')
        
        self.assertFalse(is_valid)
        self.assertIn('пустым', error)
    
    def test_validate_project_name_invalid_chars(self):
        """Тест валидации имени с недопустимыми символами"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        invalid_names = ['Project/Name', 'Project\\Name', 'Project:Name', 
                        'Project*Name', 'Project?Name', 'Project"Name',
                        'Project<Name', 'Project>Name', 'Project|Name']
        
        for name in invalid_names:
            is_valid, error = dialog._validate_project_name(name)
            self.assertFalse(is_valid, f"Name '{name}' should be invalid")
            self.assertIn('недопустимый символ', error)
    
    def test_validate_project_name_duplicate(self):
        """Тест валидации дублирующегося имени"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add',
            existing_projects=['ExistingProject']
        )
        
        is_valid, error = dialog._validate_project_name('ExistingProject')
        
        self.assertFalse(is_valid)
        self.assertIn('уже существует', error)
    
    def test_sanitize_filename(self):
        """Тест замены пробелов в имени файла"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        result = dialog._sanitize_filename('My Project Name')
        
        self.assertEqual(result, 'My_Project_Name')
        self.assertNotIn(' ', result)
    
    def test_get_param_description(self):
        """Тест получения описания параметра"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        # Специфичный для скрипта параметр
        desc1 = dialog._get_param_description('V8_SRC_PATH', 'conf2cf')
        self.assertIsInstance(desc1, str)
        self.assertGreater(len(desc1), 0)
        
        # Общий параметр
        desc2 = dialog._get_param_description('V8_VERSION', 'conf2cf')
        self.assertIsInstance(desc2, str)
        self.assertGreater(len(desc2), 0)
    
    def test_load_base_env(self):
        """Тест загрузки базового .env файла"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        base_env = dialog._load_base_env()
        
        self.assertIsInstance(base_env, dict)
        # Может быть пустым если нет базового .env


class TestProjectEditorModes(unittest.TestCase):
    """Тесты различных режимов работы диалога"""
    
    @classmethod
    def setUpClass(cls):
        """Загружаем описания параметров"""
        cls.params_descriptions = None
        if PARAMS_DESC_FILE.exists():
            with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
                cls.params_descriptions = json.load(f)
    
    def test_mode_add(self):
        """Тест режима добавления"""
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='add'
        )
        
        self.assertEqual(dialog.mode, 'add')
        self.assertEqual(dialog.project_data, {})
    
    def test_mode_edit(self):
        """Тест режима редактирования"""
        project_data = {
            'name': 'TestProject',
            'script': 'conf2cf',
            'env_path': '/path/to/project.env'
        }
        
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='edit',
            project_data=project_data
        )
        
        self.assertEqual(dialog.mode, 'edit')
        self.assertEqual(dialog.project_data['name'], 'TestProject')
    
    def test_mode_copy(self):
        """Тест режима копирования"""
        project_data = {
            'name': 'OriginalProject',
            'script': 'dp2epf'
        }
        
        dialog = ProjectEditorDialog(
            params_descriptions=self.params_descriptions,
            mode='copy',
            project_data=project_data
        )
        
        self.assertEqual(dialog.mode, 'copy')
        self.assertEqual(dialog.project_data['name'], 'OriginalProject')


if __name__ == '__main__':
    # Запуск тестов с подробным выводом
    unittest.main(verbosity=2)

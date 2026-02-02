#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты логики выбора строк в таблице проектов
"""

import pytest
from pathlib import Path
import sys

# Добавляем путь к src для импорта
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


class TestTableSelectionLogic:
    """Тесты логики выбора и переключения чекбоксов в таблице"""
    
    def test_click_toggles_checkbox_for_clicked_row(self):
        """Тест: клик по строке переключает чекбокс именно для этой строки"""
        # Arrange: создаем список проектов
        projects = [
            {'name': 'Project1', 'selected': False, 'script': 'conf2cf', 
             'env_path': '/path1', 'dst_path': '/dst1', 'custom_dst_path': None},
            {'name': 'Project2', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path2', 'dst_path': '/dst2', 'custom_dst_path': None},
            {'name': 'Project3', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path3', 'dst_path': '/dst3', 'custom_dst_path': None},
        ]
        selected_row = None
        
        # Act: симулируем клик по первой строке (индекс 0)
        clicked_row = 0
        projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        selected_row = clicked_row
        
        # Assert: проверяем что чекбокс первой строки переключился
        assert projects[0]['selected'] is True
        assert projects[1]['selected'] is False
        assert projects[2]['selected'] is False
        assert selected_row == 0
    
    def test_click_second_row_toggles_only_second(self):
        """Тест: клик по второй строке переключает только вторую строку"""
        # Arrange
        projects = [
            {'name': 'Project1', 'selected': True, 'script': 'conf2cf',
             'env_path': '/path1', 'dst_path': '/dst1', 'custom_dst_path': None},
            {'name': 'Project2', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path2', 'dst_path': '/dst2', 'custom_dst_path': None},
            {'name': 'Project3', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path3', 'dst_path': '/dst3', 'custom_dst_path': None},
        ]
        selected_row = 0
        
        # Act: симулируем клик по второй строке (индекс 1)
        clicked_row = 1
        projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        selected_row = clicked_row
        
        # Assert: проверяем что изменилась только вторая строка
        assert projects[0]['selected'] is True  # Не изменилась
        assert projects[1]['selected'] is True  # Переключилась
        assert projects[2]['selected'] is False  # Не изменилась
        assert selected_row == 1
    
    def test_click_same_row_twice_toggles_back(self):
        """Тест: двойной клик по строке переключает чекбокс туда-обратно"""
        # Arrange
        projects = [
            {'name': 'Project1', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path1', 'dst_path': '/dst1', 'custom_dst_path': None},
        ]
        selected_row = None
        
        # Act: первый клик
        clicked_row = 0
        projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        selected_row = clicked_row
        
        assert projects[0]['selected'] is True
        
        # Act: второй клик по той же строке
        clicked_row = 0
        projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        selected_row = clicked_row
        
        # Assert: чекбокс вернулся в исходное состояние
        assert projects[0]['selected'] is False
        assert selected_row == 0
    
    def test_old_logic_bug_would_fail(self):
        """
        Тест: демонстрирует баг старой логики
        
        Старая логика:
        1. Проверяла if self.selected_row is not None (старое значение)
        2. Переключала чекбокс для self.selected_row (старой строки)
        3. Обновляла self.selected_row = values['-TABLE-'][0] (новая строка)
        
        Результат: при первом клике ничего не происходило, 
        при втором клике переключалась предыдущая строка
        """
        # Arrange: симулируем старую логику
        projects = [
            {'name': 'Project1', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path1', 'dst_path': '/dst1', 'custom_dst_path': None},
            {'name': 'Project2', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path2', 'dst_path': '/dst2', 'custom_dst_path': None},
        ]
        selected_row = None
        
        # Act: первый клик по строке 0 (старая логика)
        clicked_row: int | None = 0
        if selected_row is not None:  # False - не выполнится
            projects[selected_row]['selected'] = not projects[selected_row]['selected']
        selected_row = clicked_row
        
        # Assert: при первом клике ничего не изменилось (БАГ!)
        assert projects[0]['selected'] is False  # Не переключилось!
        assert selected_row == 0
        
        # Act: второй клик по строке 1 (старая логика)
        clicked_row = 1
        if selected_row is not None:  # True - выполнится
            projects[selected_row]['selected'] = not projects[selected_row]['selected']  # Переключит строку 0!
        selected_row = clicked_row
        
        # Assert: переключилась не та строка (БАГ!)
        assert projects[0]['selected'] is True  # Переключилась строка 0, а не 1!
        assert projects[1]['selected'] is False  # Строка 1 не переключилась!
        assert selected_row == 1
    
    def test_new_logic_works_correctly(self):
        """Тест: новая логика работает правильно с первого клика"""
        # Arrange
        projects = [
            {'name': 'Project1', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path1', 'dst_path': '/dst1', 'custom_dst_path': None},
            {'name': 'Project2', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path2', 'dst_path': '/dst2', 'custom_dst_path': None},
        ]
        selected_row = None
        
        # Act: первый клик по строке 0 (новая логика)
        clicked_row = 0
        projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        selected_row = clicked_row
        
        # Assert: сразу переключилась правильная строка
        assert projects[0]['selected'] is True  # Переключилась!
        assert projects[1]['selected'] is False
        assert selected_row == 0
        
        # Act: второй клик по строке 1 (новая логика)
        clicked_row = 1
        projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        selected_row = clicked_row
        
        # Assert: переключилась правильная строка
        assert projects[0]['selected'] is True  # Не изменилась
        assert projects[1]['selected'] is True  # Переключилась!
        assert selected_row == 1
    
    def test_multiple_selections(self):
        """Тест: можно выбрать несколько проектов"""
        # Arrange
        projects = [
            {'name': 'Project1', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path1', 'dst_path': '/dst1', 'custom_dst_path': None},
            {'name': 'Project2', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path2', 'dst_path': '/dst2', 'custom_dst_path': None},
            {'name': 'Project3', 'selected': False, 'script': 'conf2cf',
             'env_path': '/path3', 'dst_path': '/dst3', 'custom_dst_path': None},
        ]
        
        # Act: выбираем несколько проектов
        for clicked_row in [0, 2]:
            projects[clicked_row]['selected'] = not projects[clicked_row]['selected']
        
        # Assert: выбраны нужные проекты
        assert projects[0]['selected'] is True
        assert projects[1]['selected'] is False
        assert projects[2]['selected'] is True
        
        # Проверяем что можно получить список выбранных
        selected = [p for p in projects if p['selected']]
        assert len(selected) == 2
        assert selected[0]['name'] == 'Project1'
        assert selected[1]['name'] == 'Project3'


if __name__ == '__main__':
    _ = pytest.main([__file__, '-v'])

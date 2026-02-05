#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты для проверки выбора скриптов в редакторе проектов
"""

import json
from pathlib import Path
import sys

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.gui.project_editor import ProjectEditorDialog


def test_available_scripts_loaded():
    """Проверяет, что список доступных скриптов загружается из params_descriptions.json"""
    # Загружаем params_descriptions.json
    params_file = Path('src/config/params_descriptions.json')
    with open(params_file, 'r', encoding='utf-8') as f:
        params_descriptions = json.load(f)
    
    # Создаем диалог
    dialog = ProjectEditorDialog(params_descriptions, mode='add')
    
    # Проверяем, что список скриптов не пустой
    assert len(dialog.available_scripts) > 0, "Список доступных скриптов пуст"
    
    # Проверяем, что все скрипты из params_descriptions присутствуют
    expected_scripts = [key for key in params_descriptions.keys() if key != 'common']
    assert set(dialog.available_scripts) == set(expected_scripts), \
        f"Список скриптов не совпадает. Ожидалось: {expected_scripts}, получено: {dialog.available_scripts}"
    
    print(f"✓ Загружено {len(dialog.available_scripts)} скриптов")
    print(f"  Скрипты: {', '.join(sorted(dialog.available_scripts))}")


def test_script_params_loaded():
    """Проверяет, что параметры для каждого скрипта загружаются корректно"""
    # Загружаем params_descriptions.json
    params_file = Path('src/config/params_descriptions.json')
    with open(params_file, 'r', encoding='utf-8') as f:
        params_descriptions = json.load(f)
    
    # Создаем диалог
    dialog = ProjectEditorDialog(params_descriptions, mode='add')
    
    # Проверяем параметры для каждого скрипта
    for script in dialog.available_scripts:
        params = dialog._get_script_params(script)
        
        # Проверяем, что есть хотя бы общие параметры
        assert len(params) > 0, f"Для скрипта {script} не загружены параметры"
        
        # Проверяем, что есть специфичные параметры (V8_SRC_PATH, V8_DST_PATH)
        if script in params_descriptions:
            script_specific_params = params_descriptions[script]
            for param_name in script_specific_params.keys():
                assert param_name in params, \
                    f"Параметр {param_name} для скрипта {script} не найден в загруженных параметрах"
        
        print(f"✓ Скрипт {script}: {len(params)} параметров")


def test_param_descriptions():
    """Проверяет, что описания параметров загружаются корректно"""
    # Загружаем params_descriptions.json
    params_file = Path('src/config/params_descriptions.json')
    with open(params_file, 'r', encoding='utf-8') as f:
        params_descriptions = json.load(f)
    
    # Создаем диалог
    dialog = ProjectEditorDialog(params_descriptions, mode='add')
    
    # Проверяем описания для нескольких параметров
    test_cases = [
        ('conf2cf', 'V8_SRC_PATH', 'Путь к источнику конфигурации'),
        ('dp2epf', 'V8_DST_PATH', 'Путь к каталогу для сохранения'),
        ('ext2cfe', 'V8_EXT_NAME', 'Имя расширения'),
    ]
    
    for script, param, expected_substring in test_cases:
        description = dialog._get_param_description(param, script)
        assert description, f"Описание для {param} в скрипте {script} не найдено"
        assert expected_substring in description, \
            f"Описание для {param} не содержит ожидаемый текст. Получено: {description}"
        print(f"✓ {script}.{param}: описание найдено")


if __name__ == '__main__':
    print("Запуск тестов выбора скриптов...")
    print("=" * 60)
    
    try:
        test_available_scripts_loaded()
        print()
        test_script_params_loaded()
        print()
        test_param_descriptions()
        print()
        print("=" * 60)
        print("✓ Все тесты пройдены успешно!")
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ Тест провален: {e}")
        sys.exit(1)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки улучшений в ProjectEditorDialog
"""

import sys
from pathlib import Path

# Добавляем корень проекта в sys.path
SCRIPT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

import json

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

from src.gui.project_editor import ProjectEditorDialog
from src.gui.constants import PARAMS_DESC_FILE
from tests.unit.gui_test_helper import skip_if_no_gui


if __name__ == '__main__':
    # Проверяем наличие GUI
    if not skip_if_no_gui("test_editor_improvements.py"):
        exit(0)  # Пропускаем тест в headless режиме

    # Загружаем описания параметров
    params_descriptions = None
    if PARAMS_DESC_FILE.exists():
        with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
            params_descriptions = json.load(f)

    # Создаем тестовый диалог
    dialog = ProjectEditorDialog(
        params_descriptions=params_descriptions,
        mode='add',
        existing_projects=['TestProject1', 'TestProject2']
    )

    print("Запуск диалога редактирования проекта...")
    print("\nПроверьте следующие улучшения:")
    print("1. ✓ Кнопка '?' рядом с каждым параметром - показывает описание")
    print("2. ✓ Ctrl+C / Ctrl+V работает в полях ввода")
    print("3. ✓ Кнопка '...' сразу открывает диалог выбора файла/папки")
    print("4. ✓ Недоступные поля имеют темный фон (не белый)")
    print()

    result = dialog.show()

    if result:
        print("\n✓ Проект создан успешно!")
        print(f"  Имя: {result['name']}")
        print(f"  Скрипт: {result['script']}")
        print(f"  Параметров: {len(result['params'])}")
    else:
        print("\n✗ Создание проекта отменено")

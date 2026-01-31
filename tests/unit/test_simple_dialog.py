#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Простой тест открытия диалога редактирования проекта
"""

import json
from pathlib import Path

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

from src.gui.project_editor import ProjectEditorDialog
from src.gui.constants import PARAMS_DESC_FILE

print("Загрузка описаний параметров...")
params_descriptions = None
if PARAMS_DESC_FILE.exists():
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        params_descriptions = json.load(f)
    print(f"✓ Загружено {len(params_descriptions)} групп параметров")
else:
    print("✗ Файл params_descriptions.json не найден")

print("\nСоздание диалога...")
try:
    dialog = ProjectEditorDialog(
        params_descriptions=params_descriptions,
        mode='add',
        existing_projects=['TestProject1', 'TestProject2']
    )
    print("✓ Диалог создан успешно")
except Exception as e:
    print(f"✗ Ошибка создания диалога: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nОткрытие диалога...")
print("Проверьте:")
print("  1. Диалог открывается без ошибок")
print("  2. Контекстное меню работает (правый клик на поле)")
print("  3. Кнопка '?' показывает описание")
print("  4. Кнопка '...' открывает диалог выбора")
print("  5. Недоступные поля имеют темный фон")
print()

try:
    result = dialog.show()
    
    if result:
        print("\n✓ Проект создан успешно!")
        print(f"  Имя: {result['name']}")
        print(f"  Скрипт: {result['script']}")
        print(f"  Параметров: {len(result['params'])}")
    else:
        print("\n✗ Создание проекта отменено")
except Exception as e:
    print(f"\n✗ Ошибка при работе с диалогом: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✓ Тест завершен успешно!")

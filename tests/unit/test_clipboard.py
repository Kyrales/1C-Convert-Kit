#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы буфера обмена в ProjectEditorDialog
"""

import json
from pathlib import Path

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

from src.gui.project_editor import ProjectEditorDialog
from src.gui.constants import PARAMS_DESC_FILE

# Загружаем описания параметров
params_descriptions = None
if PARAMS_DESC_FILE.exists():
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        params_descriptions = json.load(f)

print("=" * 80)
print("ТЕСТ РАБОТЫ БУФЕРА ОБМЕНА В ДИАЛОГЕ РЕДАКТИРОВАНИЯ ПРОЕКТА")
print("=" * 80)
print()
print("Проверьте следующие функции:")
print()
print("1. КОНТЕКСТНОЕ МЕНЮ (правый клик на поле):")
print("   - Копировать")
print("   - Вставить")
print("   - Вырезать")
print("   - Выделить все")
print("   - Отменить")
print()
print("2. ГОРЯЧИЕ КЛАВИШИ:")
print("   - Ctrl+C - копировать выделенный текст")
print("   - Ctrl+V - вставить из буфера обмена")
print("   - Ctrl+X - вырезать выделенный текст")
print("   - Ctrl+A - выделить весь текст в поле")
print("   - Ctrl+Z - отменить последнее действие")
print()
print("3. ТЕСТОВЫЙ СЦЕНАРИЙ:")
print("   a) Введите текст в любое поле (например, V8_VERSION)")
print("   b) Выделите часть текста мышью")
print("   c) Нажмите Ctrl+C (или правый клик → Копировать)")
print("   d) Перейдите в другое поле")
print("   e) Нажмите Ctrl+V (или правый клик → Вставить)")
print("   f) Проверьте, что текст вставился")
print()
print("4. ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:")
print("   - Ctrl+A должен выделить весь текст в активном поле")
print("   - Ctrl+X должен вырезать выделенный текст")
print("   - Ctrl+Z должен отменить последнее изменение")
print()
print("=" * 80)
print()

# Создаем тестовый диалог
dialog = ProjectEditorDialog(
    params_descriptions=params_descriptions,
    mode='add',
    existing_projects=['TestProject1', 'TestProject2']
)

print("Запуск диалога...")
result = dialog.show()

if result:
    print("\n✓ Проект создан успешно!")
    print(f"  Имя: {result['name']}")
    print(f"  Скрипт: {result['script']}")
else:
    print("\n✗ Создание проекта отменено")

print()
print("Если все функции работают корректно, тест пройден! ✓")

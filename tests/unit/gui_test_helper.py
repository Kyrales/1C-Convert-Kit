#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Вспомогательный модуль для GUI тестов
Проверяет наличие графического окружения
"""


def check_gui_available():
    """
    Проверяет доступность графического окружения
    
    Returns:
        tuple: (has_display: bool, error_message: str)
    """
    # Проверяем наличие PySimpleGUI/FreeSimpleGUI
    try:
        import FreeSimpleGUI as sg
    except ImportError:
        try:
            import PySimpleGUI as sg
        except ImportError:
            return False, "PySimpleGUI/FreeSimpleGUI не установлен"
    
    # Проверяем возможность создания Tkinter окна
    try:
        import tkinter as tk
        # Пробуем создать тестовое окно
        test_root = tk.Tk()
        test_root.withdraw()
        test_root.destroy()
        return True, ""
    except Exception as e:
        return False, f"Графическое окружение недоступно: {e}"


def skip_if_no_gui(test_name="GUI тест"):
    """
    Пропускает тест если GUI недоступен
    
    Args:
        test_name: название теста для вывода
        
    Returns:
        bool: True если GUI доступен, False если нужно пропустить
    """
    has_display, error = check_gui_available()
    
    if not has_display:
        print("=" * 80)
        print(f"⊘ ТЕСТ ПРОПУЩЕН: {test_name}")
        print("=" * 80)
        print(f"\nПричина: {error}")
        print("\nЭтот тест требует:")
        print("  - Графическое окружение (X11, Wayland, Windows GUI)")
        print("  - PySimpleGUI или FreeSimpleGUI")
        print("  - Tkinter")
        print("\nДля headless окружения используйте:")
        print("  python tests/unit/test_project_editor_unit.py")
        print("\nИли настройте виртуальный дисплей (Xvfb):")
        print(f"  xvfb-run python {__file__}")
        print("=" * 80)
        return False
    
    return True

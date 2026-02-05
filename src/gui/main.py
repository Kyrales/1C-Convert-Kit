#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI для конвертера 1С файлов в стиле Cyberpunk
Точка входа приложения
"""

import sys

from .sg_import import sg
from .constants import CONVERT_SCRIPT
from .main_window import CyberpunkGUI


def main() -> None:
    """Точка входа"""
    # Проверяем наличие convert.py
    if not CONVERT_SCRIPT.exists():
        _ = sg.popup_error(f'Не найден скрипт convert.py: {CONVERT_SCRIPT}')  # type: ignore
        sys.exit(1)
    
    # Создаем и запускаем GUI
    gui = CyberpunkGUI()
    gui.handle_events()


if __name__ == '__main__':
    main()

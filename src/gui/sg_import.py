#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Централизованный импорт GUI библиотеки.

Обеспечивает единую точку импорта FreeSimpleGUI/PySimpleGUI
для всех GUI модулей приложения.
"""

try:
    import FreeSimpleGUI as sg
except ImportError:
    try:
        import PySimpleGUI as sg  # type: ignore[no-redef]
    except ImportError:
        raise ImportError(
            "Требуется FreeSimpleGUI или PySimpleGUI. "
            "Установите: pip install FreeSimpleGUI"
        )

__all__ = ['sg']

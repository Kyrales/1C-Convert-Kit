#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Константы для GUI приложения
"""

from pathlib import Path

# Версия приложения
VERSION = "1.3.1"

# Цветовая схема Cyberpunk
COLORS = {
    'bg': '#0f0f1e',           # Темный фон
    'bg_secondary': '#1a1a2e', # Вторичный фон
    'primary': '#00d9ff',      # Неоново-синий (основной)
    'accent': '#ff006e',       # Неоново-розовый (акцент)
    'success': '#00ff88',      # Успех
    'error': '#ff0055',        # Ошибка
    'warning': '#ffdd00',      # Предупреждение
    'text': '#e0e0e0',         # Основной текст
    'text_dim': '#808080',     # Приглушенный текст
    'cyan': '#00d9ff',         # Cyan (для маркера S)
    'yellow': '#ffdd00'        # Yellow (для маркера N)
}

# Пути
SCRIPT_DIR = Path(__file__).parent.parent.parent  # Корень проекта
PROJECTS_DIR = SCRIPT_DIR / 'projects'
CONVERT_SCRIPT = SCRIPT_DIR / 'src' / 'core' / 'convert.py'
PARAMS_DESC_FILE = SCRIPT_DIR / 'src' / 'config' / 'params_descriptions.json'
PARAMS_DEPEND_FILE = SCRIPT_DIR / 'src' / 'config' / 'params_depend.json'

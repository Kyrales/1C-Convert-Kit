#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тесты для проверки распознавания маркеров логирования в GUI
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path
_SCRIPT_DIR = Path(__file__).parent.parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from src.gui.conversion_runner import ConversionRunner
from src.gui.constants import COLORS


class TestLogColorRecognition:
    """Тесты для проверки распознавания цветов логов"""
    
    def setup_method(self):
        """Подготовка к тестам"""
        # Создаем mock объект window
        class MockWindow:
            pass
        
        self.runner = ConversionRunner(MockWindow())
    
    def test_warning_marker_preduprezhdenie(self):
        """Тест распознавания маркера [ПРЕДУПРЕЖДЕНИЕ]"""
        line = "[ПРЕДУПРЕЖДЕНИЕ] Это предупреждение"
        color = self.runner._get_log_color(line)
        assert color == COLORS['warning'], f"Ожидался цвет warning, получен {color}"
    
    def test_warning_marker_vnimanie(self):
        """Тест распознавания маркера [ВНИМАНИЕ]"""
        line = "[ВНИМАНИЕ] Это внимание"
        color = self.runner._get_log_color(line)
        assert color == COLORS['warning'], f"Ожидался цвет warning, получен {color}"
    
    def test_warning_word_preduprezhdenie(self):
        """Тест распознавания слова 'предупреждение' в тексте"""
        line = "Это предупреждение о чем-то"
        color = self.runner._get_log_color(line)
        assert color == COLORS['warning'], f"Ожидался цвет warning, получен {color}"
    
    def test_warning_word_vnimanie(self):
        """Тест распознавания слова 'внимание' в тексте"""
        line = "Обратите внимание на это"
        color = self.runner._get_log_color(line)
        assert color == COLORS['warning'], f"Ожидался цвет warning, получен {color}"
    
    def test_warning_word_warn(self):
        """Тест распознавания слова 'warn' в тексте"""
        line = "Warning: something happened"
        color = self.runner._get_log_color(line)
        assert color == COLORS['warning'], f"Ожидался цвет warning, получен {color}"
    
    def test_error_marker(self):
        """Тест распознавания маркера ошибки"""
        line = "[ОШИБКА] Произошла ошибка"
        color = self.runner._get_log_color(line)
        assert color == COLORS['error'], f"Ожидался цвет error, получен {color}"
    
    def test_success_marker(self):
        """Тест распознавания маркера успеха"""
        line = "[УСПЕХ] Операция завершена успешно"
        color = self.runner._get_log_color(line)
        assert color == COLORS['success'], f"Ожидался цвет success, получен {color}"
    
    def test_info_marker(self):
        """Тест распознавания маркера информации"""
        line = "[ИНФО] Информационное сообщение"
        color = self.runner._get_log_color(line)
        assert color == COLORS['primary'], f"Ожидался цвет primary, получен {color}"
    
    def test_debug_marker(self):
        """Тест распознавания маркера отладки"""
        line = "[ОТЛАДКА] Отладочное сообщение"
        color = self.runner._get_log_color(line)
        assert color == COLORS['text_dim'], f"Ожидался цвет text_dim, получен {color}"
    
    def test_regular_text(self):
        """Тест обычного текста без маркеров"""
        line = "Обычный текст без маркеров"
        color = self.runner._get_log_color(line)
        assert color == COLORS['text'], f"Ожидался цвет text, получен {color}"
    
    def test_case_insensitive_warning(self):
        """Тест нечувствительности к регистру для предупреждений"""
        lines = [
            "ПРЕДУПРЕЖДЕНИЕ: что-то",
            "Предупреждение: что-то",
            "предупреждение: что-то",
            "ВНИМАНИЕ: что-то",
            "Внимание: что-то",
            "внимание: что-то",
            "WARNING: something",
            "Warning: something",
            "warning: something"
        ]
        
        for line in lines:
            color = self.runner._get_log_color(line)
            assert color == COLORS['warning'], f"Для строки '{line}' ожидался цвет warning, получен {color}"
    
    def test_error_does_not_override_success(self):
        """Тест что слово 'ошибка' не перекрывает успех если есть оба"""
        line = "Завершено успешно без ошибок"
        color = self.runner._get_log_color(line)
        # Должен быть success, так как есть проверка на отсутствие 'ошибк' и 'error'
        assert color == COLORS['success'], f"Ожидался цвет success, получен {color}"

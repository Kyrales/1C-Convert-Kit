#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Запуск конвертации проектов
"""

from __future__ import annotations

import os
import subprocess
import time
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project_scanner import ProjectDict

from .constants import COLORS, SCRIPT_DIR, CONVERT_SCRIPT
from .utils import format_duration


class ConversionRunner:
    """Запуск конвертации проектов"""
    
    def __init__(self, window: object) -> None:
        self.window = window
        self.is_running: bool = False
        self.total_start_time: float | None = None
        self.project_start_time: float | None = None
    
    def run_conversions(self, projects: "list[ProjectDict]") -> None:  # type: ignore
        """
        Запускает конвертацию выбранных проектов
        
        Args:
            projects: список проектов для конвертации
        """
        self.is_running = True
        total = len(projects)
        
        # Запоминаем время начала всех конвертаций
        self.total_start_time = time.time()
        
        for idx, project in enumerate(projects, 1):
            if not self.is_running:
                break
            
            # Обновляем статус
            status = f"Конвертация: {project['name']}..."
            percent = int((idx - 1) / total * 100)
            _ = self.window.write_event_value('-UPDATE_STATUS-',  # type: ignore[attr-defined]
                                         (idx - 1, total, percent, status))
            
            # Запоминаем время начала проекта
            self.project_start_time = time.time()
            
            # Запускаем конвертацию
            self._run_single_conversion(project)
            
            # Вычисляем время выполнения проекта
            assert self.project_start_time is not None
            project_duration = time.time() - self.project_start_time
            duration_str = format_duration(project_duration)
            
            # Обновляем прогресс
            percent = int(idx / total * 100)
            status = f"Завершено: {project['name']} (Время: {duration_str})"
            _ = self.window.write_event_value('-UPDATE_STATUS-',  # type: ignore[attr-defined]
                                         (idx, total, percent, status))
        
        # Завершение
        if self.is_running:
            # Вычисляем общее время выполнения
            assert self.total_start_time is not None
            total_duration = time.time() - self.total_start_time
            total_duration_str = format_duration(total_duration)
            
            _ = self.window.write_event_value('-CONVERSION_DONE-',  # type: ignore[attr-defined]
                                         (total, total, 100, total_duration_str))
        
        self.is_running = False
    
    def _run_single_conversion(self, project: "ProjectDict") -> None:  # type: ignore
        """
        Запускает конвертацию одного проекта
        
        Args:
            project: словарь с информацией о проекте
        """
        from pathlib import Path as PathType
        
        # Формируем команду
        project_path = PathType(project['env_path']).parent
        cmd = ['python', str(CONVERT_SCRIPT), '--env', str(project_path)]
        
        # Добавляем custom путь если указан
        if project['custom_dst_path']:
            cmd.extend(['--output', project['custom_dst_path']])
        
        # Добавляем флаг отладки если включен
        debug_mode: bool = bool(self.window and self.window['-DEBUG-'].get())  # type: ignore[attr-defined, index]
        if debug_mode:
            cmd.append('--debug')
        
        # Логируем команду с цветом и иконкой
        _ = self.window.write_event_value('-LOG-', {  # type: ignore[attr-defined]
            'text': f"\n{'═'*80}\n▶ Запуск: {project['name']}\n{'═'*80}\n",
            'color': COLORS['primary']
        })
        
        # Выводим команду в режиме отладки
        if debug_mode:
            cmd_str = ' '.join(cmd)
            _ = self.window.write_event_value('-LOG-', {  # type: ignore[attr-defined]
                'text': f"[ОТЛАДКА] Команда: {cmd_str}\n",
                'color': COLORS['text_dim']
            })
        
        try:
            # Запускаем процесс с улучшенной обработкой кодировки
            # Добавляем PYTHONUNBUFFERED=1 для отключения буферизации вывода Python
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # Передаем режим отладки через переменную окружения
            if debug_mode:
                env['CONVERTER_DEBUG'] = '1'
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(SCRIPT_DIR),
                env=env
            )
            
            # Читаем вывод построчно с обработкой разных кодировок
            assert process.stdout is not None
            for line in iter(process.stdout.readline, b''):
                if not self.is_running:
                    process.terminate()
                    break
                
                # Пробуем разные кодировки
                decoded_line = None
                for encoding in ['utf-8', 'cp1251', 'cp866', 'latin-1']:
                    try:
                        decoded_line = line.decode(encoding)
                        break
                    except (UnicodeDecodeError, AttributeError):
                        continue
                
                # Если не удалось декодировать, используем замену ошибочных символов
                if decoded_line is None:
                    decoded_line = line.decode('utf-8', errors='replace')
                
                # Удаляем ANSI escape-коды (цветовые коды)
                decoded_line = re.sub(r'\x1b\[[0-9;]*m', '', decoded_line)
                
                # Отправляем строку с определением цвета
                _ = self.window.write_event_value('-LOG-', {  # type: ignore[attr-defined]
                    'text': decoded_line,
                    'color': self._get_log_color(decoded_line)
                })
            
            _ = process.wait()
            
            if process.returncode == 0:
                # Вычисляем время выполнения проекта
                assert self.project_start_time is not None
                project_duration = time.time() - self.project_start_time
                duration_str = format_duration(project_duration)
                
                _ = self.window.write_event_value('-LOG-', {  # type: ignore[attr-defined]
                    'text': f"✓ Проект {project['name']} завершен успешно. Время выполнения: {duration_str}\n",
                    'color': COLORS['success']
                })
            else:
                _ = self.window.write_event_value('-LOG-', {  # type: ignore[attr-defined]
                    'text': f"✗ Проект {project['name']} завершен с ошибкой (код: {process.returncode})\n",
                    'color': COLORS['error']
                })
        
        except Exception as e:
            _ = self.window.write_event_value('-LOG-', {  # type: ignore[attr-defined]
                'text': f"✗ Исключение при выполнении {project['name']}: {e}\n",
                'color': COLORS['error']
            })
    
    def stop(self) -> None:
        """Останавливает выполнение конвертации"""
        self.is_running = False
    
    def _get_log_color(self, line: str) -> str:
        """
        Определяет цвет для строки лога на основе содержимого
        
        Args:
            line: строка лога
            
        Returns:
            str: цвет из COLORS
        """
        line_lower: str = line.lower()
        
        # Отладка
        if '[ОТЛАДКА]' in line or '[отладка]' in line_lower:
            return COLORS['text_dim']
        
        # Успех
        if any(word in line_lower for word in ['успех', 'завершен', 'completed', 'done', 'ok']):
            if 'ошибк' not in line_lower and 'error' not in line_lower:
                return COLORS['success']
        
        # Ошибка
        if any(word in line_lower for word in ['ошибка', 'failed', 'fail', 'exception', 'исключение']):
            return COLORS['error']
        
        # Предупреждение
        if any(word in line_lower for word in ['внимание', 'предупреждение', 'warn']):
            return COLORS['warning']
        
        # Информация (специальные маркеры)
        if any(marker in line for marker in ['[ИНФО]', 'ℹ', '▶', '●']):
            return COLORS['primary']
        
        # Обычный текст
        return COLORS['text']

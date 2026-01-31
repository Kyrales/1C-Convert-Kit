#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Запуск конвертации проектов
"""

import os
import subprocess
import time
import re

from .constants import COLORS, SCRIPT_DIR, CONVERT_SCRIPT
from .utils import format_duration


class ConversionRunner:
    """Запуск конвертации проектов"""
    
    def __init__(self, window):
        self.window = window
        self.is_running = False
        self.total_start_time = None
        self.project_start_time = None
    
    def run_conversions(self, projects):
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
            self.window.write_event_value('-UPDATE_STATUS-', 
                                         (idx - 1, total, percent, status))
            
            # Запоминаем время начала проекта
            self.project_start_time = time.time()
            
            # Запускаем конвертацию
            self._run_single_conversion(project)
            
            # Вычисляем время выполнения проекта
            project_duration = time.time() - self.project_start_time
            duration_str = format_duration(project_duration)
            
            # Обновляем прогресс
            percent = int(idx / total * 100)
            status = f"Завершено: {project['name']} (Время: {duration_str})"
            self.window.write_event_value('-UPDATE_STATUS-', 
                                         (idx, total, percent, status))
        
        # Завершение
        if self.is_running:
            # Вычисляем общее время выполнения
            total_duration = time.time() - self.total_start_time
            total_duration_str = format_duration(total_duration)
            
            self.window.write_event_value('-CONVERSION_DONE-', 
                                         (total, total, 100, total_duration_str))
        
        self.is_running = False
    
    def _run_single_conversion(self, project):
        """
        Запускает конвертацию одного проекта
        
        Args:
            project: словарь с информацией о проекте
        """
        from pathlib import Path
        
        # Формируем команду
        project_path = Path(project['env_path']).parent
        cmd = ['python', str(CONVERT_SCRIPT), '--env', str(project_path)]
        
        # Добавляем custom путь если указан
        if project['custom_dst_path']:
            cmd.extend(['--output', project['custom_dst_path']])
        
        # Добавляем флаг отладки если включен
        debug_mode = self.window and self.window['-DEBUG-'].get()
        if debug_mode:
            cmd.append('--debug')
        
        # Логируем команду с цветом и иконкой
        self.window.write_event_value('-LOG-', {
            'text': f"\n{'═'*80}\n▶ Запуск: {project['name']}\n{'═'*80}\n",
            'color': COLORS['primary']
        })
        
        # Выводим команду в режиме отладки
        if debug_mode:
            cmd_str = ' '.join(cmd)
            self.window.write_event_value('-LOG-', {
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
                env=env,
                bufsize=1  # Построчная буферизация
            )
            
            # Читаем вывод построчно с обработкой разных кодировок
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
                self.window.write_event_value('-LOG-', {
                    'text': decoded_line,
                    'color': self._get_log_color(decoded_line)
                })
            
            process.wait()
            
            if process.returncode == 0:
                # Вычисляем время выполнения проекта
                project_duration = time.time() - self.project_start_time
                duration_str = format_duration(project_duration)
                
                self.window.write_event_value('-LOG-', {
                    'text': f"✓ Проект {project['name']} завершен успешно. Время выполнения: {duration_str}\n",
                    'color': COLORS['success']
                })
            else:
                self.window.write_event_value('-LOG-', {
                    'text': f"✗ Проект {project['name']} завершен с ошибкой (код: {process.returncode})\n",
                    'color': COLORS['error']
                })
        
        except Exception as e:
            self.window.write_event_value('-LOG-', {
                'text': f"✗ Исключение при выполнении {project['name']}: {e}\n",
                'color': COLORS['error']
            })
    
    def stop(self):
        """Останавливает выполнение конвертации"""
        self.is_running = False
    
    def _get_log_color(self, line):
        """
        Определяет цвет для строки лога на основе содержимого
        
        Args:
            line: строка лога
            
        Returns:
            str: цвет из COLORS
        """
        line_lower = line.lower()
        
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

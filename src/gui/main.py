#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GUI для конвертера 1С файлов в стиле Cyberpunk
"""

import os
import sys
import subprocess
import threading
import re
from pathlib import Path
from datetime import datetime

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

# Импортируем функции из convert.py
from ..core.convert import load_env_file

# ============================================================================
# КОНСТАНТЫ
# ============================================================================

VERSION = "1.0.3"

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
    'text_dim': '#808080'      # Приглушенный текст
}

# Пути
SCRIPT_DIR = Path(__file__).parent.parent.parent  # Корень проекта
PROJECTS_DIR = SCRIPT_DIR / 'projects'
CONVERT_SCRIPT = SCRIPT_DIR / 'src' / 'core' / 'convert.py'
PARAMS_DESC_FILE = SCRIPT_DIR / 'src' / 'config' / 'params_descriptions.json'

# ============================================================================
# КЛАСС ДЛЯ СКАНИРОВАНИЯ ПРОЕКТОВ
# ============================================================================

class ProjectScanner:
    """Сканирование и загрузка информации о проектах"""
    
    @staticmethod
    def scan_projects():
        """
        Сканирует папку projects и возвращает список проектов
        
        Returns:
            list: список словарей с информацией о проектах
        """
        projects = []
        
        if not PROJECTS_DIR.exists():
            return projects
        
        # Ищем все подпапки с .env файлами
        for item in PROJECTS_DIR.iterdir():
            if not item.is_dir():
                continue
            
            # Пропускаем служебные папки
            if item.name.startswith('.') or item.name.startswith('__'):
                continue
            
            # Ищем .env файлы в папке
            env_files = list(item.glob('*.env'))
            if not env_files:
                continue
            
            # Берем первый .env файл
            env_file = env_files[0]
            
            # Читаем ScriptName и V8_DST_PATH из .env
            script_name, dst_path = ProjectScanner._read_env_data(env_file)
            
            # Если ScriptName не указан, пропускаем проект
            if not script_name:
                continue
            
            # Создаем запись о проекте
            project = {
                'name': item.name,
                'script': script_name,
                'env_path': str(env_file),
                'dst_path': dst_path,
                'custom_dst_path': None,
                'selected': False
            }
            
            projects.append(project)
        
        # Сортируем по имени
        projects.sort(key=lambda x: x['name'])
        
        return projects
    
    @staticmethod
    def _read_env_data(env_file):
        """
        Читает ScriptName и V8_DST_PATH из .env файла
        
        Args:
            env_file: путь к .env файлу
            
        Returns:
            tuple: (script_name, dst_path)
        """
        script_name = ''
        dst_path = ''
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ScriptName='):
                        value = line.split('=', 1)[1]
                        script_name = value.strip('"').strip("'")
                    elif line.startswith('V8_DST_PATH='):
                        value = line.split('=', 1)[1]
                        dst_path = value.strip('"').strip("'")
        except Exception:
            pass
        
        return script_name, dst_path

# ============================================================================
# КЛАСС ДЛЯ ЗАПУСКА КОНВЕРТАЦИИ
# ============================================================================

class ConversionRunner:
    """Запуск конвертации проектов"""
    
    def __init__(self, window):
        self.window = window
        self.is_running = False
    
    def run_conversions(self, projects):
        """
        Запускает конвертацию выбранных проектов
        
        Args:
            projects: список проектов для конвертации
        """
        self.is_running = True
        total = len(projects)
        
        for idx, project in enumerate(projects, 1):
            if not self.is_running:
                break
            
            # Обновляем статус
            status = f"Конвертация: {project['name']}..."
            percent = int((idx - 1) / total * 100)
            self.window.write_event_value('-UPDATE_STATUS-', 
                                         (idx - 1, total, percent, status))
            
            # Запускаем конвертацию
            self._run_single_conversion(project)
            
            # Обновляем прогресс
            percent = int(idx / total * 100)
            status = f"Завершено: {project['name']}"
            self.window.write_event_value('-UPDATE_STATUS-', 
                                         (idx, total, percent, status))
        
        # Завершение
        if self.is_running:
            self.window.write_event_value('-CONVERSION_DONE-', 
                                         (total, total, 100))
        
        self.is_running = False
    
    def _run_single_conversion(self, project):
        """
        Запускает конвертацию одного проекта
        
        Args:
            project: словарь с информацией о проекте
        """
        # Формируем команду
        project_path = Path(project['env_path']).parent
        cmd = ['python', str(CONVERT_SCRIPT), '--env', str(project_path)]
        
        # Добавляем custom путь если указан
        if project['custom_dst_path']:
            cmd.extend(['--output', project['custom_dst_path']])
        
        # Логируем команду
        self.window.write_event_value('-LOG-', 
            f"\n{'='*80}\n[INFO] Запуск: {project['name']}\n{'='*80}\n")
        
        try:
            # Запускаем процесс с улучшенной обработкой кодировки
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(SCRIPT_DIR)
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
                import re
                decoded_line = re.sub(r'\x1b\[[0-9;]*m', '', decoded_line)
                
                self.window.write_event_value('-LOG-', decoded_line)
            
            process.wait()
            
            if process.returncode == 0:
                self.window.write_event_value('-LOG-', 
                    f"[SUCCESS] Проект {project['name']} завершен успешно\n")
            else:
                self.window.write_event_value('-LOG-', 
                    f"[ERROR] Проект {project['name']} завершен с ошибкой (код: {process.returncode})\n")
        
        except Exception as e:
            self.window.write_event_value('-LOG-', 
                f"[ERROR] Исключение при выполнении {project['name']}: {e}\n")
    
    def stop(self):
        """Останавливает выполнение конвертации"""
        self.is_running = False

# ============================================================================
# ГЛАВНЫЙ КЛАСС GUI
# ============================================================================

class CyberpunkGUI:
    """Главный класс графического интерфейса"""
    
    def __init__(self):
        self.projects = []
        self.selected_row = None
        self.runner = None
        self.conversion_thread = None
        self.params_descriptions = self._load_params_descriptions()
        
        # Настраиваем тему
        self._setup_theme()
        
        # Сканируем проекты
        self.scan_projects()
        
        # Создаем окно
        self.window = sg.Window(
            f'1C Files Converter - Cyberpunk Edition | Версия {VERSION}',
            self.create_layout(),
            size=(1600, 750),  # Еще больше увеличен размер окна
            finalize=True,
            resizable=True,
            background_color=COLORS['bg'],
            return_keyboard_events=True  # Включаем обработку клавиш
        )
        
        # Настраиваем таблицу
        self.table = self.window['-TABLE-']
        self.details_table = self.window['-DETAILS_TABLE-']
        self.log_output = self.window['-LOG-']
        
        # Обновляем таблицу
        self.update_table()
    
    def _load_params_descriptions(self):
        """Загружает описания параметров из JSON файла"""
        try:
            if PARAMS_DESC_FILE.exists():
                import json
                with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data
        except Exception:
            pass
        return None
    
    def _setup_theme(self):
        """Настройка Cyberpunk темы"""
        # Используем встроенную темную тему как основу
        sg.theme('DarkBlack')
    
    def scan_projects(self):
        """Сканирует проекты"""
        self.projects = ProjectScanner.scan_projects()
    
    def create_layout(self):
        """Создает layout интерфейса"""
        
        # Вкладка "Проекты"
        projects_tab = [
            # Таблица проектов
            [sg.Table(
                values=[],
                headings=['✓', 'Наименование', 'Скрипт', 'Путь выгрузки'],
                key='-TABLE-',
                enable_events=True,
                select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                auto_size_columns=False,
                col_widths=[3, 40, 15, 90],
                num_rows=10,
                font=('Consolas', 13),
                background_color=COLORS['bg_secondary'],
                text_color=COLORS['primary'],
                alternating_row_color=COLORS['bg'],
                header_background_color=COLORS['bg'],
                header_text_color=COLORS['primary'],
                justification='left',
                selected_row_colors=(COLORS['bg'], COLORS['accent']),
            )],
            
            # Кнопки управления
            [
                sg.Button('Выбрать все', key='-SELECT_ALL-', 
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0),
                sg.Button('Снять все', key='-DESELECT_ALL-', 
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0),
                sg.Button('Вверх ▲', key='-MOVE_UP-', 
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0),
                sg.Button('Вниз ▼', key='-MOVE_DOWN-', 
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0),
                sg.Button('Изменить путь...', key='-CHANGE_PATH-', 
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0),
                sg.Button('Обновить проекты', key='-REFRESH-', 
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0)
            ],
            
            # Разделитель
            [sg.HorizontalSeparator(color=COLORS['primary'])],
            
            # Заголовок панели деталей
            [sg.Text('Детали проекта:', 
                    text_color=COLORS['primary'], 
                    background_color=COLORS['bg'],
                    font=('Consolas', 11, 'bold'))],
            
            # Таблица деталей .env файла
            [sg.Table(
                values=[],
                headings=['Параметр', 'Значение', 'Описание'],
                key='-DETAILS_TABLE-',
                enable_events=False,
                auto_size_columns=False,
                col_widths=[30, 60, 110],
                num_rows=15,
                font=('Consolas', 10),
                background_color=COLORS['bg_secondary'],
                text_color=COLORS['text'],
                alternating_row_color=COLORS['bg'],
                header_background_color=COLORS['bg'],
                header_text_color=COLORS['accent'],
                justification='left',
            )]
        ]
        
        # Вкладка "Лог выполнения"
        log_tab = [
            [sg.Multiline(
                '',
                key='-LOG-',
                size=(160, 35),  # Увеличен размер, т.к. освободилось место
                font=('Consolas', 9),
                background_color=COLORS['bg_secondary'],
                text_color=COLORS['text'],
                autoscroll=True,
                disabled=False,
                write_only=False,
                no_scrollbar=False,
                border_width=0,
                reroute_stdout=False,
                reroute_stderr=False,
                reroute_cprint=False,
                right_click_menu=['', ['Копировать', 'Выделить все']]
            )],
            [
                sg.Button('Очистить лог', key='-CLEAR_LOG-',
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0),
                sg.Button('Сохранить лог', key='-SAVE_LOG-',
                         button_color=(COLORS['text'], COLORS['bg_secondary']),
                         border_width=0)
            ]
        ]
        
        # Главный layout с вкладками и элементами управления внизу
        layout = [
            # Вкладки
            [sg.TabGroup([
                [sg.Tab('Проекты', projects_tab, 
                       background_color=COLORS['bg'],
                       border_width=0)],
                [sg.Tab('Лог выполнения', log_tab, 
                       background_color=COLORS['bg'],
                       border_width=0)]
            ], key='-TABS-', 
               background_color=COLORS['bg'],
               tab_background_color=COLORS['bg_secondary'],
               selected_background_color=COLORS['primary'],
               selected_title_color=COLORS['bg'],
               title_color=COLORS['text'],
               border_width=0)],
            
            # Разделитель
            [sg.HorizontalSeparator(color=COLORS['primary'])],
            
            # Прогресс-бар (всегда видим)
            [sg.Text('Готов к запуску', key='-PROGRESS_TEXT-', 
                    text_color=COLORS['text'], 
                    background_color=COLORS['bg'],
                    font=('Consolas', 10))],
            [sg.ProgressBar(100, orientation='h', size=(140, 20), 
                           key='-PROGRESS_BAR-', 
                           bar_color=(COLORS['primary'], COLORS['bg_secondary']))],
            
            # Кнопка ВЫПОЛНИТЬ (всегда видима)
            [sg.Button('ВЫПОЛНИТЬ (F5)', key='-EXECUTE-', 
                      size=(20, 2),
                      button_color=(COLORS['bg'], COLORS['primary']),
                      font=('Arial', 14, 'bold'),
                      border_width=0)]
        ]
        
        return layout
    
    def update_table(self):
        """Обновляет данные в таблице"""
        table_data = []
        for idx, project in enumerate(self.projects):
            check = '✓' if project['selected'] else ''
            # Добавляем стрелку для текущей выбранной строки
            marker = '→' if idx == self.selected_row else ''
            name = f"{marker} {project['name']}" if marker else project['name']
            dst = project['custom_dst_path'] or project['dst_path']
            table_data.append([check, name, project['script'], dst])
        
        self.table.update(values=table_data)
        
        # Обновляем таблицу деталей
        self.update_details_table()
    
    def _get_param_description(self, param_name, script_name):
        """
        Получает описание параметра из JSON
        
        Args:
            param_name: имя параметра (без источника в скобках)
            script_name: имя скрипта (например: conf2cf.cmd)
            
        Returns:
            str: описание параметра или пустая строка
        """
        if not self.params_descriptions:
            return ''
        
        # Сначала ищем в специфичных для скрипта
        if script_name in self.params_descriptions:
            if param_name in self.params_descriptions[script_name]:
                return self.params_descriptions[script_name][param_name]
        
        # Затем ищем в общих
        if 'common' in self.params_descriptions:
            if param_name in self.params_descriptions['common']:
                return self.params_descriptions['common'][param_name]
        
        return ''
    
    def update_details_table(self):
        """Обновляет таблицу деталей выбранного проекта с объединением базового .env"""
        if self.selected_row is None or self.selected_row >= len(self.projects):
            self.details_table.update(values=[])
            return
        
        project = self.projects[self.selected_row]
        project_env_path = project['env_path']
        script_name = project.get('script', '')
        
        details_data = []
        
        try:
            # Собираем список .env файлов как в convert.py
            env_files = []
            base_env_name = None
            
            # 1. Сначала ищем базовый .env в корне projects/ (любой .env файл не в подпапках)
            base_env_files = [f for f in PROJECTS_DIR.glob('*.env') if f.is_file()]
            if base_env_files:
                # Берем первый найденный
                base_env_path = base_env_files[0]
                env_files.append(str(base_env_path))
                base_env_name = base_env_path.name
            
            # 2. Затем .env проекта
            env_files.append(project_env_path)
            
            # Загружаем каждый файл отдельно для отслеживания источника и значений
            base_params = {}  # Параметры из базового файла
            project_params = {}  # Параметры из проекта
            
            for env_file in env_files:
                env_vars = load_env_file(env_file, silent=True)
                if env_vars:
                    source_name = Path(env_file).name
                    if source_name == base_env_name:
                        base_params = env_vars.copy()
                    else:
                        project_params = env_vars.copy()
            
            project_env_name = Path(project_env_path).name
            
            # 1. ScriptName всегда первым
            if 'ScriptName' in project_params:
                param_name = 'ScriptName'
                value = project_params['ScriptName']
                # Проверяем переопределение
                if param_name in base_params and base_params[param_name] != value:
                    value = f"{value} (в {base_env_name} = {base_params[param_name]})"
                description = self._get_param_description(param_name, script_name)
                details_data.append([param_name, value, description])
            
            # 2. Остальные параметры из проекта (кроме ScriptName)
            for param, value in sorted(project_params.items()):
                if param == 'ScriptName':
                    continue
                # Проверяем переопределение
                if param in base_params and base_params[param] != value:
                    value = f"{value} (в {base_env_name} = {base_params[param]})"
                description = self._get_param_description(param, script_name)
                details_data.append([param, value, description])
            
            # 3. Параметры только из базового файла (не переопределенные)
            if base_env_name:
                for param, value in sorted(base_params.items()):
                    if param not in project_params:
                        param_with_source = f"{param} ({base_env_name})"
                        description = self._get_param_description(param, script_name)
                        details_data.append([param_with_source, value, description])
            
        except Exception as e:
            details_data.append(['Ошибка', f'Не удалось прочитать файлы: {e}', ''])
        
        self.details_table.update(values=details_data)
    
    def handle_events(self):
        """Обработка событий"""
        while True:
            event, values = self.window.read()
            
            if event == sg.WIN_CLOSED:
                break
            
            # F5 - Выполнить
            elif event == 'F5:116':  # F5 key code
                self._execute_conversion()
            
            # Выбор строки в таблице
            elif event == '-TABLE-':
                if values['-TABLE-']:
                    self.selected_row = values['-TABLE-'][0]
                    # Переключаем чекбокс
                    self.projects[self.selected_row]['selected'] = \
                        not self.projects[self.selected_row]['selected']
                    self.update_table()
            
            # Выбрать все
            elif event == '-SELECT_ALL-':
                for project in self.projects:
                    project['selected'] = True
                self.update_table()
            
            # Снять все
            elif event == '-DESELECT_ALL-':
                for project in self.projects:
                    project['selected'] = False
                self.update_table()
            
            # Переместить вверх
            elif event == '-MOVE_UP-':
                self._move_row(-1)
            
            # Переместить вниз
            elif event == '-MOVE_DOWN-':
                self._move_row(1)
            
            # Изменить путь
            elif event == '-CHANGE_PATH-':
                self._change_path()
            
            # Обновить проекты
            elif event == '-REFRESH-':
                self.scan_projects()
                self.selected_row = None
                self.update_table()
                self.log_output.update('[INFO] Проекты обновлены\n', append=True)
            
            # Выполнить
            elif event == '-EXECUTE-':
                self._execute_conversion()
            
            # Очистить лог
            elif event == '-CLEAR_LOG-' or event == 'Очистить':
                self.log_output.update('')
            
            # Сохранить лог
            elif event == '-SAVE_LOG-':
                self._save_log()
            
            # Копировать (из контекстного меню)
            elif event == 'Копировать':
                try:
                    # Получаем выделенный текст
                    selected_text = self.log_output.Widget.selection_get()
                    if selected_text:
                        self.window.TKroot.clipboard_clear()
                        self.window.TKroot.clipboard_append(selected_text)
                except:
                    # Если ничего не выделено, копируем весь текст
                    all_text = self.log_output.get()
                    if all_text:
                        self.window.TKroot.clipboard_clear()
                        self.window.TKroot.clipboard_append(all_text)
            
            # Выделить все (из контекстного меню)
            elif event == 'Выделить все':
                try:
                    self.log_output.Widget.tag_add('sel', '1.0', 'end')
                except:
                    pass
            
            # Обновление статуса
            elif event == '-UPDATE_STATUS-':
                completed, total, percent, status = values[event]
                self.window['-PROGRESS_TEXT-'].update(
                    f'Выполнено: {completed} из {total} проектов ({percent}%)')
                self.window['-PROGRESS_BAR-'].update(percent)
                self.log_output.update(f'[INFO] {status}\n', append=True)
            
            # Завершение конвертации
            elif event == '-CONVERSION_DONE-':
                completed, total, percent = values[event]
                self.window['-PROGRESS_TEXT-'].update(
                    f'Готово! Выполнено: {completed} из {total} ({percent}%)')
                self.window['-PROGRESS_BAR-'].update(100)
                # Убрано всплывающее окно
            
            # Лог
            elif event == '-LOG-':
                self.log_output.update(values[event], append=True)
        
        # Останавливаем конвертацию если запущена
        if self.runner:
            self.runner.stop()
        
        self.window.close()
    
    def _move_row(self, direction):
        """Перемещает выбранную строку вверх или вниз"""
        if self.selected_row is None:
            return
        
        new_idx = self.selected_row + direction
        
        if 0 <= new_idx < len(self.projects):
            # Меняем местами
            self.projects[self.selected_row], self.projects[new_idx] = \
                self.projects[new_idx], self.projects[self.selected_row]
            
            self.selected_row = new_idx
            self.update_table()
    
    def _change_path(self):
        """Изменяет путь выгрузки для выбранного проекта"""
        if self.selected_row is None:
            sg.popup('Выберите проект в таблице', 
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        
        # Определяем тип скрипта
        script_lower = project['script'].lower()
        
        if '2cf' in script_lower or '2cfe' in script_lower:
            # Выбор файла
            new_path = sg.popup_get_file(
                'Выберите файл для сохранения',
                save_as=True,
                file_types=(('CF Files', '*.cf'), ('CFE Files', '*.cfe'), ('All Files', '*.*')),
                background_color=COLORS['bg'],
                text_color=COLORS['text']
            )
        else:
            # Выбор папки
            new_path = sg.popup_get_folder(
                'Выберите папку для сохранения',
                background_color=COLORS['bg'],
                text_color=COLORS['text']
            )
        
        if new_path:
            project['custom_dst_path'] = new_path
            self.update_table()
    
    def _execute_conversion(self):
        """Запускает конвертацию выбранных проектов"""
        # Получаем выбранные проекты
        selected = [p for p in self.projects if p['selected']]
        
        if not selected:
            sg.popup('Выберите хотя бы один проект', 
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        # Переключаемся на вкладку лога
        self.window['-TABS-'].Widget.select(1)
        
        # Очищаем лог
        self.log_output.update('')
        
        # Сбрасываем прогресс
        self.window['-PROGRESS_BAR-'].update(0)
        self.window['-PROGRESS_TEXT-'].update('Запуск конвертации...')
        
        # Запускаем в отдельном потоке
        self.runner = ConversionRunner(self.window)
        self.conversion_thread = threading.Thread(
            target=self.runner.run_conversions,
            args=(selected,),
            daemon=True
        )
        self.conversion_thread.start()
    
    def _save_log(self):
        """Сохраняет лог в файл"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'converter_log_{timestamp}.log'
        # Путь к папке logs (не создаем пока)
        logs_dir = SCRIPT_DIR / 'logs'
        # Полный путь с каталогом logs
        default_path = str(logs_dir / default_name)
        
        file_path = sg.popup_get_file(
            'Сохранить лог',
            save_as=True,
            default_extension='.log',
            file_types=(('Log Files', '*.log'), ('All Files', '*.*')),
            default_path=default_path,
            background_color=COLORS['bg'],
            text_color=COLORS['text']
        )
        
        if file_path:
            try:
                # Создаем папку logs если не существует (только при сохранении)
                file_dir = Path(file_path).parent
                file_dir.mkdir(parents=True, exist_ok=True)
                
                # Сохраняем в UTF-8 для корректного отображения
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_output.get())
                sg.popup(f'Лог сохранен: {file_path}', 
                        background_color=COLORS['bg'],
                        text_color=COLORS['success'])
            except Exception as e:
                sg.popup(f'Ошибка сохранения: {e}', 
                        background_color=COLORS['bg'],
                        text_color=COLORS['error'])

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Точка входа"""
    # Проверяем наличие convert.py
    if not CONVERT_SCRIPT.exists():
        sg.popup_error(f'Не найден скрипт convert.py: {CONVERT_SCRIPT}')
        sys.exit(1)
    
    # Создаем и запускаем GUI
    gui = CyberpunkGUI()
    gui.handle_events()

if __name__ == '__main__':
    main()

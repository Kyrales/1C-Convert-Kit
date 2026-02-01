#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Главное окно GUI приложения
"""

import sys
import threading
import shutil
from pathlib import Path
from datetime import datetime

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

from ..core.convert import load_env_file
from .constants import VERSION, COLORS, SCRIPT_DIR, PROJECTS_DIR, CONVERT_SCRIPT, PARAMS_DESC_FILE
from .project_scanner import ProjectScanner
from .project_editor import ProjectEditorDialog
from .conversion_runner import ConversionRunner


class CyberpunkGUI:
    """Главный класс графического интерфейса"""
    
    def __init__(self):
        self.projects = []
        self.selected_row = None
        self.runner = None
        self.conversion_thread = None
        self.params_descriptions = self._load_params_descriptions()
        self.debug_mode = False  # Режим отладки
        
        # Настраиваем тему
        self._setup_theme()
        
        # Сканируем проекты
        self.scan_projects()
        
        # Создаем окно
        icon_path = SCRIPT_DIR / 'docs' / 'images' / 'icons8-cyberpunk-gradient-16.ico'
        self.window = sg.Window(
            f'1C-Convert-Kit - Cyberpunk Edition | Версия {VERSION}',
            self.create_layout(),
            size=(1600, 750),
            finalize=True,
            resizable=True,
            background_color=COLORS['bg'],
            return_keyboard_events=True,
            icon=str(icon_path) if icon_path.exists() else None
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
            # Кнопки управления проектами (над таблицей)
            [
                sg.Button('Добавить', key='-ADD_PROJECT-', 
                         button_color=(COLORS['bg'], COLORS['success']),
                         border_width=0, font=('Arial', 10, 'bold')),
                sg.Button('Изменить', key='-EDIT_PROJECT-', 
                         button_color=(COLORS['bg'], COLORS['primary']),
                         border_width=0, font=('Arial', 10, 'bold')),
                sg.Button('Копировать', key='-COPY_PROJECT-', 
                         button_color=(COLORS['bg'], COLORS['accent']),
                         border_width=0, font=('Arial', 10, 'bold')),
                sg.Button('Удалить', key='-DELETE_PROJECT-', 
                         button_color=(COLORS['bg'], COLORS['error']),
                         border_width=0, font=('Arial', 10, 'bold'))
            ],
            
            # Таблица проектов и иконка
            [
                sg.Table(
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
                ),
                sg.Image(str(SCRIPT_DIR / 'docs' / 'images' / 'icons8-cyberpunk-gradient-96.png'),
                        background_color=COLORS['bg'])
            ],
            
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
                size=(160, 35),
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
            
            # Кнопка ВЫПОЛНИТЬ и чекбокс Отладка
            [
                sg.Button('ВЫПОЛНИТЬ (F5)', key='-EXECUTE-', 
                         size=(20, 2),
                         button_color=(COLORS['bg'], COLORS['primary']),
                         font=('Arial', 14, 'bold'),
                         border_width=0),
                sg.Checkbox('Отладка', key='-DEBUG-', 
                           default=False,
                           enable_events=True,
                           text_color=COLORS['text'],
                           background_color=COLORS['bg'],
                           font=('Consolas', 10))
            ]
        ]
        
        return layout
    
    def update_table(self):
        """Обновляет данные в таблице"""
        table_data = []
        for idx, project in enumerate(self.projects):
            check = '✓' if project['selected'] else ''
            # Добавляем стрелку для текущей выбранной строки
            marker = '>' if idx == self.selected_row else ''
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
            script_name: имя скрипта (например: conf2cf или conf2cf.cmd)
            
        Returns:
            str: описание параметра или пустая строка
        """
        if not self.params_descriptions:
            return ''
        
        # Нормализуем имя скрипта - добавляем .cmd если нет
        script_key = script_name if script_name.endswith('.cmd') else f"{script_name}.cmd"
        
        # Сначала ищем в специфичных для скрипта
        if script_key in self.params_descriptions:
            if param_name in self.params_descriptions[script_key]:
                return self.params_descriptions[script_key][param_name]
        
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
            
            # Чекбокс отладки
            elif event == '-DEBUG-':
                self.debug_mode = values['-DEBUG-']
                status = "включен" if self.debug_mode else "выключен"
                self.log_output.print(f'ℹ Режим отладки {status}\n', 
                                     text_color=COLORS['primary'], 
                                     end='')
            
            # Выбор строки в таблице
            elif event == '-TABLE-':
                if values['-TABLE-']:
                    self.selected_row = values['-TABLE-'][0]
                    # Переключаем чекбокс
                    self.projects[self.selected_row]['selected'] = \
                        not self.projects[self.selected_row]['selected']
                    self.update_table()
            
            # Добавить проект
            elif event == '-ADD_PROJECT-':
                self._add_project()
            
            # Изменить проект
            elif event == '-EDIT_PROJECT-':
                self._edit_project()
            
            # Копировать проект
            elif event == '-COPY_PROJECT-':
                self._copy_project()
            
            # Удалить проект
            elif event == '-DELETE_PROJECT-':
                self._delete_project()
            
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
                self.log_output.print('✓ Проекты обновлены\n', 
                                     text_color=COLORS['success'], 
                                     end='')
            
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
                # Цветной вывод статуса
                self.log_output.print(f'ℹ {status}\n', text_color=COLORS['primary'], end='')
            
            # Завершение конвертации
            elif event == '-CONVERSION_DONE-':
                completed, total, percent, total_duration_str = values[event]
                self.window['-PROGRESS_TEXT-'].update(
                    f'Готово! Выполнено: {completed} из {total} ({percent}%). Общее время: {total_duration_str}')
                self.window['-PROGRESS_BAR-'].update(100)
            
            # Лог с цветом
            elif event == '-LOG-':
                log_data = values[event]
                if isinstance(log_data, dict):
                    # Новый формат с цветом
                    self.log_output.print(log_data['text'], 
                                         text_color=log_data['color'], 
                                         end='')
                else:
                    # Старый формат (обратная совместимость)
                    self.log_output.update(log_data, append=True)
        
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
    
    def _add_project(self):
        """Добавляет новый проект"""
        existing_names = [p['name'] for p in self.projects]
        
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            mode='add',
            existing_projects=existing_names
        )
        
        result = dialog.show()
        
        if result:
            # Создаем папку проекта
            project_name = result['name']
            project_folder = PROJECTS_DIR / project_name
            
            try:
                project_folder.mkdir(parents=True, exist_ok=False)
                
                # Создаем .env файл
                env_filename = f"{self._sanitize_filename(project_name)}_{result['script']}.env"
                env_path = project_folder / env_filename
                
                self._save_env_file(env_path, result['params'])
                
                # Обновляем список проектов
                self.scan_projects()
                
                # Находим и выбираем новый проект
                for idx, project in enumerate(self.projects):
                    if project['name'] == project_name:
                        self.selected_row = idx
                        break
                
                self.update_table()
                
                self.log_output.print(f'✓ Проект "{project_name}" успешно создан\n', 
                                     text_color=COLORS['success'], end='')
            
            except Exception as e:
                sg.popup_error(f'Ошибка создания проекта: {e}',
                              background_color=COLORS['bg'],
                              text_color=COLORS['error'])
    
    def _edit_project(self):
        """Изменяет существующий проект"""
        if self.selected_row is None:
            sg.popup('Выберите проект для изменения',
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        existing_names = [p['name'] for p in self.projects]
        
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            mode='edit',
            project_data=project,
            existing_projects=existing_names
        )
        
        result = dialog.show()
        
        if result:
            try:
                original_name = result['original_name']
                new_name = result['name']
                new_script = result['script']
                
                original_folder = PROJECTS_DIR / original_name
                new_folder = PROJECTS_DIR / new_name
                
                # Если имя изменилось, переименовываем папку
                if original_name != new_name:
                    original_folder.rename(new_folder)
                
                # Удаляем старый .env файл
                old_env_files = list(new_folder.glob('*.env'))
                for old_env in old_env_files:
                    old_env.unlink()
                
                # Создаем новый .env файл
                env_filename = f"{self._sanitize_filename(new_name)}_{new_script}.env"
                env_path = new_folder / env_filename
                
                self._save_env_file(env_path, result['params'])
                
                # Обновляем список проектов
                self.scan_projects()
                
                # Находим и выбираем измененный проект
                for idx, project in enumerate(self.projects):
                    if project['name'] == new_name:
                        self.selected_row = idx
                        break
                
                self.update_table()
                
                self.log_output.print(f'✓ Проект "{new_name}" успешно изменен\n', 
                                     text_color=COLORS['success'], end='')
            
            except Exception as e:
                sg.popup_error(f'Ошибка изменения проекта: {e}',
                              background_color=COLORS['bg'],
                              text_color=COLORS['error'])
    
    def _copy_project(self):
        """Копирует существующий проект"""
        if self.selected_row is None:
            sg.popup('Выберите проект для копирования',
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        existing_names = [p['name'] for p in self.projects]
        
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            mode='copy',
            project_data=project,
            existing_projects=existing_names
        )
        
        result = dialog.show()
        
        if result:
            # Создаем папку проекта
            project_name = result['name']
            project_folder = PROJECTS_DIR / project_name
            
            try:
                project_folder.mkdir(parents=True, exist_ok=False)
                
                # Создаем .env файл
                env_filename = f"{self._sanitize_filename(project_name)}_{result['script']}.env"
                env_path = project_folder / env_filename
                
                self._save_env_file(env_path, result['params'])
                
                # Обновляем список проектов
                self.scan_projects()
                
                # Находим и выбираем новый проект
                for idx, project in enumerate(self.projects):
                    if project['name'] == project_name:
                        self.selected_row = idx
                        break
                
                self.update_table()
                
                self.log_output.print(f'✓ Проект "{project_name}" успешно скопирован\n', 
                                     text_color=COLORS['success'], end='')
            
            except Exception as e:
                sg.popup_error(f'Ошибка копирования проекта: {e}',
                              background_color=COLORS['bg'],
                              text_color=COLORS['error'])
    
    def _delete_project(self):
        """Удаляет проект"""
        if self.selected_row is None:
            sg.popup('Выберите проект для удаления',
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        project_name = project['name']
        
        # Подтверждение удаления
        response = sg.popup_yes_no(
            f'Вы уверены, что хотите удалить проект "{project_name}"?',
            title='Подтверждение удаления',
            background_color=COLORS['bg'],
            text_color=COLORS['warning']
        )
        
        if response == 'Yes':
            try:
                project_folder = PROJECTS_DIR / project_name
                
                # Удаляем папку проекта со всем содержимым
                shutil.rmtree(project_folder)
                
                # Обновляем список проектов
                self.scan_projects()
                self.selected_row = None
                self.update_table()
                
                self.log_output.print(f'✓ Проект "{project_name}" успешно удален\n', 
                                     text_color=COLORS['success'], end='')
            
            except Exception as e:
                sg.popup_error(f'Ошибка удаления проекта: {e}',
                              background_color=COLORS['bg'],
                              text_color=COLORS['error'])
    
    def _save_env_file(self, env_path, params):
        """
        Сохраняет параметры в .env файл
        
        Args:
            env_path: путь к .env файлу
            params: словарь параметров
        """
        with open(env_path, 'w', encoding='utf-8') as f:
            # Сначала ScriptName
            if 'ScriptName' in params:
                f.write(f'ScriptName={params["ScriptName"]}\n')
            
            # Затем остальные параметры в алфавитном порядке
            for key in sorted(params.keys()):
                if key != 'ScriptName':
                    value = params[key]
                    # Экранируем значения с пробелами
                    if ' ' in value:
                        value = f'"{value}"'
                    f.write(f'{key}={value}\n')
    
    def _sanitize_filename(self, name):
        """Заменяет пробелы на подчеркивания в имени файла"""
        return name.replace(' ', '_')
    
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

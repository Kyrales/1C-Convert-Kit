#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Главное окно GUI приложения
"""

from __future__ import annotations

import threading
import shutil
from pathlib import Path
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .project_scanner import ProjectDict

from .sg_import import sg
from ..core.convert import load_env_file
from .constants import VERSION, COLORS, SCRIPT_DIR, PROJECTS_DIR, PARAMS_DESC_FILE, PARAMS_DEPEND_FILE
from .project_scanner import ProjectScanner
from .project_editor import ProjectEditorDialog
from .conversion_runner import ConversionRunner


class CyberpunkGUI:
    """Главный класс графического интерфейса"""
    
    def __init__(self) -> None:
        self.projects: "list[ProjectDict]" = []
        self.selected_row: int | None = None
        self.runner: ConversionRunner | None = None
        self.conversion_thread: threading.Thread | None = None
        self.params_descriptions: dict[str, dict[str, str]] | None = self._load_params_descriptions()
        self.params_depend: dict[str, dict[str, list[str]]] | None = self._load_params_depend()
        self.debug_mode: bool = False  # Режим отладки
        
        # Настраиваем тему
        self._setup_theme()
        
        # Сканируем проекты
        self.scan_projects()
        
        # Создаем окно
        icon_path = SCRIPT_DIR / 'docs' / 'images' / 'icons8-cyberpunk-gradient-16.ico'
        self.window = sg.Window(  # type: ignore[attr-defined, assignment]
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
        self.table = self.window['-TABLE-']  # type: ignore[index]
        self.details_table = self.window['-DETAILS_TABLE-']  # type: ignore[index]
        self.log_output = self.window['-LOG-']  # type: ignore[index]
        
        # Проверяем, что элементы инициализированы
        assert self.table is not None, "Table element not found"
        assert self.details_table is not None, "Details table element not found"
        assert self.log_output is not None, "Log output element not found"
        
        # Обновляем таблицу
        self.update_table()
    
    def _load_params_descriptions(self) -> dict[str, dict[str, str]] | None:
        """Загружает описания параметров из JSON файла"""
        try:
            if PARAMS_DESC_FILE.exists():
                import json
                with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
                    data: dict[str, dict[str, str]] = json.load(f)
                    return data
        except Exception:
            pass
        return None
    
    def _load_params_depend(self) -> dict[str, dict[str, list[str]]] | None:
        """Загружает зависимости параметров из JSON файла"""
        try:
            if PARAMS_DEPEND_FILE.exists():
                import json
                with open(PARAMS_DEPEND_FILE, 'r', encoding='utf-8') as f:
                    data: dict[str, dict[str, list[str]]] = json.load(f)
                    return data
        except Exception:
            pass
        return None
    
    def _setup_theme(self) -> None:
        """Настройка Cyberpunk темы"""
        # Используем встроенную темную тему как основу
        _ = sg.theme('DarkBlack')  # type: ignore[attr-defined]
    
    def scan_projects(self) -> None:
        """Сканирует проекты"""
        self.projects = ProjectScanner.scan_projects()
    
    def create_layout(self) -> "list[list[object]]":
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
                headings=['', 'Параметр', 'Значение', 'Описание'],
                key='-DETAILS_TABLE-',
                enable_events=False,
                auto_size_columns=False,
                col_widths=[3, 27, 60, 110],
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
        
        return layout  # type: ignore[return-value]
    
    def update_table(self) -> None:
        """Обновляет данные в таблице"""
        table_data: list[list[str]] = []
        for idx, project in enumerate(self.projects):
            check = '✓' if project['selected'] else ''
            # Добавляем стрелку для текущей выбранной строки
            marker = '>' if idx == self.selected_row else ''
            name = f"{marker} {project['name']}" if marker else project['name']
            dst = project['custom_dst_path'] or project['dst_path']
            table_data.append([check, name, project['script'], dst])
        
        _ = self.table.update(values=table_data)  # type: ignore[attr-defined]
        
        # Обновляем таблицу деталей
        self.update_details_table()
    
    def _get_param_description(self, param_name: str, script_name: str) -> str:
        """
        Получает описание параметра из JSON
        
        Args:
            param_name: имя параметра (без источника в скобках)
            script_name: имя скрипта (например: conf2cf)
            
        Returns:
            str: описание параметра или пустая строка
        """
        if not self.params_descriptions:
            return ''
        
        # Сначала ищем в специфичных для скрипта (без .cmd)
        if script_name in self.params_descriptions:
            if param_name in self.params_descriptions[script_name]:
                return self.params_descriptions[script_name][param_name]
        
        # Пробуем с .cmd для обратной совместимости
        script_key_with_cmd = f"{script_name}.cmd"
        if script_key_with_cmd in self.params_descriptions:
            if param_name in self.params_descriptions[script_key_with_cmd]:
                return self.params_descriptions[script_key_with_cmd][param_name]
        
        # Затем ищем в общих
        if 'common' in self.params_descriptions:
            if param_name in self.params_descriptions['common']:
                return self.params_descriptions['common'][param_name]
        
        return ''
    
    def _get_param_category(self, param_name: str, script_name: str) -> str:
        """
        Определяет категорию параметра
        
        Args:
            param_name: имя параметра (может содержать суффикс с именем файла)
            script_name: имя скрипта (например: conf2cf)
        
        Returns:
            str: 'common' - общий параметр
                 'special' - специальный параметр проекта (не common)
                 'not_described' - параметр отсутствует в описании
        """
        if not self.params_descriptions:
            return 'not_described'
        
        # Убираем суффикс с именем файла, если есть (например, "V8_VERSION (base_1.env)" -> "V8_VERSION")
        clean_param_name = param_name.split(' (')[0].strip()
        
        # Проверяем в common
        if 'common' in self.params_descriptions:
            if clean_param_name in self.params_descriptions['common']:
                return 'common'
        
        # Проверяем в специфичных для скрипта
        if script_name in self.params_descriptions:
            if clean_param_name in self.params_descriptions[script_name]:
                return 'special'
        
        # Пробуем с .cmd для обратной совместимости
        script_key_with_cmd = f"{script_name}.cmd"
        if script_key_with_cmd in self.params_descriptions:
            if clean_param_name in self.params_descriptions[script_key_with_cmd]:
                return 'special'
        
        # Параметр не найден в описании
        return 'not_described'
    
    def update_details_table(self) -> None:
        """Обновляет таблицу деталей выбранного проекта с объединением базового .env"""
        if self.selected_row is None or self.selected_row >= len(self.projects):
            _ = self.details_table.update(values=[])  # type: ignore[attr-defined]
            return
        
        project = self.projects[self.selected_row]
        project_env_path: str = project['env_path']
        script_name: str = project.get('script', '')
        
        details_data: list[list[str]] = []
        
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
            
            # 1. ScriptName всегда первым
            if 'ScriptName' in project_params:
                param_name = 'ScriptName'
                value = project_params['ScriptName']
                # Проверяем переопределение
                if param_name in base_params and base_params[param_name] != value:
                    value = f"{value} (в {base_env_name} = {base_params[param_name]})"
                description = self._get_param_description(param_name, script_name)
                
                # Определяем маркер категории
                category = self._get_param_category(param_name, script_name)
                marker = self._get_category_marker(category)
                
                details_data.append([marker, param_name, value, description])
            
            # 2. Остальные параметры из проекта (кроме ScriptName)
            for param, value in sorted(project_params.items()):
                if param == 'ScriptName':
                    continue
                # Проверяем переопределение
                if param in base_params and base_params[param] != value:
                    value = f"{value} (в {base_env_name} = {base_params[param]})"
                description = self._get_param_description(param, script_name)
                
                # Определяем маркер категории
                category = self._get_param_category(param, script_name)
                marker = self._get_category_marker(category)
                
                details_data.append([marker, param, value, description])
            
            # 3. Параметры только из базового файла (не переопределенные)
            if base_env_name:
                for param, value in sorted(base_params.items()):
                    if param not in project_params:
                        param_with_source = f"{param} ({base_env_name})"
                        description = self._get_param_description(param, script_name)
                        
                        # Определяем маркер категории
                        category = self._get_param_category(param, script_name)
                        marker = self._get_category_marker(category)
                        
                        details_data.append([marker, param_with_source, value, description])
            
        except Exception as e:
            details_data.append(['', 'Ошибка', f'Не удалось прочитать файлы: {e}', ''])
        
        _ = self.details_table.update(values=details_data)  # type: ignore[attr-defined]
    
    def _get_category_marker(self, category: str) -> str:
        """
        Возвращает маркер для категории параметра
        
        Args:
            category: 'common', 'special' или 'not_described'
            
        Returns:
            str: 'S' для special, 'N' для not_described, '' для common
        """
        if category == 'special':
            # Используем цветной квадрат + S для визуального выделения
            return 'S'
        elif category == 'not_described':
            return 'N'
        else:  # common
            return ''
    
    def handle_events(self) -> None:
        """Обработка событий"""
        while True:
            event, values = self.window.read()  # type: ignore[attr-defined, misc, union-attr]
            
            if event == sg.WIN_CLOSED:  # type: ignore[attr-defined]
                break
            
            # F5 - Выполнить
            elif event == 'F5:116':  # F5 key code
                self._execute_conversion()
            
            # Чекбокс отладки
            elif event == '-DEBUG-':
                self.debug_mode = values['-DEBUG-']  # type: ignore[index]
                status = "включен" if self.debug_mode else "выключен"
                _ = self.log_output.print(f'ℹ Режим отладки {status}\n',  # type: ignore[attr-defined, union-attr]
                                     text_color=COLORS['primary'], 
                                     end='')
            
            # Выбор строки в таблице
            elif event == '-TABLE-':
                if values['-TABLE-']:  # type: ignore[index]
                    clicked_row = values['-TABLE-'][0]  # type: ignore[index]
                    # Переключаем чекбокс для кликнутой строки
                    self.projects[clicked_row]['selected'] = \
                        not self.projects[clicked_row]['selected']
                    # Обновляем выбранную строку
                    self.selected_row = clicked_row
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
                _ = self.log_output.print('✓ Проекты обновлены\n',  # type: ignore[attr-defined, union-attr]
                                     text_color=COLORS['success'], 
                                     end='')
            
            # Выполнить
            elif event == '-EXECUTE-':
                self._execute_conversion()
            
            # Очистить лог
            elif event == '-CLEAR_LOG-' or event == 'Очистить':
                _ = self.log_output.update(value='')  # type: ignore[attr-defined]
            
            # Сохранить лог
            elif event == '-SAVE_LOG-':
                self._save_log()
            
            # Копировать (из контекстного меню)
            elif event == 'Копировать':
                try:
                    # Получаем выделенный текст
                    selected_text = self.log_output.Widget.selection_get()  # type: ignore[attr-defined, union-attr]
                    if selected_text:
                        _ = self.window.TKroot.clipboard_clear()  # type: ignore[attr-defined, union-attr]
                        _ = self.window.TKroot.clipboard_append(selected_text)  # type: ignore[attr-defined, union-attr]
                except Exception:
                    # Если ничего не выделено, копируем весь текст
                    try:
                        all_text = self.log_output.get()  # type: ignore[attr-defined, union-attr]
                        if all_text:
                            _ = self.window.TKroot.clipboard_clear()  # type: ignore[attr-defined, union-attr]
                            _ = self.window.TKroot.clipboard_append(all_text)  # type: ignore[attr-defined, union-attr]
                    except Exception:
                        pass
            
            # Выделить все (из контекстного меню)
            elif event == 'Выделить все':
                try:
                    self.log_output.Widget.tag_add('sel', '1.0', 'end')  # type: ignore[attr-defined]
                except Exception:
                    pass
            
            # Обновление статуса
            elif event == '-UPDATE_STATUS-':
                completed, total, percent, status = values[event]  # type: ignore[misc]
                _ = self.window['-PROGRESS_TEXT-'].update(  # type: ignore[index, attr-defined]
                    value=f'Выполнено: {completed} из {total} проектов ({percent}%)')
                _ = self.window['-PROGRESS_BAR-'].update(current_count=percent)  # type: ignore[index, attr-defined]
                # Цветной вывод статуса
                _ = self.log_output.print(f'ℹ {status}\n', text_color=COLORS['primary'], end='')  # type: ignore[attr-defined, union-attr]
            
            # Завершение конвертации
            elif event == '-CONVERSION_DONE-':
                completed, total, percent, total_duration_str = values[event]  # type: ignore[misc]
                _ = self.window['-PROGRESS_TEXT-'].update(  # type: ignore[index, attr-defined]
                    value=f'Готово! Выполнено: {completed} из {total} ({percent}%). Общее время: {total_duration_str}')
                _ = self.window['-PROGRESS_BAR-'].update(current_count=100)  # type: ignore[index, attr-defined]
            
            # Лог с цветом
            elif event == '-LOG-':
                log_data = values[event]  # type: ignore[index]
                if isinstance(log_data, dict):
                    # Новый формат с цветом
                    _ = self.log_output.print(log_data['text'],  # type: ignore[attr-defined, union-attr, index]
                                         text_color=log_data['color'],  # type: ignore[index]
                                         end='')
                else:
                    # Старый формат (обратная совместимость)
                    _ = self.log_output.update(value=log_data, append=True)  # type: ignore[attr-defined]
        
        # Останавливаем конвертацию если запущена
        if self.runner:
            self.runner.stop()
        
        _ = self.window.close()  # type: ignore[attr-defined]
    
    def _move_row(self, direction: int) -> None:
        """Перемещает выбранную строку вверх или вниз"""
        if self.selected_row is None:
            _ = sg.popup('Выберите проект в таблице',  # type: ignore[attr-defined]
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        new_idx = self.selected_row + direction
        
        if 0 <= new_idx < len(self.projects):
            # Меняем местами
            self.projects[self.selected_row], self.projects[new_idx] = \
                self.projects[new_idx], self.projects[self.selected_row]
            
            self.selected_row = new_idx
            self.update_table()
    
    def _change_path(self) -> None:
        """Изменяет путь выгрузки для выбранного проекта"""
        if self.selected_row is None:
            _ = sg.popup('Выберите проект в таблице',  # type: ignore[attr-defined]
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        
        # Определяем тип скрипта
        script_lower = project['script'].lower()
        
        if '2cf' in script_lower or '2cfe' in script_lower:
            # Выбор файла
            new_path = sg.popup_get_file(  # type: ignore[attr-defined]
                'Выберите файл для сохранения',
                save_as=True,
                file_types=(('CF Files', '*.cf'), ('CFE Files', '*.cfe'), ('All Files', '*.*')),
                background_color=COLORS['bg'],
                text_color=COLORS['text']
            )
        else:
            # Выбор папки
            new_path = sg.popup_get_folder(  # type: ignore[attr-defined]
                'Выберите папку для сохранения',
                background_color=COLORS['bg'],
                text_color=COLORS['text']
            )
        
        if new_path:
            project['custom_dst_path'] = new_path
            self.update_table()
            _ = self.log_output.print(f'ℹ Путь выгрузки изменен для проекта "{project["name"]}"\n',  # type: ignore[attr-defined, union-attr]
                                 text_color=COLORS['primary'], end='')
    
    def _execute_conversion(self) -> None:
        """Запускает конвертацию выбранных проектов"""
        # Получаем выбранные проекты
        selected = [p for p in self.projects if p['selected']]
        
        if not selected:
            _ = sg.popup('Выберите хотя бы один проект',  # type: ignore[attr-defined]
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        # Переключаемся на вкладку лога
        _ = self.window['-TABS-'].Widget.select(1)  # type: ignore[index, attr-defined, union-attr]
        
        # Очищаем лог
        _ = self.log_output.update(value='')  # type: ignore[attr-defined]
        
        # Сбрасываем прогресс
        _ = self.window['-PROGRESS_BAR-'].update(current_count=0)  # type: ignore[index, attr-defined]
        _ = self.window['-PROGRESS_TEXT-'].update(value='Запуск конвертации...')  # type: ignore[index, attr-defined]
        
        # Запускаем в отдельном потоке
        self.runner = ConversionRunner(self.window)
        self.conversion_thread = threading.Thread(
            target=self.runner.run_conversions,
            args=(selected,),
            daemon=True
        )
        self.conversion_thread.start()
    
    def _create_project_pipeline(
        self,
        project_name: str,
        script_name: str,
        params: dict[str, str],
        success_message: str
    ) -> bool:
        """
        Общий pipeline создания проекта.
        
        Args:
            project_name: Имя проекта
            script_name: Тип скрипта (ScriptName)
            params: Параметры для .env файла
            success_message: Сообщение об успехе
        
        Returns:
            True если успешно, False при ошибке
        """
        project_folder = PROJECTS_DIR / project_name
        
        try:
            # 1. Создать папку проекта
            project_folder.mkdir(parents=True, exist_ok=False)
            
            # 2. Создать .env файл
            env_filename = f"{self._sanitize_filename(project_name)}_{script_name}.env"
            env_path = project_folder / env_filename
            self._save_env_file(env_path, params)  # type: ignore[arg-type]
            
            # 3. Пересканировать проекты
            self.scan_projects()
            
            # 4. Выбрать новый проект в таблице
            for idx, project in enumerate(self.projects):
                if project['name'] == project_name:
                    self.selected_row = idx
                    break
            
            # 5. Обновить таблицу
            self.update_table()
            
            # 6. Показать сообщение об успехе
            _ = self.log_output.print(f'✓ {success_message}\n',  # type: ignore[attr-defined, union-attr]
                                 text_color=COLORS['success'], end='')
            
            return True
            
        except Exception as e:
            _ = sg.popup_error(f'Ошибка создания проекта: {e}',  # type: ignore[attr-defined]
                          background_color=COLORS['bg'],
                          text_color=COLORS['error'])
            return False
    
    def _add_project(self) -> None:
        """Добавляет новый проект"""
        existing_names = [p['name'] for p in self.projects]
        
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            params_depend=self.params_depend,
            mode='add',
            existing_projects=existing_names
        )
        
        result = dialog.show()
        
        if result:
            project_name = str(result['name'])
            script_name = str(result['script'])
            params = result['params']
            
            if isinstance(params, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in params.items()):
                self._create_project_pipeline(
                    project_name=project_name,
                    script_name=script_name,
                    params=params,  # type: ignore[arg-type]
                    success_message=f'Проект "{project_name}" успешно создан'
                )
    
    def _edit_project(self) -> None:
        """Изменяет существующий проект"""
        if self.selected_row is None:
            _ = sg.popup('Выберите проект для изменения',  # type: ignore[attr-defined]
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        existing_names = [p['name'] for p in self.projects]
        
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            params_depend=self.params_depend,
            mode='edit',
            project_data=project,  # type: ignore[arg-type]
            existing_projects=existing_names
        )
        
        result = dialog.show()
        
        if result:
            try:
                original_name = str(result.get('original_name', ''))
                new_name = str(result['name'])
                new_script = str(result['script'])
                
                original_folder = PROJECTS_DIR / original_name
                new_folder = PROJECTS_DIR / new_name
                
                # Если имя изменилось, переименовываем папку
                if original_name != new_name:
                    _ = original_folder.rename(new_folder)
                
                # Удаляем старый .env файл
                old_env_files = list(new_folder.glob('*.env'))
                for old_env in old_env_files:
                    old_env.unlink()
                
                # Создаем новый .env файл
                env_filename = f"{self._sanitize_filename(new_name)}_{new_script}.env"
                env_path = new_folder / env_filename
                
                params = result['params']
                if isinstance(params, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in params.items()):
                    # Type narrowing: params is dict[str, str]
                    self._save_env_file(env_path, params)  # type: ignore[arg-type]
                
                # Обновляем список проектов
                self.scan_projects()
                
                # Находим и выбираем измененный проект
                for idx, project in enumerate(self.projects):
                    if project['name'] == new_name:
                        self.selected_row = idx
                        break
                
                self.update_table()
                
                _ = self.log_output.print(f'✓ Проект "{new_name}" успешно изменен\n',  # type: ignore[attr-defined, union-attr]
                                     text_color=COLORS['success'], end='')
            
            except Exception as e:
                _ = sg.popup_error(f'Ошибка изменения проекта: {e}',  # type: ignore[attr-defined]
                              background_color=COLORS['bg'],
                              text_color=COLORS['error'])
    
    def _copy_project(self) -> None:
        """Копирует существующий проект"""
        if self.selected_row is None:
            _ = sg.popup('Выберите проект для копирования',  # type: ignore[attr-defined]
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        existing_names = [p['name'] for p in self.projects]
        
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            params_depend=self.params_depend,
            mode='copy',
            project_data=project,  # type: ignore[arg-type]
            existing_projects=existing_names
        )
        
        result = dialog.show()
        
        if result:
            project_name = str(result['name'])
            script_name = str(result['script'])
            params = result['params']
            
            if isinstance(params, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in params.items()):
                self._create_project_pipeline(
                    project_name=project_name,
                    script_name=script_name,
                    params=params,  # type: ignore[arg-type]
                    success_message=f'Проект "{project_name}" успешно скопирован'
                )
    
    def _delete_project(self) -> None:
        """Удаляет проект"""
        if self.selected_row is None:
            _ = sg.popup('Выберите проект для удаления',  # type: ignore[attr-defined]
                    background_color=COLORS['bg'],
                    text_color=COLORS['warning'])
            return
        
        project = self.projects[self.selected_row]
        project_name = project['name']
        
        # Подтверждение удаления
        response = sg.popup_yes_no(  # type: ignore[attr-defined]
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
                
                _ = self.log_output.print(f'✓ Проект "{project_name}" успешно удален\n',  # type: ignore[attr-defined, union-attr]
                                     text_color=COLORS['success'], end='')
            
            except Exception as e:
                _ = sg.popup_error(f'Ошибка удаления проекта: {e}',  # type: ignore[attr-defined]
                              background_color=COLORS['bg'],
                              text_color=COLORS['error'])
    
    def _save_env_file(self, env_path: Path, params: "dict[str, str]") -> None:
        """
        Сохраняет параметры в .env файл
        
        Args:
            env_path: путь к .env файлу
            params: словарь параметров
        """
        with open(env_path, 'w', encoding='utf-8') as f:
            # Сначала ScriptName
            if 'ScriptName' in params:
                _ = f.write(f'ScriptName={params["ScriptName"]}\n')
            
            # Затем остальные параметры в алфавитном порядке
            for key in sorted(params.keys()):
                if key != 'ScriptName':
                    value = params[key]
                    # Экранируем значения с пробелами
                    if ' ' in value:
                        value = f'"{value}"'
                    _ = f.write(f'{key}={value}\n')
    
    def _sanitize_filename(self, name: str) -> str:
        """Заменяет пробелы на подчеркивания в имени файла"""
        return name.replace(' ', '_')
    
    def _save_log(self) -> None:
        """Сохраняет лог в файл"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f'converter_log_{timestamp}.log'
        # Путь к папке logs (не создаем пока)
        logs_dir = SCRIPT_DIR / 'logs'
        # Полный путь с каталогом logs
        default_path = str(logs_dir / default_name)
        
        file_path = sg.popup_get_file(  # type: ignore[attr-defined]
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
                from pathlib import Path as PathType
                file_dir = PathType(file_path).parent
                file_dir.mkdir(parents=True, exist_ok=True)
                
                # Сохраняем в UTF-8 для корректного отображения
                with open(file_path, 'w', encoding='utf-8') as f:
                    _ = f.write(self.log_output.get())  # type: ignore[attr-defined]
                _ = sg.popup(f'Лог сохранен: {file_path}',  # type: ignore[attr-defined]
                        background_color=COLORS['bg'],
                        text_color=COLORS['success'])
            except Exception as e:
                _ = sg.popup(f'Ошибка сохранения: {e}',  # type: ignore[attr-defined]
                        background_color=COLORS['bg'],
                        text_color=COLORS['error'])

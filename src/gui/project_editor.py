#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Диалог редактирования проекта
"""

try:
    import FreeSimpleGUI as sg
except ImportError:
    import PySimpleGUI as sg

from ..core.convert import load_env_file
from .constants import COLORS, PROJECTS_DIR


class ProjectEditorDialog:
    """Диалог добавления/изменения/копирования проекта"""
    
    def __init__(self, params_descriptions, mode='add', project_data=None, existing_projects=None):
        """
        Args:
            params_descriptions: словарь с описаниями параметров из JSON
            mode: режим работы ('add', 'edit', 'copy')
            project_data: данные проекта для режимов 'edit' и 'copy'
            existing_projects: список существующих проектов для проверки дубликатов
        """
        self.params_descriptions = params_descriptions
        self.mode = mode
        self.project_data = project_data or {}
        self.existing_projects = existing_projects or []
        self.result = None
        self.window = None
        
        # Получаем список доступных скриптов
        self.available_scripts = self._get_available_scripts()
        
        # Загружаем базовый .env если есть
        self.base_env_params = self._load_base_env()
    
    def _get_available_scripts(self):
        """Получает список доступных скриптов из params_descriptions"""
        if not self.params_descriptions:
            return []
        
        scripts = []
        for key in self.params_descriptions.keys():
            if key != 'common':
                scripts.append(key)
        
        return sorted(scripts)
    
    def _load_base_env(self):
        """Загружает параметры из базового .env файла"""
        base_env_files = [f for f in PROJECTS_DIR.glob('*.env') if f.is_file()]
        if base_env_files:
            base_env_path = base_env_files[0]
            try:
                return load_env_file(str(base_env_path), silent=True) or {}
            except:
                pass
        return {}
    
    def _get_script_params(self, script_name):
        """
        Получает список параметров для скрипта
        
        Returns:
            dict: {param_name: {'description': str, 'required': bool, 'type': str}}
        """
        if not self.params_descriptions:
            return {}
        
        params = {}
        
        # Добавляем общие параметры
        if 'common' in self.params_descriptions:
            for param, desc in self.params_descriptions['common'].items():
                if param != 'ScriptName':
                    params[param] = {
                        'description': desc,
                        'required': False,
                        'type': self._detect_param_type(param, desc)
                    }
        
        # Добавляем специфичные для скрипта параметры
        if script_name in self.params_descriptions:
            for param, desc in self.params_descriptions[script_name].items():
                params[param] = {
                    'description': desc,
                    'required': param in ['V8_SRC_PATH', 'V8_DST_PATH', 'V8_EXT_NAME'],
                    'type': self._detect_param_type(param, desc)
                }
        
        return params
    
    def _detect_param_type(self, param_name, description):
        """
        Определяет тип параметра
        
        Returns:
            str: 'path_file', 'path_folder', 'boolean', 'text'
        """
        desc_lower = description.lower()
        
        # Булевы параметры (0 или 1)
        if 'установлена в 1' in desc_lower or 'если установлена' in desc_lower:
            return 'boolean'
        
        # Пути к файлам
        if param_name.endswith('_TOOL') or 'файл' in desc_lower:
            if 'каталог' not in desc_lower and 'папк' not in desc_lower:
                return 'path_file'
        
        # Пути к папкам
        if 'каталог' in desc_lower or 'папк' in desc_lower or param_name.endswith('_PATH'):
            # Исключения - это файлы
            if '.cf' in desc_lower or '.cfe' in desc_lower or '.epf' in desc_lower or '.erf' in desc_lower:
                return 'path_file'
            return 'path_folder'
        
        return 'text'
    
    def _validate_project_name(self, name):
        """
        Валидирует имя проекта
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Наименование не может быть пустым"
        
        # Проверка на недопустимые символы
        invalid_chars = r'/\:*?"<>|'
        for char in invalid_chars:
            if char in name:
                return False, f"Наименование содержит недопустимый символ: {char}"
        
        # Проверка на дубликаты (только для режимов add и copy, или при изменении имени)
        if self.mode in ['add', 'copy']:
            if name in self.existing_projects:
                return False, f"Проект с именем '{name}' уже существует"
        elif self.mode == 'edit':
            original_name = self.project_data.get('name', '')
            if name != original_name and name in self.existing_projects:
                return False, f"Проект с именем '{name}' уже существует"
        
        return True, ""
    
    def _sanitize_filename(self, name):
        """Заменяет пробелы на подчеркивания в имени файла"""
        return name.replace(' ', '_')
    
    def _create_layout(self, script_name=None):
        """Создает layout диалога"""
        # Заголовок окна
        if self.mode == 'add':
            title = 'Добавить проект'
        elif self.mode == 'edit':
            title = 'Изменить проект'
        else:  # copy
            title = 'Копировать проект'
        
        # Получаем данные проекта
        current_name = self.project_data.get('name', '')
        current_script = script_name or self.project_data.get('script', self.available_scripts[0] if self.available_scripts else '')
        
        # Загружаем параметры проекта из .env если режим edit или copy
        project_params = {}
        if self.mode in ['edit', 'copy'] and 'env_path' in self.project_data:
            try:
                project_params = load_env_file(self.project_data['env_path'], silent=True) or {}
            except:
                pass
        
        # Получаем параметры для выбранного скрипта
        script_params = self._get_script_params(current_script)
        
        # Сортируем параметры: обязательные, включенные, выключенные
        required_params = []
        enabled_params = []
        disabled_params = []
        
        for param, info in script_params.items():
            param_enabled = param in project_params
            
            if info['required']:
                required_params.append((param, info, param_enabled))
            elif param_enabled:
                enabled_params.append((param, info, param_enabled))
            else:
                disabled_params.append((param, info, param_enabled))
        
        # Сортируем внутри групп по имени
        required_params.sort(key=lambda x: x[0])
        enabled_params.sort(key=lambda x: x[0])
        disabled_params.sort(key=lambda x: x[0])
        
        all_params = required_params + enabled_params + disabled_params
        
        # Layout
        layout = []
        
        # Контекстное меню для поддержки Ctrl+C/V/X/A
        right_click_menu = ['', ['Копировать', 'Вставить', 'Вырезать', 'Выделить все', '---', 'Отменить']]
        
        # Обязательные поля
        layout.append([
            sg.Text('Наименование:', size=(20, 1), text_color=COLORS['text'], background_color=COLORS['bg']),
            sg.Input(current_name, key='-NAME-', size=(60, 1), 
                    background_color=COLORS['bg_secondary'], text_color=COLORS['text'],
                    right_click_menu=right_click_menu)
        ])
        
        layout.append([
            sg.Text('Скрипт:', size=(20, 1), text_color=COLORS['text'], background_color=COLORS['bg']),
            sg.Combo(self.available_scripts, default_value=current_script, key='-SCRIPT-', 
                    size=(58, 1), readonly=True, enable_events=True,
                    background_color=COLORS['bg_secondary'], text_color=COLORS['text'])
        ])
        
        layout.append([sg.HorizontalSeparator(color=COLORS['primary'])])
        
        # Заголовок для параметров
        layout.append([
            sg.Text('Параметры проекта:', text_color=COLORS['primary'], 
                   background_color=COLORS['bg'], font=('Consolas', 10, 'bold'))
        ])
        
        # Создаем колонку с прокруткой для параметров
        params_column = []
        
        for param, info, is_enabled in all_params:
            param_value = project_params.get(param, '')
            is_required = info['required']
            param_type = info['type']
            
            # Получаем значение из базового .env для информации
            base_value = self.base_env_params.get(param, '')
            
            # Определяем отображаемое значение:
            # - Если чекбокс включен или обязательный параметр - показываем значение из проекта
            # - Если чекбокс выключен и есть значение в base_env - показываем его с пометкой
            if is_enabled or is_required:
                display_value = param_value
            else:
                display_value = f"{base_value} (base_1.env)" if base_value else ''
            
            # Чекбокс (для обязательных - disabled)
            checkbox = sg.Checkbox('', key=f'-CHK_{param}-', default=is_enabled or is_required,
                                  disabled=is_required, enable_events=True,
                                  background_color=COLORS['bg'])
            
            # Метка параметра (без tooltip, будет кнопка ?)
            label = sg.Text(f'{param}:', size=(25, 1), text_color=COLORS['text'], 
                          background_color=COLORS['bg'])
            
            # Поле ввода в зависимости от типа
            # Цвет фона для disabled полей - темнее
            disabled_bg = COLORS['bg']  # Темный фон для недоступных полей
            enabled_bg = COLORS['bg_secondary']  # Светлее для доступных
            
            # Цвет текста для информационных значений из base_env
            text_color = COLORS['text'] if (is_enabled or is_required) else COLORS['text_dim']
            
            # Контекстное меню для поддержки Ctrl+C/V/X/A
            right_click_menu = ['', ['Копировать', 'Вставить', 'Вырезать', 'Выделить все', '---', 'Отменить']]
            
            if param_type == 'boolean':
                input_field = sg.Combo(['0', '1'], default_value=display_value or '0', 
                                      key=f'-VAL_{param}-', size=(45, 1), readonly=True,
                                      background_color=enabled_bg if (is_enabled or is_required) else disabled_bg,
                                      text_color=text_color,
                                      disabled=not (is_enabled or is_required),
                                      metadata={'base_value': base_value})
            else:
                input_field = sg.Input(display_value, key=f'-VAL_{param}-', size=(45, 1),
                                      background_color=enabled_bg if (is_enabled or is_required) else disabled_bg,
                                      text_color=text_color,
                                      disabled=not (is_enabled or is_required),
                                      enable_events=False,
                                      right_click_menu=right_click_menu,
                                      metadata={'base_value': base_value})
            
            # Кнопка помощи "?" с описанием параметра
            help_btn = sg.Button('?', key=f'-HELP_{param}-', size=(2, 1),
                                button_color=(COLORS['primary'], COLORS['bg']),
                                tooltip='Показать описание параметра')
            
            # Кнопка выбора для путей
            if param_type in ['path_file', 'path_folder']:
                browse_btn = sg.Button('...', key=f'-BROWSE_{param}-', size=(3, 1),
                                      button_color=(COLORS['text'], COLORS['bg_secondary']),
                                      disabled=not (is_enabled or is_required),
                                      metadata={'type': param_type})  # Сохраняем тип для обработки
                params_column.append([checkbox, label, input_field, help_btn, browse_btn])
            else:
                params_column.append([checkbox, label, input_field, help_btn])
        
        # Добавляем колонку с прокруткой
        layout.append([
            sg.Column(params_column, size=(900, 400), scrollable=True, vertical_scroll_only=True,
                     background_color=COLORS['bg'], key='-PARAMS_COLUMN-')
        ])
        
        layout.append([sg.HorizontalSeparator(color=COLORS['primary'])])
        
        # Таблица базового .env
        if self.base_env_params:
            layout.append([
                sg.Text('Базовый .env (только для просмотра):', text_color=COLORS['accent'], 
                       background_color=COLORS['bg'], font=('Consolas', 10, 'bold'))
            ])
            
            base_env_data = []
            for param, value in sorted(self.base_env_params.items()):
                description = self._get_param_description(param, current_script)
                base_env_data.append([param, value, description])
            
            layout.append([
                sg.Table(base_env_data, headings=['Параметр', 'Значение', 'Описание'],
                        auto_size_columns=False, col_widths=[25, 40, 60],
                        num_rows=10, font=('Consolas', 9),
                        background_color=COLORS['bg_secondary'], text_color=COLORS['text_dim'],
                        alternating_row_color=COLORS['bg'],
                        header_background_color=COLORS['bg'],
                        header_text_color=COLORS['accent'],
                        justification='left')
            ])
        
        layout.append([sg.HorizontalSeparator(color=COLORS['primary'])])
        
        # Кнопки
        layout.append([
            sg.Button('Сохранить', key='-SAVE-', size=(15, 1),
                     button_color=(COLORS['bg'], COLORS['success']),
                     font=('Arial', 11, 'bold')),
            sg.Button('Отменить', key='-CANCEL-', size=(15, 1),
                     button_color=(COLORS['bg'], COLORS['error']),
                     font=('Arial', 11, 'bold'))
        ])
        
        return layout, title
    
    def _get_param_description(self, param_name, script_name):
        """Получает описание параметра"""
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
    
    def _update_params_visibility(self, window, script_name):
        """Обновляет видимость и доступность полей при смене скрипта"""
        script_params = self._get_script_params(script_name)
        
        # Проходим по всем параметрам и обновляем их состояние
        for param, info in script_params.items():
            checkbox_key = f'-CHK_{param}-'
            value_key = f'-VAL_{param}-'
            browse_key = f'-BROWSE_{param}-'
            
            if checkbox_key in window.AllKeysDict:
                is_checked = window[checkbox_key].get()
                is_required = info['required']
                is_enabled = is_checked or is_required
                
                # Определяем цвет фона
                new_bg = COLORS['bg_secondary'] if is_enabled else COLORS['bg']
                
                # Обновляем доступность поля ввода и цвет фона
                window[value_key].update(disabled=not is_enabled, background_color=new_bg)
                
                # Обновляем доступность кнопки browse если есть
                if browse_key in window.AllKeysDict:
                    window[browse_key].update(disabled=not is_enabled)
    
    def show(self):
        """Показывает диалог и возвращает результат"""
        # Используем цикл для пересоздания окна при смене скрипта
        current_script = None
        saved_values = None
        
        try:
            while True:
                result = self._show_window(script_name=current_script, saved_values=saved_values)
                
                # Если результат - это запрос на смену скрипта
                if isinstance(result, dict) and result.get('_action') == 'change_script':
                    current_script = result.get('script')
                    saved_values = result.get('values')
                    continue
                
                # Иначе возвращаем результат (None или данные проекта)
                return result
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            sg.popup_error(f"Критическая ошибка в диалоге:\n{e}\n\nПодробности в консоли",
                          background_color=COLORS['bg'],
                          text_color=COLORS['error'])
            return None
    
    def _show_window(self, script_name=None, saved_values=None):
        """Внутренний метод для показа окна"""
        layout, title = self._create_layout(script_name=script_name)
        
        icon_path = PROJECTS_DIR.parent / 'docs' / 'images' / 'icons8-cyberpunk-gradient-16.ico'
        self.window = sg.Window(
            title,
            layout,
            size=(950, 800),
            finalize=True,
            modal=True,
            background_color=COLORS['bg'],
            resizable=False,
            icon=str(icon_path) if icon_path.exists() else None
        )
        
        # Включаем undo/redo для всех полей Input (включая Наименование)
        for key in self.window.AllKeysDict:
            if isinstance(key, str) and (key.startswith('-VAL_') or key == '-NAME-'):
                element = self.window[key]
                if hasattr(element, 'Widget') and hasattr(element.Widget, 'configure'):
                    try:
                        # Включаем undo для Entry виджетов
                        element.Widget.configure(undo=True, maxundo=-1)
                    except:
                        pass
        
        # Восстанавливаем сохраненные значения если есть
        if saved_values:
            if 'name' in saved_values:
                self.window['-NAME-'].update(saved_values['name'])
            if 'params' in saved_values:
                for param, value in saved_values['params'].items():
                    value_key = f'-VAL_{param}-'
                    if value_key in self.window.AllKeysDict:
                        self.window[value_key].update(value)
        
        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, '-CANCEL-'):
                self.window.close()
                return None
            
            # Изменение скрипта - возвращаем специальный результат для пересоздания окна
            elif event == '-SCRIPT-':
                try:
                    new_script = values['-SCRIPT-']
                    
                    # Сохраняем текущие значения полей
                    current_values = {
                        'name': values['-NAME-'],
                        'params': {}
                    }
                    for key, value in values.items():
                        # ВАЖНО: Проверяем, что key - это строка, а не число
                        if isinstance(key, str) and key.startswith('-VAL_'):
                            param_name = key[5:]  # Убираем '-VAL_'
                            if value and not value.endswith('(base_1.env)'):
                                current_values['params'][param_name] = value
                    
                    # Обновляем project_data с новым скриптом
                    self.project_data['script'] = new_script
                    
                    # Закрываем текущее окно
                    self.window.close()
                    
                    # Возвращаем специальный результат для пересоздания окна
                    return {
                        '_action': 'change_script',
                        'script': new_script,
                        'values': current_values
                    }
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    sg.popup_error(f"Ошибка при смене скрипта:\n{e}\n\nПодробности в консоли",
                                  background_color=COLORS['bg'],
                                  text_color=COLORS['error'])
                    # Не закрываем окно, продолжаем работу
                    continue
            
            # Изменение чекбокса - обновляем доступность поля и цвет фона
            elif event.startswith('-CHK_'):
                param_name = event[5:-1]  # Убираем '-CHK_' и '-'
                is_checked = values[event]
                
                value_key = f'-VAL_{param_name}-'
                browse_key = f'-BROWSE_{param_name}-'
                
                # Получаем значение из базового .env
                base_value = self.base_env_params.get(param_name, '')
                
                # Обновляем цвет фона и текста в зависимости от состояния
                new_bg = COLORS['bg_secondary'] if is_checked else COLORS['bg']
                new_text_color = COLORS['text'] if is_checked else COLORS['text_dim']
                
                # Обновляем значение поля:
                # - Если включаем чекбокс - очищаем поле (пользователь будет вводить свое значение)
                # - Если выключаем чекбокс - показываем значение из base_env с пометкой
                if is_checked:
                    # Включили чекбокс - очищаем поле
                    new_value = ''
                else:
                    # Выключили чекбокс - показываем информационное значение из base_env
                    new_value = f"{base_value} (base_1.env)" if base_value else ''
                
                self.window[value_key].update(value=new_value, disabled=not is_checked, 
                                             background_color=new_bg, text_color=new_text_color)
                if browse_key in self.window.AllKeysDict:
                    self.window[browse_key].update(disabled=not is_checked)
            
            # Кнопка помощи "?" - показываем описание параметра
            elif event.startswith('-HELP_'):
                param_name = event[6:-1]  # Убираем '-HELP_' и '-'
                script_name = values['-SCRIPT-']
                description = self._get_param_description(param_name, script_name)
                
                if description:
                    sg.popup(f'Параметр: {param_name}\n\n{description}',
                            title='Описание параметра',
                            background_color=COLORS['bg'],
                            text_color=COLORS['text'],
                            button_color=(COLORS['bg'], COLORS['primary']))
                else:
                    sg.popup(f'Параметр: {param_name}\n\nОписание отсутствует',
                            title='Описание параметра',
                            background_color=COLORS['bg'],
                            text_color=COLORS['text_dim'],
                            button_color=(COLORS['bg'], COLORS['primary']))
            
            # Кнопка выбора пути
            elif event.startswith('-BROWSE_'):
                param_name = event[8:-1]  # Убираем '-BROWSE_' и '-'
                value_key = f'-VAL_{param_name}-'
                
                # Получаем текущее значение для initial_folder
                current_value = values[value_key]
                initial_folder = None
                
                if current_value:
                    from pathlib import Path
                    current_path = Path(current_value)
                    if current_path.exists():
                        if current_path.is_file():
                            initial_folder = str(current_path.parent)
                        else:
                            initial_folder = str(current_path)
                    else:
                        # Если путь не существует, берем родительскую папку
                        initial_folder = str(current_path.parent)
                
                # Определяем тип параметра
                script_name = values['-SCRIPT-']
                script_params = self._get_script_params(script_name)
                param_type = script_params.get(param_name, {}).get('type', 'text')
                
                # Открываем диалог выбора
                if param_type == 'path_folder':
                    path = sg.popup_get_folder(
                        'Выберите папку',
                        default_path=initial_folder or '',
                        background_color=COLORS['bg'],
                        text_color=COLORS['text']
                    )
                else:  # path_file
                    path = sg.popup_get_file(
                        'Выберите файл',
                        default_path=current_value or initial_folder or '',
                        background_color=COLORS['bg'],
                        text_color=COLORS['text']
                    )
                
                if path:
                    self.window[value_key].update(path)
            
            # Обработка контекстного меню (правый клик)
            elif event == 'Копировать':
                # Находим активный элемент
                focused_element = self.window.find_element_with_focus()
                if focused_element and hasattr(focused_element, 'Widget'):
                    try:
                        # Получаем выделенный текст
                        selected_text = focused_element.Widget.selection_get()
                        if selected_text:
                            self.window.TKroot.clipboard_clear()
                            self.window.TKroot.clipboard_append(selected_text)
                    except:
                        pass
            
            elif event == 'Вставить':
                # Находим активный элемент
                focused_element = self.window.find_element_with_focus()
                if focused_element and hasattr(focused_element, 'Widget'):
                    try:
                        # Получаем текст из буфера обмена
                        clipboard_text = self.window.TKroot.clipboard_get()
                        if clipboard_text:
                            # Вставляем в позицию курсора
                            focused_element.Widget.insert('insert', clipboard_text)
                    except:
                        pass
            
            elif event == 'Вырезать':
                # Находим активный элемент
                focused_element = self.window.find_element_with_focus()
                if focused_element and hasattr(focused_element, 'Widget'):
                    try:
                        # Получаем выделенный текст
                        selected_text = focused_element.Widget.selection_get()
                        if selected_text:
                            self.window.TKroot.clipboard_clear()
                            self.window.TKroot.clipboard_append(selected_text)
                            # Удаляем выделенный текст
                            focused_element.Widget.delete('sel.first', 'sel.last')
                    except:
                        pass
            
            elif event == 'Выделить все':
                # Находим активный элемент
                focused_element = self.window.find_element_with_focus()
                if focused_element and hasattr(focused_element, 'Widget'):
                    try:
                        # Выделяем весь текст
                        focused_element.Widget.select_range(0, 'end')
                        focused_element.Widget.icursor('end')
                    except:
                        pass
            
            elif event == 'Отменить':
                # Находим активный элемент
                focused_element = self.window.find_element_with_focus()
                if focused_element and hasattr(focused_element, 'Widget'):
                    try:
                        # Отменяем последнее действие
                        focused_element.Widget.edit_undo()
                    except:
                        pass
            
            # Сохранение
            elif event == '-SAVE-':
                # Валидация имени
                project_name = values['-NAME-'].strip()
                is_valid, error_msg = self._validate_project_name(project_name)
                
                if not is_valid:
                    sg.popup_error(error_msg, background_color=COLORS['bg'], 
                                  text_color=COLORS['error'])
                    continue
                
                # Собираем параметры
                script_name = values['-SCRIPT-']
                params = {'ScriptName': script_name}
                
                script_params = self._get_script_params(script_name)
                for param in script_params.keys():
                    checkbox_key = f'-CHK_{param}-'
                    value_key = f'-VAL_{param}-'
                    
                    if checkbox_key in values and values[checkbox_key]:
                        param_value = values[value_key]
                        # Сохраняем только непустые значения и не информационные (без пометки base_1.env)
                        if param_value and not param_value.endswith('(base_1.env)'):
                            params[param] = param_value
                
                # Проверяем обязательные поля
                missing_required = []
                for param, info in script_params.items():
                    if info['required'] and param not in params:
                        missing_required.append(param)
                
                if missing_required:
                    sg.popup_error(f"Не заполнены обязательные поля:\n" + "\n".join(missing_required),
                                  background_color=COLORS['bg'], text_color=COLORS['error'])
                    continue
                
                # Формируем результат
                result = {
                    'name': project_name,
                    'script': script_name,
                    'params': params,
                    'original_name': self.project_data.get('name', '') if self.mode == 'edit' else None
                }
                
                # Закрываем окно и возвращаем результат
                self.window.close()
                return result

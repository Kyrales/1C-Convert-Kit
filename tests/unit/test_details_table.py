#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест для проверки корректности отображения таблицы деталей проекта
"""

import sys
import json
from pathlib import Path

# Добавляем путь к src для импорта (файл находится в tests/unit/)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.convert import load_env_file

def test_details_table_logic():
    """
    Тестирует логику формирования таблицы деталей:
    1. ScriptName всегда первым
    2. Параметры проекта без суффикса имени файла
    3. Параметры base.env с суффиксом (имя_файла)
    4. Переопределенные значения показывают базовое значение
    """
    
    print("="*80)
    print("ТЕСТ ЛОГИКИ ТАБЛИЦЫ ДЕТАЛЕЙ ПРОЕКТА")
    print("="*80)
    
    # Пути к тестовым файлам (файл находится в tests/unit/)
    project_root = Path(__file__).parent.parent.parent
    projects_dir = project_root / 'projects'
    base_env_files = list(projects_dir.glob('*.env'))
    
    if not base_env_files:
        print("✗ Не найден базовый .env файл в projects/")
        return False
    
    base_env_path = base_env_files[0]
    base_env_name = base_env_path.name
    
    # Ищем любой тестовый проект (первый найденный)
    test_project = None
    for env_file in projects_dir.rglob('*.env'):
        if env_file.parent != projects_dir:  # Не базовый файл
            test_project = env_file
            break
    
    if not test_project:
        print(f"✗ Не найдено ни одного проекта в {projects_dir}")
        return False
    
    print(f"\n1. Загрузка файлов:")
    print(f"   Базовый: {base_env_name}")
    print(f"   Проект:  {test_project.parent.name}/{test_project.name}")
    
    # Загружаем параметры
    base_params = load_env_file(str(base_env_path), silent=True)
    project_params = load_env_file(str(test_project), silent=True)
    
    if not project_params:
        print(f"✗ Не удалось загрузить параметры проекта: {test_project}")
        return False
    
    print(f"   ✓ Загружено из базового: {len(base_params)} параметров")
    print(f"   ✓ Загружено из проекта: {len(project_params)} параметров")
    
    # Формируем таблицу по той же логике что в GUI
    details_data = []
    
    # 1. ScriptName всегда первым
    print("\n2. Проверка порядка параметров:")
    if 'ScriptName' in project_params:
        param_name = 'ScriptName'
        value = project_params['ScriptName']
        # Проверяем переопределение
        if param_name in base_params and base_params[param_name] != value:
            value = f"{value} (в {base_env_name} = {base_params[param_name]})"
        details_data.append([param_name, value])
        print(f"   ✓ ScriptName на первом месте: {project_params['ScriptName']}")
    else:
        print("   ✗ ScriptName не найден в проекте")
        return False
    
    # 2. Остальные параметры из проекта (без суффикса)
    project_params_count = 0
    for param, value in sorted(project_params.items()):
        if param == 'ScriptName':
            continue
        # Проверяем переопределение
        if param in base_params and base_params[param] != value:
            value = f"{value} (в {base_env_name} = {base_params[param]})"
        details_data.append([param, value])
        project_params_count += 1
    
    print(f"   ✓ Параметры проекта (без суффикса): {project_params_count}")
    
    # 3. Параметры только из базового файла (с суффиксом)
    base_only_count = 0
    for param, value in sorted(base_params.items()):
        if param not in project_params:
            param_with_source = f"{param} ({base_env_name})"
            details_data.append([param_with_source, value])
            base_only_count += 1
    
    print(f"   ✓ Параметры только из базового (с суффиксом): {base_only_count}")
    
    # 4. Проверка переопределений
    print("\n3. Проверка переопределенных значений:")
    overridden_count = 0
    for param, proj_value in project_params.items():
        if param in base_params and base_params[param] != proj_value:
            overridden_count += 1
            print(f"   ✓ {param}: '{proj_value}' (в {base_env_name} = '{base_params[param]}')")
    
    if overridden_count == 0:
        print("   - Переопределенных параметров не найдено")
    
    # Вывод итоговой таблицы
    print("\n4. Итоговая таблица деталей:")
    print(f"   {'Параметр':<40} | {'Значение':<60}")
    print("   " + "-"*103)
    
    for idx, (param, value) in enumerate(details_data[:10], 1):  # Показываем первые 10
        # Обрезаем длинные значения
        value_display = value[:57] + "..." if len(value) > 60 else value
        print(f"   {param:<40} | {value_display:<60}")
    
    if len(details_data) > 10:
        print(f"   ... и еще {len(details_data) - 10} параметров")
    
    print("\n" + "="*80)
    print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print("="*80)
    
    return True

def test_param_descriptions():
    """
    Тестирует наличие описаний для всех параметров из проектов
    """
    
    print("\n" + "="*80)
    print("ТЕСТ НАЛИЧИЯ ОПИСАНИЙ ПАРАМЕТРОВ")
    print("="*80)
    
    # Загружаем params_descriptions.json
    project_root = Path(__file__).parent.parent.parent
    params_desc_file = project_root / 'src' / 'config' / 'params_descriptions.json'
    
    if not params_desc_file.exists():
        print(f"✗ Не найден файл: {params_desc_file}")
        return False
    
    with open(params_desc_file, 'r', encoding='utf-8') as f:
        params_descriptions = json.load(f)
    
    print(f"\n1. Загружен файл описаний: {params_desc_file.name}")
    print(f"   Секций: {len(params_descriptions)}")
    
    # Собираем все параметры из всех проектов
    projects_dir = project_root / 'projects'
    all_params = set()
    project_params_map = {}  # {param: [список проектов где используется]}
    
    print("\n2. Сканирование проектов:")
    for env_file in projects_dir.rglob('*.env'):
        if env_file.parent == projects_dir:
            # Пропускаем базовые .env в корне
            continue
        
        env_vars = load_env_file(str(env_file), silent=True)
        if env_vars:
            project_name = env_file.parent.name
            script_name = env_vars.get('ScriptName', 'unknown')
            
            for param in env_vars.keys():
                all_params.add(param)
                if param not in project_params_map:
                    project_params_map[param] = []
                project_params_map[param].append(f"{project_name} ({script_name})")
    
    print(f"   ✓ Найдено уникальных параметров: {len(all_params)}")
    
    # Функция получения описания (как в main_window.py)
    def get_param_description(param_name: str, script_name: str) -> str:
        # Сначала ищем в специфичных для скрипта (без .cmd)
        if script_name in params_descriptions:
            if param_name in params_descriptions[script_name]:
                return params_descriptions[script_name][param_name]
        
        # Пробуем с .cmd для обратной совместимости
        script_key_with_cmd = f"{script_name}.cmd"
        if script_key_with_cmd in params_descriptions:
            if param_name in params_descriptions[script_key_with_cmd]:
                return params_descriptions[script_key_with_cmd][param_name]
        
        # Затем ищем в общих
        if 'common' in params_descriptions:
            if param_name in params_descriptions['common']:
                return params_descriptions['common'][param_name]
        
        return ''
    
    # Проверяем наличие описаний
    print("\n3. Проверка наличия описаний:")
    missing_descriptions = []
    
    for param in sorted(all_params):
        # Получаем список проектов где используется параметр
        projects_list = project_params_map[param]
        
        # Проверяем описание для каждого скрипта
        has_description = False
        for project_info in projects_list:
            # Извлекаем script_name из строки "project_name (script_name)"
            script_name = project_info.split('(')[1].rstrip(')')
            description = get_param_description(param, script_name)
            if description:
                has_description = True
                break
        
        if not has_description:
            missing_descriptions.append((param, projects_list))
    
    if missing_descriptions:
        print(f"   ✗ Найдено параметров без описания: {len(missing_descriptions)}")
        print("\n4. Параметры без описания:")
        for param, projects_list in missing_descriptions:
            print(f"\n   Параметр: {param}")
            print(f"   Используется в проектах:")
            for project_info in projects_list[:3]:  # Показываем первые 3
                print(f"     - {project_info}")
            if len(projects_list) > 3:
                print(f"     ... и еще {len(projects_list) - 3}")
        
        print("\n" + "="*80)
        print(f"✗ ТЕСТ НЕ ПРОЙДЕН: {len(missing_descriptions)} параметров без описания")
        print("="*80)
        return False
    else:
        print(f"   ✓ Все параметры имеют описания")
        
        # Дополнительная проверка - показываем примеры описаний
        print("\n4. Примеры описаний (первые 5 параметров):")
        for param in sorted(all_params)[:5]:
            projects_list = project_params_map[param]
            script_name = projects_list[0].split('(')[1].rstrip(')')
            description = get_param_description(param, script_name)
            print(f"\n   {param}:")
            print(f"   {description[:100]}..." if len(description) > 100 else f"   {description}")
        
        print("\n" + "="*80)
        print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("="*80)
        return True

if __name__ == '__main__':
    print("Запуск тестов...\n")
    
    # Тест 1: Логика таблицы деталей
    result1 = test_details_table_logic()
    
    # Тест 2: Наличие описаний параметров
    result2 = test_param_descriptions()
    
    # Итоговый результат
    if result1 and result2:
        print("\n" + "="*80)
        print("✓✓✓ ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ ✓✓✓")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("✗✗✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ ✗✗✗")
        print("="*80)
        sys.exit(1)

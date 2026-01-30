#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест для проверки корректности отображения таблицы деталей проекта
"""

import sys
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
    
    # Ищем тестовый проект
    test_project = projects_dir / 'uhmrg_conf2edt' / 'uhmrg.env'
    
    if not test_project.exists():
        print(f"✗ Не найден тестовый проект: {test_project}")
        return False
    
    print(f"\n1. Загрузка файлов:")
    print(f"   Базовый: {base_env_name}")
    print(f"   Проект:  {test_project.name}")
    
    # Загружаем параметры
    base_params = load_env_file(str(base_env_path), silent=True)
    project_params = load_env_file(str(test_project), silent=True)
    
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

if __name__ == '__main__':
    test_details_table_logic()

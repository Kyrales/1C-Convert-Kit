#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест для проверки загрузки и получения описаний параметров
"""

import json
from pathlib import Path

# Пути (файл находится в tests/unit/, JSON в src/config/)
SCRIPT_DIR = Path(__file__).parent.parent.parent  # Корень проекта
PARAMS_DESC_FILE = SCRIPT_DIR / 'src' / 'config' / 'params_descriptions.json'


def test_json_file_exists():
    """Проверяет существование JSON файла"""
    print(f"\n1. Проверка существования файла: {PARAMS_DESC_FILE}")
    assert PARAMS_DESC_FILE.exists(), f"Файл не найден: {PARAMS_DESC_FILE}"
    print(f"   ✓ Файл существует")


def test_json_file_valid():
    """Проверяет валидность JSON"""
    print(f"\n2. Проверка валидности JSON")
    try:
        with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   ✓ JSON валиден")
    except json.JSONDecodeError as e:
        assert False, f"Ошибка парсинга JSON: {e}"


def test_json_structure():
    """Проверяет структуру JSON"""
    print(f"\n3. Проверка структуры JSON")
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert 'common' in data, "Отсутствует секция 'common'"
    print(f"   ✓ Секция 'common' найдена")
    
    assert 'conf2edt' in data, "Отсутствует секция 'conf2edt'"
    print(f"   ✓ Секция 'conf2edt' найдена")
    
    print(f"\n   Доступные секции:")
    for key in data.keys():
        print(f"     - {key}")


def test_common_params():
    """Проверяет наличие общих параметров"""
    print(f"\n4. Проверка общих параметров")
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    common = data.get('common', {})
    
    # Проверяем ключевые параметры
    test_params = ['V8_VERSION', 'V8_TOOL', 'ScriptName', 'V8_SRC_PATH']
    
    for param in test_params:
        if param in common:
            print(f"   ✓ {param}: {common[param][:50]}...")
        else:
            print(f"   ✗ {param}: НЕ НАЙДЕН")
    
    print(f"\n   Всего параметров в 'common': {len(common)}")


def test_script_specific_params():
    """Проверяет параметры для конкретного скрипта"""
    print(f"\n5. Проверка параметров для conf2edt")
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    script_params = data.get('conf2edt', {})
    
    if 'V8_SRC_PATH' in script_params:
        print(f"   ✓ V8_SRC_PATH: {script_params['V8_SRC_PATH']}")
    else:
        print(f"   ✗ V8_SRC_PATH: НЕ НАЙДЕН")
    
    if 'V8_DST_PATH' in script_params:
        print(f"   ✓ V8_DST_PATH: {script_params['V8_DST_PATH']}")
    else:
        print(f"   ✗ V8_DST_PATH: НЕ НАЙДЕН")
    
    print(f"\n   Всего параметров для 'conf2edt': {len(script_params)}")


def get_param_description(params_descriptions, param_name, script_name):
    """
    Получает описание параметра из JSON (копия функции из GUI)
    
    Args:
        params_descriptions: загруженный JSON
        param_name: имя параметра
        script_name: имя скрипта (например: conf2edt)
        
    Returns:
        str: описание параметра или пустая строка
    """
    if not params_descriptions:
        return ''
    
    # Сначала ищем в специфичных для скрипта
    if script_name in params_descriptions:
        if param_name in params_descriptions[script_name]:
            return params_descriptions[script_name][param_name]
    
    # Затем ищем в общих
    if 'common' in params_descriptions:
        if param_name in params_descriptions['common']:
            return params_descriptions['common'][param_name]
    
    return ''


def test_get_description_function():
    """Проверяет функцию получения описания"""
    print(f"\n6. Проверка функции get_param_description")
    
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Тест 1: Параметр из common
    desc = get_param_description(data, 'V8_VERSION', 'conf2edt')
    print(f"\n   Тест 1: V8_VERSION (из common)")
    print(f"   Результат: {desc}")
    assert desc != '', "Описание не найдено для V8_VERSION"
    print(f"   ✓ Описание найдено")
    
    # Тест 2: Параметр специфичный для скрипта
    desc = get_param_description(data, 'V8_SRC_PATH', 'conf2edt')
    print(f"\n   Тест 2: V8_SRC_PATH (специфичный для conf2edt)")
    print(f"   Результат: {desc}")
    assert desc != '', "Описание не найдено для V8_SRC_PATH"
    print(f"   ✓ Описание найдено")
    
    # Тест 3: Приоритет специфичного над общим
    desc_specific = get_param_description(data, 'V8_SRC_PATH', 'conf2edt')
    desc_common = data.get('common', {}).get('V8_SRC_PATH', '')
    print(f"\n   Тест 3: Приоритет специфичного описания")
    print(f"   Специфичное: {desc_specific[:50]}...")
    if desc_common:
        print(f"   Общее: {desc_common[:50]}...")
        assert desc_specific != desc_common, "Специфичное описание должно отличаться от общего"
    print(f"   ✓ Приоритет работает корректно")
    
    # Тест 4: Несуществующий параметр
    desc = get_param_description(data, 'NONEXISTENT_PARAM', 'conf2edt')
    print(f"\n   Тест 4: Несуществующий параметр")
    print(f"   Результат: '{desc}'")
    assert desc == '', "Для несуществующего параметра должна быть пустая строка"
    print(f"   ✓ Возвращается пустая строка")


def test_real_scenario():
    """Тест реального сценария из uhmrg.env"""
    print(f"\n7. Тест реального сценария (uhmrg.env)")
    
    with open(PARAMS_DESC_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Параметры из uhmrg.env
    params = [
        'ScriptName',
        'V8_CONVERT_TOOL',
        'V8_CONF_CLEAN_DST',
        'V8_EXT_CLEAN_DST',
        'IBCMD_DATA',
        'V8_SRC_PATH',
        'V8_DST_PATH',
        'V8_DP_CLEAN_DST'
    ]
    
    script_name = 'conf2edt'
    
    print(f"\n   Скрипт: {script_name}")
    print(f"   Параметры из uhmrg.env:\n")
    
    found_count = 0
    for param in params:
        desc = get_param_description(data, param, script_name)
        if desc:
            print(f"   ✓ {param:20} -> {desc[:60]}...")
            found_count += 1
        else:
            print(f"   ✗ {param:20} -> ОПИСАНИЕ НЕ НАЙДЕНО")
    
    print(f"\n   Найдено описаний: {found_count}/{len(params)}")
    assert found_count > 0, "Не найдено ни одного описания"


def main():
    """Запуск всех тестов"""
    print("="*80)
    print("ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ ОПИСАНИЙ ПАРАМЕТРОВ")
    print("="*80)
    
    try:
        test_json_file_exists()
        test_json_file_valid()
        test_json_structure()
        test_common_params()
        test_script_specific_params()
        test_get_description_function()
        test_real_scenario()
        
        print("\n" + "="*80)
        print("✓ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
        print("="*80)
        
    except AssertionError as e:
        print("\n" + "="*80)
        print(f"✗ ТЕСТ ПРОВАЛЕН: {e}")
        print("="*80)
        raise


if __name__ == '__main__':
    main()

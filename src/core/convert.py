#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт конвертации обработки 1С из EDT в EPF формат
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Optional


# ANSI цветовые коды для Windows
class Colors:
    """Цветовые коды для консоли"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'
    
    @staticmethod
    def enable_windows_colors():
        """Включает поддержку ANSI цветов в Windows"""
        if sys.platform == 'win32':
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass


def print_info(message):
    """Выводит информационное сообщение зеленым цветом"""
    print(f"{Colors.GREEN}[ИНФО]{Colors.RESET} {message}")


def print_error(message):
    """Выводит сообщение об ошибке красным цветом"""
    print(f"{Colors.RED}[ОШИБКА]{Colors.RESET} {message}")


def print_warning(message):
    """Выводит предупреждение желтым цветом"""
    print(f"{Colors.YELLOW}[ВНИМАНИЕ]{Colors.RESET} {message}")


def print_success(message):
    """Выводит сообщение об успехе зеленым цветом"""
    print(f"{Colors.GREEN}[УСПЕХ]{Colors.RESET} {message}")


def load_env_file(env_path, silent=False):
    """
    Загружает переменные из .env файла
    
    Args:
        env_path: путь к .env файлу
        silent: если True, не выводить сообщения (для GUI)
        
    Returns:
        dict: словарь с переменными окружения
    """
    env_vars = {}
    
    if not os.path.exists(env_path):
        if not silent:
            print_error(f"Файл .env не найден: {env_path}")
        return None
    
    if not silent:
        print_info(f"Чтение переменных окружения из: {env_path}")
    
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Убираем кавычки если есть
                value = value.strip('"').strip("'")
                env_vars[key.strip()] = value
    
    return env_vars


def find_env_files(path):
    """
    Находит .env файлы по указанному пути
    
    Args:
        path: путь к .env файлу или каталогу с .env файлами
        
    Returns:
        list: список путей к найденным .env файлам
    """
    path = Path(path)
    
    # Если это файл, возвращаем его
    if path.is_file():
        if path.suffix == '.env' or path.name.endswith('.env'):
            return [str(path)]
        else:
            print_error(f"Файл {path} не является .env файлом")
            return []
    
    # Если это каталог, ищем все .env файлы
    if path.is_dir():
        env_files = sorted(path.glob('*.env'))
        if env_files:
            print_info(f"Найдено {len(env_files)} .env файлов в каталоге {path}:")
            for env_file in env_files:
                print_info(f"  - {env_file.name}")
            return [str(f) for f in env_files]
        else:
            print_error(f"Не найдено .env файлов в каталоге {path}")
            return []
    
    print_error(f"Путь не существует: {path}")
    return []


def merge_env_files(env_files, silent=False):
    """
    Объединяет несколько .env файлов в один словарь
    Более вложенные файлы (из папки проекта) имеют приоритет над базовыми
    При совпадении параметров используется значение из более вложенного файла
    
    Args:
        env_files: список путей к .env файлам (от базовых к вложенным)
        silent: если True, не выводить сообщения (для GUI)
        
    Returns:
        dict: объединенный словарь с переменными окружения
    """
    merged_vars = {}
    
    for env_file in env_files:
        env_vars = load_env_file(env_file, silent=silent)
        if env_vars is None:
            return None
        
        # Проверяем на дубли и выводим информацию о переопределении
        for key, value in env_vars.items():
            if key in merged_vars and merged_vars[key] != value:
                if not silent:
                    print_info(f"Параметр '{key}' переопределен: '{merged_vars[key]}' -> '{value}'")
        
        # Объединяем, переопределяя существующие значения
        # Более поздние файлы (вложенные) имеют приоритет
        merged_vars.update(env_vars)
    
    if len(env_files) > 1 and not silent:
        print_info(f"Объединено {len(env_files)} файлов конфигурации")
    
    return merged_vars


def run_conversion(env_files, output_path=None, debug=False):
    """
    Запускает конвертацию используя Python конвертеры
    
    Args:
        env_files: список путей к .env файлам
        output_path: путь для сохранения результата (опционально)
        debug: режим отладки (опционально)
        
    Returns:
        int: код возврата (0 - успех, 1 - ошибка)
    """
    # Получаем абсолютные пути к .env файлам
    env_files = [os.path.abspath(f) for f in env_files]
    
    # Загружаем и объединяем переменные из всех .env файлов
    env_vars = merge_env_files(env_files)
    if env_vars is None:
        return 1
    
    # Переопределяем путь назначения если передан
    if output_path:
        env_vars['V8_DST_PATH'] = os.path.abspath(output_path)
        print_info(f"Используется переданный путь назначения: {output_path}")
    
    # Получаем тип конвертации из ScriptName
    script_name = env_vars.get('ScriptName')
    if not script_name:
        print_error("Переменная ScriptName не определена в .env файлах")
        return 1
    
    # Получаем конвертер из реестра
    try:
        from converters.registry import ConverterRegistry
    except ImportError:
        # Пробуем импортировать с относительным путем
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from converters.registry import ConverterRegistry
    
    registry = ConverterRegistry()
    converter_class = registry.get_converter(script_name)
    
    if not converter_class:
        print_error(f"Конвертер для '{script_name}' не найден")
        print_error(f"Доступные конвертеры: {', '.join(registry.list_converters())}")
        return 1
    
    print_info(f"Используется Python конвертер: {converter_class.__name__}")
    
    # Получаем пути из переменных окружения
    src_path = env_vars.get('V8_SRC_PATH', '')
    dst_path = env_vars.get('V8_DST_PATH', '')
    
    if not src_path:
        print_error("Переменная V8_SRC_PATH не определена в .env файле")
        return 1
    
    if not dst_path:
        print_error("Путь назначения не указан (V8_DST_PATH в .env или параметр --output)")
        return 1
    
    print_info("Запуск конвертации...")
    print_info(f"Источник: {src_path}")
    print_info(f"Назначение: {dst_path}")
    
    # Создаем и запускаем конвертер
    try:
        converter = converter_class(env_vars, silent=False, debug=debug)
        converter.validate()
        exit_code = converter.convert()
        
        if exit_code == 0:
            # Проверяем наличие выходного файла
            dst_path_obj = Path(dst_path)
            if dst_path_obj.exists():
                if dst_path_obj.is_file():
                    print()
                    print_success(f"Конвертация завершена успешно: {dst_path}")
                    print_info(f"Размер файла: {dst_path_obj.stat().st_size / (1024 * 1024):.2f} МБ")
                else:
                    print()
                    print_success(f"Конвертация завершена успешно")
                    print_info(f"Результаты сохранены в: {dst_path}")
            else:
                print()
                print_success("Конвертация завершена успешно")
            
            converter.cleanup()
        
        return exit_code
        
    except Exception as e:
        print_error(f"Ошибка при выполнении конвертации: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Главная функция"""
    # Включаем поддержку цветов в Windows
    Colors.enable_windows_colors()
    
    parser = argparse.ArgumentParser(
        description='Конвертация файлов 1С (обработки, отчеты, конфигурации, расширения)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python convert.py
  python convert.py --env F:\\Projects\\MyProject
  python convert.py --env F:\\Projects\\MyProject --output F:\\Output

Поддерживаемые типы конвертации (определяются по ScriptName в .env):
  - dp2epf.cmd / dp2erf.cmd - обработки и отчеты в бинарный формат (.epf, .erf)
  - conf2cf.cmd - конфигурация в бинарный формат (.cf)
  - ext2cfe.cmd - расширение в бинарный формат (.cfe)
        """
    )
    
    parser.add_argument(
        '-e', '--env',
        dest='project_path',
        help='Путь к папке проекта (с .env файлами и скриптом конвертации)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Путь для сохранения результата (переопределяет V8_DST_PATH из .env)'
    )
    
    parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Режим отладки (выводит выполняемые команды)'
    )
    
    args = parser.parse_args()
    
    # Собираем все .env файлы
    all_env_files = []
    script_dir = Path(__file__).parent.parent.parent  # Корень проекта
    projects_dir = script_dir / 'projects'
    
    if not args.project_path:
        # Если путь не указан, ищем все .env в папке projects
        print_info(f"Параметр --env не указан, поиск .env файлов в: {projects_dir}")
        env_files = find_env_files(projects_dir)
        
        if not env_files:
            print_error("Не найдено ни одного .env файла")
            sys.exit(1)
        
        all_env_files.extend(env_files)
    else:
        # Указан путь к папке проекта
        project_path = Path(args.project_path)
        
        if not project_path.is_absolute():
            project_path = Path(os.getcwd()) / project_path
        
        if not project_path.exists():
            print_error(f"Папка проекта не существует: {project_path}")
            sys.exit(1)
        
        print_info(f"Папка проекта: {project_path}")
        
        # 1. Сначала ищем базовый .env в папке projects/
        # Ищем любой .env файл в корне projects/ (не в подпапках)
        base_env_files = [f for f in projects_dir.glob('*.env') if f.is_file()]
        if base_env_files:
            # Берем первый найденный (или можно отсортировать)
            base_env = base_env_files[0]
            print_info(f"Найден базовый .env: {base_env}")
            all_env_files.append(str(base_env))
        else:
            print_warning(f"Базовый .env файл не найден в: {projects_dir}")
        
        # 2. Затем ищем все .env файлы в папке проекта
        project_env_files = find_env_files(project_path)
        if not project_env_files:
            print_error(f"Не найдено .env файлов в папке проекта: {project_path}")
            sys.exit(1)
        
        all_env_files.extend(project_env_files)
    
    if not all_env_files:
        print_error("Не найдено ни одного .env файла для обработки")
        sys.exit(1)
    
    # Запускаем конвертацию
    exit_code = run_conversion(all_env_files, args.output, args.debug)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

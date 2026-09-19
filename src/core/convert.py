#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ядро системы конвертации 1С файлов

Обеспечивает:
- Загрузку и объединение .env конфигураций
- Интеграцию с ConverterRegistry для автоматического выбора конвертера
- CLI интерфейс для запуска конвертаций из командной строки
- Поддержку всех типов конвертации:
  * Конфигурации (EDT/XML/IB → CF, DT ↔ IB)
  * Обработки и отчеты (EDT/XML → EPF/ERF)
  * Расширения (EDT/XML/IB → CFE)
  * Валидация EDT проектов

Использование CLI:
    python src/core/convert.py --env projects/MyProject/project.env
    python src/core/convert.py --env projects/MyProject/project.env --output /path/to/output
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Добавляем корневую директорию проекта в sys.path для корректных импортов
_SCRIPT_DIR = Path(__file__).parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# Импортируем Logger из базового конвертера
from converters.base.converter import Logger  # type: ignore

# Создаем глобальный экземпляр логгера для CLI
logger = Logger(silent=False, debug=False)


def load_env_file(env_path: str, silent: bool = False) -> Optional[Dict[str, str]]:
    """
    Загружает переменные из .env файла
    
    Поддерживает:
    - UTF-8 с BOM и без BOM
    - Fallback на CP1251 для старых файлов
    - Комментарии (строки начинающиеся с #)
    - Значения в кавычках (одинарных и двойных)
    
    Args:
        env_path: путь к .env файлу
        silent: если True, не выводить сообщения (для GUI)
        
    Returns:
        dict: словарь с переменными окружения, или None при ошибке
    """
    env_vars: Dict[str, str] = {}
    
    if not os.path.exists(env_path):
        if not silent:
            logger.error(f"Файл .env не найден: {env_path}")
        return None
    
    if not silent:
        logger.info(f"Чтение переменных окружения из: {env_path}")
    
    # Пробуем разные кодировки
    encodings = ['utf-8-sig', 'utf-8', 'cp1251']
    content = None
    
    for encoding in encodings:
        try:
            with open(env_path, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, LookupError):
            continue
    
    if content is None:
        if not silent:
            logger.error(f"Не удалось прочитать файл {env_path} ни в одной из кодировок: {encodings}")
        return None
    
    # Парсим содержимое
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            # Убираем кавычки если есть (одинарные или двойные)
            if (value.startswith('"') and value.endswith('"')) or \
               (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            env_vars[key] = value
    
    return env_vars


def find_env_files(path: str) -> List[str]:
    """
    Находит .env файлы по указанному пути
    
    Args:
        path: путь к .env файлу или каталогу с .env файлами
        
    Returns:
        list: список путей к найденным .env файлам
    """
    path_obj = Path(path)
    
    # Если это файл, возвращаем его
    if path_obj.is_file():
        if path_obj.suffix == '.env' or path_obj.name.endswith('.env'):
            return [str(path_obj)]
        else:
            logger.error(f"Файл {path_obj} не является .env файлом")
            return []
    
    # Если это каталог, ищем все .env файлы
    if path_obj.is_dir():
        env_files = sorted(path_obj.glob('*.env'))
        if env_files:
            logger.info(f"Найдено {len(env_files)} .env файлов в каталоге {path_obj}:")
            for env_file in env_files:
                logger.info(f"  - {env_file.name}")
            return [str(f) for f in env_files]
        else:
            logger.error(f"Не найдено .env файлов в каталоге {path_obj}")
            return []
    
    logger.error(f"Путь не существует: {path_obj}")
    return []


def merge_env_files(env_files: List[str], silent: bool = False) -> Optional[Dict[str, str]]:
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
    merged_vars: Dict[str, str] = {}
    
    for env_file in env_files:
        env_vars = load_env_file(env_file, silent=silent)
        if env_vars is None:
            return None
        
        # Проверяем на дубли и выводим информацию о переопределении
        for key, value in env_vars.items():
            if key in merged_vars and merged_vars[key] != value:
                if not silent:
                    logger.info(f"Параметр '{key}' переопределен: '{merged_vars[key]}' -> '{value}'")
        
        # Объединяем, переопределяя существующие значения
        # Более поздние файлы (вложенные) имеют приоритет
        merged_vars.update(env_vars)
    
    if len(env_files) > 1 and not silent:
        logger.info(f"Объединено {len(env_files)} файлов конфигурации")
    
    return merged_vars


def run_conversion(env_files: List[str], output_path: Optional[str] = None, debug: bool = False) -> int:
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
    env_files_abs: List[str] = [os.path.abspath(f) for f in env_files]
    
    # Загружаем и объединяем переменные из всех .env файлов
    env_vars = merge_env_files(env_files_abs)
    if env_vars is None:
        return 1
    
    # Переопределяем путь назначения если передан
    if output_path:
        env_vars['V8_DST_PATH'] = os.path.abspath(output_path)
        logger.info(f"Используется переданный путь назначения: {output_path}")
    
    # Получаем тип конвертации из ScriptName
    script_name = env_vars.get('ScriptName')
    if not script_name:
        logger.error("Переменная ScriptName не определена в .env файлах")
        return 1
    
    # Получаем конвертер из реестра
    from converters.registry import ConverterRegistry  # type: ignore
    
    registry = ConverterRegistry()
    converter_class = registry.get_converter(script_name)
    
    if not converter_class:
        logger.error(f"Конвертер для '{script_name}' не найден")
        logger.error(f"Доступные конвертеры: {', '.join(registry.list_converters())}")
        return 1
    
    logger.info(f"Используется Python конвертер: {converter_class.__name__}")
    
    # Получаем пути из переменных окружения
    src_path = env_vars.get('V8_SRC_PATH', '')
    dst_path = env_vars.get('V8_DST_PATH', '')
    
    if not src_path:
        logger.error("Переменная V8_SRC_PATH не определена в .env файле")
        return 1
    
    if not dst_path:
        logger.error("Путь назначения не указан (V8_DST_PATH в .env или параметр --output)")
        return 1
    
    logger.info("Запуск конвертации...")
    logger.info(f"Источник: {src_path}")
    logger.info(f"Назначение: {dst_path}")
    
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
                    logger.success(f"Конвертация завершена успешно: {dst_path}")
                    logger.info(f"Размер файла: {dst_path_obj.stat().st_size / (1024 * 1024):.2f} МБ")
                else:
                    print()
                    logger.success(f"Конвертация завершена успешно")
                    logger.info(f"Результаты сохранены в: {dst_path}")
            else:
                print()
                logger.success("Конвертация завершена успешно")
            
            # Очистка уже выполнена внутри converter.convert() в зависимости от V8_TEMP_AFTER_CLEAN
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Ошибка при выполнении конвертации: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> None:
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description='Конвертация файлов 1С (обработки, отчеты, конфигурации, расширения)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python convert.py
  python convert.py --env F:\\Projects\\MyProject
  python convert.py --env F:\\Projects\\MyProject --output F:\\Output

Поддерживаемые типы конвертации (определяются по ScriptName в .env):
  - dp2epf / dp2erf - обработки и отчеты в бинарный формат (.epf, .erf)
  - conf2cf - конфигурация в бинарный формат (.cf)
  - dt2ib / ib2dt - восстановление и выгрузка информационной базы (.dt)
  - ext2cfe - расширение в бинарный формат (.cfe)
        """
    )
    
    _ = parser.add_argument(
        '-e', '--env',
        dest='project_path',
        help='Путь к папке проекта (с .env файлами и скриптом конвертации)'
    )
    
    _ = parser.add_argument(
        '-o', '--output',
        help='Путь для сохранения результата (переопределяет V8_DST_PATH из .env)'
    )
    
    _ = parser.add_argument(
        '-d', '--debug',
        action='store_true',
        help='Режим отладки (выводит выполняемые команды)'
    )
    
    args = parser.parse_args()
    
    # Извлекаем аргументы с явными типами
    project_path_arg: Optional[str] = getattr(args, 'project_path', None)
    output_arg: Optional[str] = getattr(args, 'output', None)
    debug_arg: bool = getattr(args, 'debug', False)
    
    # Собираем все .env файлы
    all_env_files: List[str] = []
    script_dir = Path(__file__).parent.parent.parent  # Корень проекта
    projects_dir = script_dir / 'projects'
    
    if not project_path_arg:
        # Если путь не указан, ищем все .env в папке projects
        logger.info(f"Параметр --env не указан, поиск .env файлов в: {projects_dir}")
        env_files = find_env_files(str(projects_dir))
        
        if not env_files:
            logger.error("Не найдено ни одного .env файла")
            sys.exit(1)
        
        all_env_files.extend(env_files)
    else:
        # Указан путь к папке проекта
        project_path = Path(project_path_arg)
        
        if not project_path.is_absolute():
            project_path = Path(os.getcwd()) / project_path
        
        if not project_path.exists():
            logger.error(f"Папка проекта не существует: {project_path}")
            sys.exit(1)
        
        logger.info(f"Папка проекта: {project_path}")
        
        # 1. Сначала ищем базовый .env в папке projects/
        # Ищем любой .env файл в корне projects/ (не в подпапках)
        base_env_files = [f for f in projects_dir.glob('*.env') if f.is_file()]
        if base_env_files:
            # Берем первый найденный (или можно отсортировать)
            base_env = base_env_files[0]
            logger.info(f"Найден базовый .env: {base_env}")
            all_env_files.append(str(base_env))
        else:
            logger.warning(f"Базовый .env файл не найден в: {projects_dir}")
        
        # 2. Затем ищем все .env файлы в папке проекта
        project_env_files = find_env_files(str(project_path))
        if not project_env_files:
            logger.error(f"Не найдено .env файлов в папке проекта: {project_path}")
            sys.exit(1)
        
        all_env_files.extend(project_env_files)
    
    if not all_env_files:
        logger.error("Не найдено ни одного .env файла для обработки")
        sys.exit(1)
    
    # Запускаем конвертацию
    exit_code = run_conversion(all_env_files, output_arg, debug_arg)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

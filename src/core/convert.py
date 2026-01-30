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
    print(f"{Colors.GREEN}[INFO]{Colors.RESET} {message}")


def print_error(message):
    """Выводит сообщение об ошибке красным цветом"""
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {message}")


def print_warning(message):
    """Выводит предупреждение желтым цветом"""
    print(f"{Colors.YELLOW}[WARNING]{Colors.RESET} {message}")


def print_success(message):
    """Выводит сообщение об успехе зеленым цветом"""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.RESET} {message}")


def find_legacy_script(script_name: str) -> Optional[Path]:
    """
    Находит legacy CMD скрипт в соответствующей папке
    
    Args:
        script_name: имя скрипта (например: dp2epf.cmd, conf2cf.cmd)
        
    Returns:
        Path: путь к скрипту или None если не найден
    """
    converters_dir = Path(__file__).parent.parent / 'converters'
    
    # Определяем тип скрипта по имени
    if script_name.startswith('conf'):
        legacy_dir = converters_dir / 'configuration' / 'legacy'
    elif script_name.startswith('dp'):
        legacy_dir = converters_dir / 'dataprocessor' / 'legacy'
    elif script_name.startswith('ext'):
        legacy_dir = converters_dir / 'extension' / 'legacy'
    elif script_name.startswith('edt'):
        legacy_dir = converters_dir / 'validation' / 'legacy'
    else:
        return None
    
    script_path = legacy_dir / script_name
    return script_path if script_path.exists() else None


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


def get_output_file_info(script_name, src_path, dst_path):
    """
    Определяет информацию о выходном файле на основе имени скрипта
    
    Args:
        script_name: имя скрипта конвертации (например, dp2epf.cmd, conf2cf.cmd)
        src_path: путь к источнику
        dst_path: путь назначения
        
    Returns:
        tuple: (extension, file_type_description, needs_file_path) или (None, None, None) если тип не определен
        needs_file_path: True если скрипт требует путь к файлу, False если требует путь к каталогу
    """
    script_lower = script_name.lower()
    
    # Определяем тип выходного файла по окончанию имени скрипта
    if script_lower.endswith('2epf.cmd') or script_lower.endswith('2epf'):
        extension = '.epf'
        file_type = 'обработка'
        needs_file_path = False  # dp2epf требует каталог
    elif script_lower.endswith('2erf.cmd') or script_lower.endswith('2erf'):
        extension = '.erf'
        file_type = 'отчет'
        needs_file_path = False  # dp2erf требует каталог
    elif script_lower.endswith('2cf.cmd') or script_lower.endswith('2cf'):
        extension = '.cf'
        file_type = 'конфигурация'
        needs_file_path = True  # conf2cf требует путь к файлу
    elif script_lower.endswith('2cfe.cmd') or script_lower.endswith('2cfe'):
        extension = '.cfe'
        file_type = 'расширение'
        needs_file_path = True  # ext2cfe требует путь к файлу
    else:
        # Неизвестный тип скрипта
        return None, None, None
    
    return extension, file_type, needs_file_path


def run_conversion(env_files, output_path=None):
    """
    Запускает конвертацию
    
    Args:
        env_files: список путей к .env файлам
        output_path: путь для сохранения результата (опционально)
        
    Returns:
        int: код возврата (0 - успех, 1 - ошибка)
    """
    # Получаем абсолютные пути к .env файлам
    env_files = [os.path.abspath(f) for f in env_files]
    
    # Загружаем и объединяем переменные из всех .env файлов
    env_vars = merge_env_files(env_files)
    if env_vars is None:
        return 1
    
    # Получаем путь к скрипту из переменной ScriptName
    script_name = env_vars.get('ScriptName')
    if not script_name:
        print_error("Переменная ScriptName не определена в .env файлах")
        return 1
    
    # Ищем legacy скрипт в соответствующей папке
    conversion_script = find_legacy_script(script_name)
    
    if not conversion_script:
        print_error(f"Скрипт {script_name} не найден")
        print_error(f"Проверьте, что скрипт находится в папке src/converters/*/legacy/")
        return 1
    
    print_info(f"Используется скрипт конвертации: {conversion_script}")
    
    # Получаем директорию скрипта для запуска
    script_dir = conversion_script.parent
    
    # Получаем пути из переменных окружения
    src_path = env_vars.get('V8_SRC_PATH', '')
    dst_path = env_vars.get('V8_DST_PATH', '')
    
    # Если передан output_path, используем его вместо V8_DST_PATH
    if output_path:
        dst_path = os.path.abspath(output_path)
        print_info(f"Используется переданный путь назначения: {dst_path}")
        # Обновляем переменную в .env файле временно
        env_vars['V8_DST_PATH'] = dst_path
    
    if not src_path:
        print_error("Переменная V8_SRC_PATH не определена в .env файле")
        return 1
    
    if not dst_path:
        print_error("Путь назначения не указан (V8_DST_PATH в .env или параметр --output)")
        return 1
    
    # Определяем тип выходного файла и требования к пути
    extension, file_type, needs_file_path = get_output_file_info(script_name, src_path, dst_path)
    
    if extension is None:
        print_warning(f"Не удалось определить тип скрипта {script_name}")
        needs_file_path = None
    
    # Проверяем, является ли dst_path каталогом или файлом
    dst_path_obj = Path(dst_path)
    # Путь считается каталогом если:
    # 1. Заканчивается на слеш
    # 2. Существует и является каталогом
    # 3. Не имеет расширения (но это не надежный признак)
    is_directory = dst_path.endswith(('\\', '/'))
    if not is_directory and dst_path_obj.exists():
        is_directory = dst_path_obj.is_dir()
    
    has_extension = dst_path_obj.suffix != ''
    
    # Валидация пути в зависимости от типа скрипта
    if needs_file_path is True:
        # Скрипты 2cf, 2cfe требуют путь к файлу
        if is_directory:
            print_error(f"Скрипт {script_name} требует путь к файлу с расширением {extension}, а не к каталогу")
            print_error(f"Текущее значение V8_DST_PATH: {dst_path}")
            print_error(f"Пример правильного пути: {dst_path_obj / ('output' + extension)}")
            return 1
        if not has_extension:
            print_error(f"Скрипт {script_name} требует путь к файлу с расширением {extension}")
            print_error(f"Текущее значение V8_DST_PATH: {dst_path}")
            print_error(f"Путь должен заканчиваться на {extension}")
            return 1
        if has_extension and dst_path_obj.suffix.lower() != extension.lower():
            print_warning(f"Расширение файла {dst_path_obj.suffix} не соответствует ожидаемому {extension}")
    
    elif needs_file_path is False:
        # Скрипты 2epf, 2erf требуют путь к каталогу
        if has_extension and not is_directory:
            print_error(f"Скрипт {script_name} требует путь к каталогу, а не к конкретному файлу")
            print_error(f"Текущее значение V8_DST_PATH: {dst_path}")
            print_error(f"Пример правильного пути: {dst_path_obj.parent}")
            return 1
    
    # Формируем окончательный путь
    if needs_file_path is True:
        # Для скриптов требующих файл - используем путь как есть
        final_dst_path = dst_path
        dst_dir = dst_path_obj.parent
    else:
        # Для скриптов требующих каталог
        if is_directory:
            final_dst_path = dst_path
            dst_dir = dst_path_obj
        else:
            # Если указан файл, берем его родительский каталог
            final_dst_path = str(dst_path_obj.parent)
            dst_dir = dst_path_obj.parent
            print_info(f"Используется каталог из пути: {final_dst_path}")
    
    # Обновляем переменную окружения
    env_vars['V8_DST_PATH'] = final_dst_path
    
    # Создаем каталог назначения если не существует
    os.makedirs(dst_dir, exist_ok=True)
    print_info(f"Каталог назначения: {dst_dir}")
    
    # Создаем временный .env файл с объединенными настройками
    import tempfile
    temp_fd, temp_env_file = tempfile.mkstemp(suffix='.env', text=True)
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            for key, value in env_vars.items():
                # Пропускаем служебную переменную ScriptName
                if key == 'ScriptName':
                    continue
                # Добавляем кавычки для путей с пробелами
                if ' ' in value and not (value.startswith('"') and value.endswith('"')):
                    value = f'"{value}"'
                f.write(f'{key}={value}\n')
        print_info("Создан временный объединенный .env файл")
    except Exception as e:
        print_error(f"Ошибка создания временного .env: {e}")
        return 1
    
    # Формируем команду для запуска
    # Для скриптов расширений (ext2*) нужно передать имя расширения как 3-й параметр
    if script_name.startswith('ext'):
        ext_name = env_vars.get('V8_EXT_NAME', '')
        cmd = [
            'cmd.exe',
            '/c',
            str(conversion_script),
            '',  # первый параметр пустой (путь источника берется из .env)
            '',  # второй параметр пустой (путь назначения берется из .env)
            ext_name,  # третий параметр - имя расширения
            temp_env_file  # четвертый параметр - путь к временному объединенному .env
        ]
    else:
        cmd = [
            'cmd.exe',
            '/c',
            str(conversion_script),
            '',  # первый параметр пустой (путь источника берется из .env)
            '',  # второй параметр пустой (путь назначения берется из .env)
            temp_env_file  # третий параметр - путь к временному объединенному .env
        ]
    
    print_info("Запуск конвертации...")
    print_info(f"Источник: {src_path}")
    print_info(f"Назначение: {final_dst_path}")
    
    # Запускаем процесс конвертации из папки где находится скрипт
    try:
        result = subprocess.run(
            cmd,
            cwd=str(script_dir),
            encoding='cp1251',
            errors='replace'
        )
        
        # Удаляем временный файл
        try:
            os.unlink(temp_env_file)
            print_info("Временный .env файл удален")
        except Exception as e:
            print_warning(f"Не удалось удалить временный файл: {e}")
        
        if result.returncode == 0:
            # Проверяем наличие выходного файла
            if needs_file_path is True:
                # Для скриптов создающих файл - проверяем конкретный файл
                output_file_path = Path(final_dst_path)
            else:
                # Для скриптов создающих файл в каталоге - ищем файл с нужным расширением
                base_name = Path(src_path).name
                output_file_path = Path(final_dst_path) / (base_name + extension)
            
            if output_file_path.exists():
                print()
                print_success(f"{file_type.capitalize()} успешно сконвертирована: {output_file_path}")
                print_info(f"Размер файла: {output_file_path.stat().st_size / (1024 * 1024):.2f} МБ")
            else:
                print()
                print_warning(f"Конвертация завершена, но файл не найден: {output_file_path}")
                print_success("Конвертация завершена успешно")
            
            return 0
        else:
            print()
            print_error(f"Ошибка конвертации (код возврата: {result.returncode})")
            return 1
            
    except Exception as e:
        print_error(f"Исключение при выполнении конвертации: {e}")
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
    exit_code = run_conversion(all_env_files, args.output)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

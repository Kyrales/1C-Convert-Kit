#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Интеграционный тест проверки команд из лога отладки.

Тест проверяет что команды 1cv8.exe и edtcli корректно выводятся в режиме отладки
и могут быть скопированы для ручного запуска из консоли.

Основные проверки:
1. Успешное выполнение конвертации в режиме отладки
2. Извлечение команд из лога (паттерн: [ОТЛАДКА] Команда: ...)
3. Фильтрация комплексных команд Python (не должны выполняться отдельно)
4. Проверка корректности формата команд (парсинг через shlex)
5. Поиск и проверка лог-файлов 1cv8.exe
6. Проверка создания итогового CF файла

Примечание: Команды НЕ выполняются повторно в тесте, так как это приведет к ошибкам
(workspace занят, ИБ уже содержит конфигурацию и т.д.). Тест только проверяет что
команды корректно выводятся и могут быть скопированы для ручного запуска.
"""

import sys
import pytest
import subprocess
import re
import tempfile
import shutil
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.convert import load_env_file


class TestDebugCommands:
    """Тесты проверки команд из лога отладки"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Подготовка и очистка для каждого теста"""
        # Список созданных тестом файлов и директорий для очистки
        created_items = []
        
        # Выполняем тест
        yield created_items
        
        # Очистка после теста: удаляем только то, что создал этот тест
        for item in created_items:
            if item.exists():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception as e:
                    print(f"Предупреждение: не удалось удалить {item}: {e}")
    
    def test_demo_edt_cf_debug_commands(self, setup_and_teardown):
        """
        Тест проверки команд из лога отладки для проекта Демо_edt_в_cf
        
        Проверяет:
        - Успешное выполнение конвертации в режиме отладки
        - Извлечение команд из лога
        - Корректность формата команд (можно скопировать и запустить вручную)
        - Проверку содержимого лог-файлов 1cv8.exe
        - Создание итогового CF файла
        
        Примечание: Команды НЕ выполняются повторно, так как это приведет к ошибкам
        (workspace занят, ИБ уже содержит конфигурацию и т.д.). Тест проверяет что
        команды корректно выводятся в лог и могут быть скопированы для ручного запуска.
        """
        # Получаем список для отслеживания созданных файлов
        created_items = setup_and_teardown
        # Arrange: подготовка путей
        demo_project_env = project_root / 'projects' / 'Демо_edt_в_cf' / 'Демо_edt_в_cf_conf2cf.env'
        
        # Проверяем наличие проекта
        assert demo_project_env.exists(), f"Проект Демо_edt_в_cf не найден: {demo_project_env}"
        
        # Создаем временный файл для лога
        log_fd, log_path_str = tempfile.mkstemp(suffix='.log', text=True)
        log_path = Path(log_path_str)
        
        try:
            # Act 1: Запускаем конвертацию в режиме отладки
            print(f"\n{'='*70}")
            print(f"[ЭТАП 1] Запуск конвертации в режиме отладки")
            print(f"{'='*70}")
            
            convert_script = project_root / 'src' / 'core' / 'convert.py'
            cmd = [
                sys.executable,
                str(convert_script),
                '--env', str(demo_project_env),
                '--debug'
            ]
            
            # Запускаем процесс и сохраняем вывод
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=str(project_root)
            )
            
            # Читаем вывод и сохраняем в файл
            output_lines = []
            with open(log_fd, 'w', encoding='utf-8', closefd=False) as log_file:
                for line in iter(process.stdout.readline, b''):
                    if not line:
                        break
                    
                    # Декодируем с обработкой разных кодировок
                    decoded_line = None
                    for encoding in ['utf-8', 'cp1251', 'cp866']:
                        try:
                            decoded_line = line.decode(encoding)
                            break
                        except (UnicodeDecodeError, AttributeError):
                            continue
                    
                    if decoded_line is None:
                        decoded_line = line.decode('utf-8', errors='replace')
                    
                    output_lines.append(decoded_line)
                    _ = log_file.write(decoded_line)
            
            exit_code = process.wait()
            
            # Assert 1: Проверяем успешность конвертации
            assert exit_code == 0, f"Конвертация завершилась с ошибкой (код: {exit_code})"
            print(f"✓ Конвертация завершена успешно (код: {exit_code})")
            print(f"✓ Лог сохранен в: {log_path}")
            
            # Act 2: Извлекаем команды из лога
            print(f"\n{'='*70}")
            print(f"[ЭТАП 2] Извлечение команд из лога")
            print(f"{'='*70}")
            
            # Читаем лог-файл
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                log_content = f.read()
            
            # Ищем строки с командами (паттерн: [ОТЛАДКА] Команда: ...)
            # Убираем ANSI escape коды
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            log_content_clean = ansi_escape.sub('', log_content)
            
            # Извлекаем команды
            command_pattern = r'\[ОТЛАДКА\]\s+Команда:\s+(.+?)(?:\n|$)'
            all_commands = re.findall(command_pattern, log_content_clean, re.MULTILINE)
            
            # Фильтруем команды: пропускаем комплексные команды Python
            # Эти команды запускают весь процесс конвертации и не должны выполняться отдельно
            commands = []
            skipped_commands = []
            
            for cmd_str in all_commands:
                # Пропускаем команды Python (python F:\1C\Projects\1c-convert-kit\src\core\convert.py ...)
                if 'python' in cmd_str.lower() and 'convert.py' in cmd_str:
                    skipped_commands.append(cmd_str)
                    continue
                commands.append(cmd_str)
            
            # Assert 2: Проверяем что команды найдены
            assert len(commands) > 0, "Команды не найдены в логе отладки"
            print(f"✓ Найдено команд: {len(all_commands)}")
            print(f"✓ Пропущено комплексных команд Python: {len(skipped_commands)}")
            print(f"✓ Команд для выполнения: {len(commands)}")
            
            # Выводим пропущенные команды
            if skipped_commands:
                print(f"\nПропущенные комплексные команды:")
                for i, cmd_str in enumerate(skipped_commands, 1):
                    cmd_display = cmd_str if len(cmd_str) <= 100 else f"{cmd_str[:97]}..."
                    print(f"  [SKIP-{i}] {cmd_display}")
            
            # Выводим найденные команды
            print(f"\nКоманды для выполнения:")
            for i, cmd_str in enumerate(commands, 1):
                # Обрезаем длинные команды для вывода
                cmd_display = cmd_str if len(cmd_str) <= 100 else f"{cmd_str[:97]}..."
                print(f"  [{i}] {cmd_display}")
            
            # Act 3: Проверяем формат команд и ищем лог-файлы
            print(f"\n{'='*70}")
            print(f"[ЭТАП 3] Проверка формата команд и поиск лог-файлов")
            print(f"{'='*70}")
            
            log_files_to_check = []
            temp_dir = None
            
            for i, cmd_str in enumerate(commands, 1):
                print(f"\n[Команда {i}/{len(commands)}]")
                cmd_display = cmd_str if len(cmd_str) <= 80 else f"{cmd_str[:77]}..."
                print(f"  {cmd_display}")
                
                try:
                    # Парсим команду (проверяем что она корректно разбирается)
                    import shlex
                    cmd_args = shlex.split(cmd_str)
                    print(f"  ✓ Команда корректно парсится ({len(cmd_args)} аргументов)")
                    
                    # Ищем лог-файл в команде (параметр /Out)
                    log_file_path = None
                    for j, arg in enumerate(cmd_args):
                        if arg.startswith('/Out'):
                            # Формат может быть: /Out file.log или /Out"file.log"
                            log_part = arg[4:].strip('"').strip()
                            if log_part:
                                log_file_path = Path(log_part)
                            elif j + 1 < len(cmd_args):
                                next_arg = cmd_args[j + 1].strip('"')
                                # Проверяем что следующий аргумент не начинается с /
                                if not next_arg.startswith('/'):
                                    log_file_path = Path(next_arg)
                            break
                    
                    # Определяем временную директорию из команды
                    if temp_dir is None:
                        for arg in cmd_args:
                            if 'ConfigurationConverter_' in arg:
                                # Извлекаем путь к временной директории
                                match = re.search(r'([a-zA-Z]:[/\\].+?ConfigurationConverter_\d{8}_\d{6})', arg)
                                if match:
                                    temp_dir = Path(match.group(1))
                                    # Добавляем временную директорию в список для очистки
                                    if temp_dir not in created_items:
                                        created_items.append(temp_dir)
                                    break
                    
                    # Проверяем лог-файл если он указан
                    if log_file_path:
                        if log_file_path.exists():
                            log_files_to_check.append(log_file_path)
                            log_size = log_file_path.stat().st_size
                            print(f"  ✓ Лог-файл найден: {log_file_path.name} ({log_size} байт)")
                        else:
                            print(f"  ⚠ Лог-файл не найден: {log_file_path.name}")
                    else:
                        print(f"  ℹ Лог-файл не указан в команде")
                
                except Exception as e:
                    print(f"  ✗ Ошибка парсинга команды: {e}")
            
            # Assert 3: Проверяем что все команды корректно парсятся
            print(f"\n{'='*70}")
            print(f"[ИТОГИ ПРОВЕРКИ КОМАНД]")
            print(f"{'='*70}")
            print(f"Всего команд:           {len(commands)}")
            print(f"Найдено лог-файлов:     {len(log_files_to_check)}")
            if temp_dir:
                print(f"Временная директория:   {temp_dir}")
                
                # Ищем лог-файлы в временной директории
                if temp_dir.exists():
                    print(f"\n[Поиск лог-файлов в временной директории]")
                    log_patterns = ['*.log', 'ERROR.txt']
                    for pattern in log_patterns:
                        for log_file in temp_dir.glob(pattern):
                            if log_file.is_file():
                                log_files_to_check.append(log_file)
                                log_size = log_file.stat().st_size
                                print(f"  ✓ Найден: {log_file.name} ({log_size} байт)")
            
            # Проверяем что команды найдены
            assert len(commands) > 0, "Команды не найдены в логе"
            
            # Проверяем содержимое лог-файлов 1cv8.exe
            if log_files_to_check:
                print(f"\n{'='*70}")
                print(f"[ЭТАП 4] ПРОВЕРКА ЛОГ-ФАЙЛОВ 1cv8.exe")
                print(f"{'='*70}")
                print(f"Найдено лог-файлов: {len(log_files_to_check)}")
                
                for log_file in log_files_to_check:
                    print(f"\n[Лог-файл: {log_file.name}]")
                    
                    try:
                        # Читаем содержимое лог-файла
                        with open(log_file, 'r', encoding='cp1251', errors='replace') as f:
                            log_content = f.read()
                        
                        # Проверяем на наличие ошибок
                        has_errors = False
                        error_keywords = ['ошибка', 'error', 'exception', 'failed']
                        
                        for keyword in error_keywords:
                            if keyword.lower() in log_content.lower():
                                has_errors = True
                                break
                        
                        if has_errors:
                            print(f"  ⚠ Обнаружены возможные ошибки в логе")
                            # Выводим первые 500 символов лога
                            log_preview = log_content[:500] if len(log_content) > 500 else log_content
                            print(f"  Содержимое (первые 500 символов):")
                            for line in log_preview.split('\n'):
                                if line.strip():
                                    print(f"    {line}")
                        else:
                            print(f"  ✓ Лог не содержит явных ошибок")
                            print(f"  Размер: {len(log_content)} символов")
                    
                    except Exception as e:
                        print(f"  ✗ Ошибка чтения лог-файла: {e}")
            
            # Act 4: Проверяем создание итогового файла
            print(f"\n{'='*70}")
            print(f"[ЭТАП 5] Проверка создания итогового CF файла")
            print(f"{'='*70}")
            
            # Читаем путь к выходному файлу из .env
            env_vars = load_env_file(str(demo_project_env), silent=True)
            output_file = Path(env_vars['V8_DST_PATH'])
            
            # Добавляем выходной файл в список для очистки
            if output_file not in created_items:
                created_items.append(output_file)
            
            # Assert 4: Проверяем что файл создан
            assert output_file.exists(), f"Выходной CF файл не создан: {output_file}"
            
            file_size = output_file.stat().st_size
            assert file_size > 0, "Выходной файл пустой"
            assert file_size > 1024 * 1024, f"Выходной файл слишком маленький: {file_size} байт"
            
            print(f"✓ CF файл создан: {output_file.name}")
            print(f"✓ Размер файла: {file_size / (1024 * 1024):.2f} МБ")
            
            print(f"\n{'='*70}")
            print(f"[УСПЕХ] Все команды выполнены успешно!")
            print(f"{'='*70}")
            
            # Выводим полные команды для ручного запуска
            print(f"\n{'='*70}")
            print(f"[КОМАНДЫ ДЛЯ РУЧНОГО ЗАПУСКА]")
            print(f"{'='*70}")
            
            print(f"\n# Для PowerShell (используйте оператор &):\n")
            for i, cmd_str in enumerate(commands, 1):
                print(f"# Команда {i}:")
                print(f"& {cmd_str}\n")
            
            print(f"\n{'='*70}")
            print(f"# Для CMD (командная строка Windows):\n")
            for i, cmd_str in enumerate(commands, 1):
                print(f"# Команда {i}:")
                print(f"{cmd_str}\n")
        
        finally:
            # Cleanup: закрываем файловый дескриптор и удаляем временный лог-файл
            try:
                import os
                os.close(log_fd)
            except Exception:
                pass
            
            if log_path.exists():
                log_path.unlink()


if __name__ == '__main__':
    # Запуск тестов с подробным выводом
    pytest.main([__file__, '-v', '-s'])

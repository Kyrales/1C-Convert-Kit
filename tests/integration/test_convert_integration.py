#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Интеграционные тесты для конвертации 1С проектов
Тестируют полный цикл конвертации с реальными инструментами 1С
"""

import os
import sys
import pytest
import shutil
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from core.convert import run_conversion, load_env_file, merge_env_files


class TestConversionIntegration:
    """Интеграционные тесты конвертации"""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Подготовка и очистка для каждого теста"""
        # Подготовка: создаем выходную директорию
        self.output_dir = project_root / 'tests' / 'fixtures' / 'output'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Выполняем тест
        yield
        
        # Очистка: удаляем выходную директорию со всем содержимым
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
    
    def test_conf2cf_conversion(self):
        """
        Тест конвертации EDT конфигурации в CF файл
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание выходного .cf файла
        - Размер файла больше 0
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_conf2cf.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного EDT проекта
        src_path = project_root / 'tests' / 'fixtures' / 'cf' / 'otusJenkinsExampleEDT'
        assert src_path.exists(), f"Исходный EDT проект не найден: {src_path}"
        assert (src_path / '.project').exists(), "Файл .project не найден в EDT проекте"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание выходного файла
        output_file = project_root / 'tests' / 'fixtures' / 'output' / 'otusJenkinsExampleEDT.cf'
        assert output_file.exists(), f"Выходной .cf файл не создан: {output_file}"
        
        # Проверяем размер файла
        file_size = output_file.stat().st_size
        assert file_size > 0, "Выходной файл пустой"
        assert file_size > 1024, f"Выходной файл слишком маленький: {file_size} байт"
        
        print(f"\n[OK] Конфигурация успешно сконвертирована")
        print(f"[OK] Размер файла: {file_size / (1024 * 1024):.2f} МБ")
    
    def test_ext2cfe_conversion(self):
        """
        Тест конвертации EDT расширения в CFE файл
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание выходного .cfe файла
        - Размер файла больше 0
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_ext2cfe.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного EDT проекта расширения
        src_path = project_root / 'tests' / 'fixtures' / 'cfe' / 'otusJenkinsExampleEDT.Колонтитулы'
        assert src_path.exists(), f"Исходный EDT проект расширения не найден: {src_path}"
        assert (src_path / '.project').exists(), "Файл .project не найден в EDT проекте расширения"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание выходного файла
        output_file = project_root / 'tests' / 'fixtures' / 'output' / 'otusJenkinsExampleEDT.Колонтитулы.cfe'
        assert output_file.exists(), f"Выходной .cfe файл не создан: {output_file}"
        
        # Проверяем размер файла
        file_size = output_file.stat().st_size
        assert file_size > 0, "Выходной файл пустой"
        assert file_size > 512, f"Выходной файл слишком маленький: {file_size} байт"
        
        print(f"\n[OK] Расширение успешно сконвертировано")
        print(f"[OK] Размер файла: {file_size / 1024:.2f} КБ")
    
    def test_env_files_loading(self):
        """
        Тест загрузки и объединения .env файлов
        
        Проверяет:
        - Корректную загрузку базового .env
        - Корректную загрузку проектного .env
        - Правильное объединение параметров
        - Переопределение параметров из проектного .env
        """
        # Arrange
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_conf2cf.env'
        
        # Act: загружаем файлы
        base_vars = load_env_file(str(base_env), silent=True)
        project_vars = load_env_file(str(project_env), silent=True)
        
        # Assert: проверяем базовый .env
        assert base_vars is not None, "Не удалось загрузить базовый .env"
        assert 'V8_TOOL' in base_vars, "V8_TOOL не найден в базовом .env"
        assert 'EDTCLI_TOOL' in base_vars, "EDTCLI_TOOL не найден в базовом .env"
        assert 'V8_TEMP' in base_vars, "V8_TEMP не найден в базовом .env"
        
        # Assert: проверяем проектный .env
        assert project_vars is not None, "Не удалось загрузить проектный .env"
        assert 'ScriptName' in project_vars, "ScriptName не найден в проектном .env"
        assert 'V8_SRC_PATH' in project_vars, "V8_SRC_PATH не найден в проектном .env"
        assert 'V8_DST_PATH' in project_vars, "V8_DST_PATH не найден в проектном .env"
        
        # Act: объединяем файлы
        merged_vars = merge_env_files([str(base_env), str(project_env)], silent=True)
        
        # Assert: проверяем объединение
        assert merged_vars is not None, "Не удалось объединить .env файлы"
        assert 'V8_TOOL' in merged_vars, "V8_TOOL потерян при объединении"
        assert 'ScriptName' in merged_vars, "ScriptName потерян при объединении"
        assert merged_vars['ScriptName'] == 'conf2cf', "Неверное значение ScriptName"
        
        print(f"\n[OK] Загружено параметров из базового .env: {len(base_vars)}")
        print(f"[OK] Загружено параметров из проектного .env: {len(project_vars)}")
        print(f"[OK] Всего параметров после объединения: {len(merged_vars)}")
    
    def test_dp2epf_conversion(self):
        """
        Тест конвертации EDT обработки в EPF файл
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание выходного .epf файла
        - Размер файла больше 0
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_dp2epf.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного EDT проекта обработки
        src_path = project_root / 'tests' / 'fixtures' / 'epf' / 'ТестоваяОбработка'
        assert src_path.exists(), f"Исходный EDT проект обработки не найден: {src_path}"
        assert (src_path / '.project').exists(), "Файл .project не найден в EDT проекте обработки"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание выходного файла
        output_file = project_root / 'tests' / 'fixtures' / 'output' / 'ТестоваяОбработка.epf'
        assert output_file.exists(), f"Выходной .epf файл не создан: {output_file}"
        
        # Проверяем размер файла
        file_size = output_file.stat().st_size
        assert file_size > 0, "Выходной файл пустой"
        assert file_size > 512, f"Выходной файл слишком маленький: {file_size} байт"
        
        print(f"\n[OK] Обработка успешно сконвертирована")
        print(f"[OK] Размер файла: {file_size / 1024:.2f} КБ")
    
    def test_dp2epf_env_config(self):
        """
        Тест конфигурации .env файла для конвертации обработки
        
        Проверяет:
        - Корректность параметров в test_dp2epf.env
        - Наличие исходного EDT проекта
        - Правильность путей
        """
        # Arrange
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_dp2epf.env'
        
        # Act: загружаем и объединяем .env файлы
        merged_vars = merge_env_files([str(base_env), str(project_env)], silent=True)
        
        # Assert: проверяем параметры
        assert merged_vars is not None, "Не удалось загрузить .env файлы"
        assert merged_vars['ScriptName'] == 'dp2epf', "Неверный ScriptName"
        assert 'V8_SRC_PATH' in merged_vars, "V8_SRC_PATH не найден"
        assert 'V8_DST_PATH' in merged_vars, "V8_DST_PATH не найден"
        
        # Проверяем исходный путь
        src_path = project_root / merged_vars['V8_SRC_PATH']
        assert src_path.exists(), f"Исходный путь не существует: {src_path}"
        assert (src_path / '.project').exists(), "Файл .project не найден"
        assert (src_path / 'DT-INF').exists(), "Папка DT-INF не найдена"
        assert (src_path / 'src').exists(), "Папка src не найдена"
        
        print(f"\n[OK] Конфигурация .env корректна")
        print(f"[OK] ScriptName: {merged_vars['ScriptName']}")
        print(f"[OK] Исходный путь: {merged_vars['V8_SRC_PATH']}")
        print(f"[OK] Выходной путь: {merged_vars['V8_DST_PATH']}")
    
    def test_conf2xml_conversion(self):
        """
        Тест конвертации CF конфигурации в XML формат
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание XML файлов
        - Наличие Configuration.xml
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_conf2xml.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного CF файла
        src_path = project_root / 'tests' / 'fixtures' / 'edt_xml' / 'demo_otus_edt.cf'
        assert src_path.exists(), f"Исходный CF файл не найден: {src_path}"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание XML файлов
        output_dir = project_root / 'tests' / 'fixtures' / 'output' / 'demo_otus_edt'
        assert output_dir.exists(), f"Выходная директория не создана: {output_dir}"
        
        config_xml = output_dir / 'Configuration.xml'
        assert config_xml.exists(), f"Файл Configuration.xml не создан: {config_xml}"
        
        # Проверяем размер файла
        file_size = config_xml.stat().st_size
        assert file_size > 0, "Файл Configuration.xml пустой"
        
        print(f"\n[OK] Конфигурация успешно сконвертирована в XML")
        print(f"[OK] Размер Configuration.xml: {file_size / 1024:.2f} КБ")
    
    def test_conf2edt_conversion(self):
        """
        Тест конвертации CF конфигурации в EDT проект
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание EDT проекта
        - Наличие .project файла
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_conf2edt.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного CF файла
        src_path = project_root / 'tests' / 'fixtures' / 'edt_xml' / 'demo_otus_edt.cf'
        assert src_path.exists(), f"Исходный CF файл не найден: {src_path}"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание EDT проекта
        output_dir = project_root / 'tests' / 'fixtures' / 'output' / 'demo_otus_edt'
        assert output_dir.exists(), f"Выходная директория не создана: {output_dir}"
        
        project_file = output_dir / '.project'
        assert project_file.exists(), f"Файл .project не создан: {project_file}"
        
        dt_inf = output_dir / 'DT-INF'
        assert dt_inf.exists(), f"Папка DT-INF не создана: {dt_inf}"
        
        src_dir = output_dir / 'src'
        assert src_dir.exists(), f"Папка src не создана: {src_dir}"
        
        print(f"\n[OK] Конфигурация успешно сконвертирована в EDT")
        print(f"[OK] EDT проект создан: {output_dir.name}")
    
    def test_ext2xml_conversion(self):
        """
        Тест конвертации CFE расширения в XML формат
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание XML файлов
        - Наличие Configuration.xml
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_ext2xml.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного CFE файла
        src_path = project_root / 'tests' / 'fixtures' / 'edt_xml' / 'otusJenkinsExampleEDT.Колонтитулы.cfe'
        assert src_path.exists(), f"Исходный CFE файл не найден: {src_path}"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание XML файлов
        output_dir = project_root / 'tests' / 'fixtures' / 'output' / 'otusJenkinsExampleEDT.Колонтитулы'
        assert output_dir.exists(), f"Выходная директория не создана: {output_dir}"
        
        config_xml = output_dir / 'Configuration.xml'
        assert config_xml.exists(), f"Файл Configuration.xml не создан: {config_xml}"
        
        # Проверяем размер файла
        file_size = config_xml.stat().st_size
        assert file_size > 0, "Файл Configuration.xml пустой"
        
        print(f"\n[OK] Расширение успешно сконвертировано в XML")
        print(f"[OK] Размер Configuration.xml: {file_size / 1024:.2f} КБ")
    
    def test_ext2edt_conversion(self):
        """
        Тест конвертации CFE расширения в EDT проект
        
        Проверяет:
        - Успешное выполнение конвертации
        - Создание EDT проекта
        - Наличие .project файла
        """
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_ext2edt.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Проверяем наличие исходного CFE файла
        src_path = project_root / 'tests' / 'fixtures' / 'edt_xml' / 'otusJenkinsExampleEDT.Колонтитулы.cfe'
        assert src_path.exists(), f"Исходный CFE файл не найден: {src_path}"
        
        # Act: выполняем конвертацию
        env_files = [str(base_env), str(project_env)]
        exit_code = run_conversion(env_files)
        
        # Assert: проверяем результат
        assert exit_code == 0, "Конвертация завершилась с ошибкой"
        
        # Проверяем создание EDT проекта
        output_dir = project_root / 'tests' / 'fixtures' / 'output' / 'otusJenkinsExampleEDT.Колонтитулы'
        assert output_dir.exists(), f"Выходная директория не создана: {output_dir}"
        
        project_file = output_dir / '.project'
        assert project_file.exists(), f"Файл .project не создан: {project_file}"
        
        dt_inf = output_dir / 'DT-INF'
        assert dt_inf.exists(), f"Папка DT-INF не создана: {dt_inf}"
        
        src_dir = output_dir / 'src'
        assert src_dir.exists(), f"Папка src не создана: {src_dir}"
        
        print(f"\n[OK] Расширение успешно сконвертировано в EDT")
        print(f"[OK] EDT проект создан: {output_dir.name}")
    
    def test_subprocess_encoding(self):
        """
        Тест запуска конвертации через subprocess с проверкой кодировки вывода
        
        Проверяет:
        - Успешный запуск через subprocess (как в GUI)
        - Корректную декодировку вывода в различных кодировках (UTF-8, CP1251, CP866)
        - Отсутствие ошибок кодирования Unicode символов
        - Что все логи корректно выводятся без исключений
        """
        import subprocess
        
        # Arrange: подготовка путей к .env файлам
        base_env = project_root / 'tests' / 'fixtures' / 'base_test.env'
        project_env = project_root / 'tests' / 'fixtures' / 'test_dp2epf.env'
        
        # Проверяем наличие исходных файлов
        assert base_env.exists(), f"Базовый .env не найден: {base_env}"
        assert project_env.exists(), f"Проектный .env не найден: {project_env}"
        
        # Формируем команду для запуска через subprocess
        # Передаем конкретный .env файл, а не папку
        convert_script = project_root / 'src' / 'core' / 'convert.py'
        
        cmd = [
            sys.executable,
            str(convert_script),
            '--env',
            str(project_env)  # Передаем путь к конкретному .env файлу
        ]
        
        # Act: запускаем процесс с перехватом вывода
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(project_root)
        )
        
        # Читаем вывод построчно с обработкой разных кодировок
        output_lines = []
        encoding_errors = []
        
        for line in iter(process.stdout.readline, b''):
            if not line:
                break
            
            # Пробуем декодировать в разных кодировках (как в GUI)
            decoded_line = None
            for encoding in ['utf-8', 'cp1251', 'cp866', 'latin-1']:
                try:
                    decoded_line = line.decode(encoding)
                    break
                except (UnicodeDecodeError, AttributeError):
                    continue
            
            # Если не удалось декодировать, используем замену ошибочных символов
            if decoded_line is None:
                try:
                    decoded_line = line.decode('utf-8', errors='replace')
                except Exception as e:
                    encoding_errors.append(f"Ошибка декодирования: {e}")
                    continue
            
            output_lines.append(decoded_line.strip())
        
        process.wait()
        
        # Assert: проверяем результат
        assert process.returncode == 0, f"Конвертация завершилась с ошибкой (код: {process.returncode})"
        
        # Проверяем что не было ошибок кодирования
        assert len(encoding_errors) == 0, f"Обнаружены ошибки кодирования: {encoding_errors}"
        
        # Проверяем что вывод не пустой
        assert len(output_lines) > 0, "Вывод процесса пустой"
        
        # Проверяем что в выводе есть ключевые сообщения
        output_text = '\n'.join(output_lines)
        
        # Выводим лог для отладки
        print(f"\n[DEBUG] Вывод процесса ({len(output_lines)} строк):")
        for line in output_lines[:20]:  # Первые 20 строк
            print(f"  {line}")
        if len(output_lines) > 20:
            print(f"  ... (еще {len(output_lines) - 20} строк)")
        
        assert 'Начало конвертации' in output_text or 'ИНФО' in output_text or 'INFO' in output_text, \
            "В выводе отсутствуют ожидаемые сообщения о конвертации"
        
        # Проверяем что нет сообщений об ошибках кодировки
        assert 'charmap' not in output_text.lower(), \
            "Обнаружена ошибка кодировки charmap в выводе"
        assert "can't encode" not in output_text.lower(), \
            "Обнаружена ошибка 'can't encode' в выводе"
        
        # Проверяем создание выходного файла
        output_file = project_root / 'tests' / 'fixtures' / 'output' / 'ТестоваяОбработка.epf'
        
        # Если файл не создан, выводим последние строки лога для диагностики
        if not output_file.exists():
            print(f"\n[DEBUG] Файл не создан. Последние 10 строк вывода:")
            for line in output_lines[-10:]:
                print(f"  {line}")
        
        assert output_file.exists(), f"Выходной .epf файл не создан: {output_file}"
        
        print(f"\n[OK] Конвертация через subprocess выполнена успешно")
        print(f"[OK] Обработано строк вывода: {len(output_lines)}")
        print(f"[OK] Ошибок кодирования: {len(encoding_errors)}")
        print(f"[OK] Выходной файл создан: {output_file.name}")
    
    def test_source_projects_exist(self):
        """
        Тест проверки наличия исходных тестовых проектов
        
        Проверяет:
        - Наличие EDT проекта конфигурации
        - Наличие EDT проекта расширения
        - Наличие EDT проекта обработки
        - Наличие CF файла конфигурации
        - Наличие CFE файла расширения
        - Корректную структуру проектов
        """
        # Проверяем конфигурацию (EDT)
        conf_project = project_root / 'tests' / 'fixtures' / 'cf' / 'otusJenkinsExampleEDT'
        assert conf_project.exists(), f"EDT проект конфигурации не найден: {conf_project}"
        assert (conf_project / '.project').exists(), "Файл .project не найден в конфигурации"
        assert (conf_project / 'src').exists(), "Папка src не найдена в конфигурации"
        assert (conf_project / 'DT-INF').exists(), "Папка DT-INF не найдена в конфигурации"
        
        # Проверяем расширение (EDT)
        ext_project = project_root / 'tests' / 'fixtures' / 'cfe' / 'otusJenkinsExampleEDT.Колонтитулы'
        assert ext_project.exists(), f"EDT проект расширения не найден: {ext_project}"
        assert (ext_project / '.project').exists(), "Файл .project не найден в расширении"
        assert (ext_project / 'src').exists(), "Папка src не найдена в расширении"
        assert (ext_project / 'DT-INF').exists(), "Папка DT-INF не найдена в расширении"
        
        # Проверяем обработку (EDT)
        dp_project = project_root / 'tests' / 'fixtures' / 'epf' / 'ТестоваяОбработка'
        assert dp_project.exists(), f"EDT проект обработки не найден: {dp_project}"
        assert (dp_project / '.project').exists(), "Файл .project не найден в обработке"
        assert (dp_project / 'src').exists(), "Папка src не найдена в обработке"
        assert (dp_project / 'DT-INF').exists(), "Папка DT-INF не найдена в обработке"
        
        # Проверяем конфигурацию (CF)
        conf_cf = project_root / 'tests' / 'fixtures' / 'edt_xml' / 'demo_otus_edt.cf'
        assert conf_cf.exists(), f"CF файл конфигурации не найден: {conf_cf}"
        assert conf_cf.stat().st_size > 0, "CF файл конфигурации пустой"
        
        # Проверяем расширение (CFE)
        ext_cfe = project_root / 'tests' / 'fixtures' / 'edt_xml' / 'otusJenkinsExampleEDT.Колонтитулы.cfe'
        assert ext_cfe.exists(), f"CFE файл расширения не найден: {ext_cfe}"
        assert ext_cfe.stat().st_size > 0, "CFE файл расширения пустой"
        
        print(f"\n[OK] EDT проект конфигурации найден: {conf_project.name}")
        print(f"[OK] EDT проект расширения найден: {ext_project.name}")
        print(f"[OK] EDT проект обработки найден: {dp_project.name}")
        print(f"[OK] CF файл конфигурации найден: {conf_cf.name}")
        print(f"[OK] CFE файл расширения найден: {ext_cfe.name}")


if __name__ == '__main__':
    # Запуск тестов с подробным выводом
    pytest.main([__file__, '-v', '-s'])

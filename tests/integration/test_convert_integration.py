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
        
        print(f"\n✓ Конфигурация успешно сконвертирована")
        print(f"✓ Размер файла: {file_size / (1024 * 1024):.2f} МБ")
    
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
        
        print(f"\n✓ Расширение успешно сконвертировано")
        print(f"✓ Размер файла: {file_size / 1024:.2f} КБ")
    
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
        assert merged_vars['ScriptName'] == 'conf2cf.cmd', "Неверное значение ScriptName"
        
        print(f"\n✓ Загружено параметров из базового .env: {len(base_vars)}")
        print(f"✓ Загружено параметров из проектного .env: {len(project_vars)}")
        print(f"✓ Всего параметров после объединения: {len(merged_vars)}")
    
    def test_source_projects_exist(self):
        """
        Тест проверки наличия исходных тестовых проектов
        
        Проверяет:
        - Наличие EDT проекта конфигурации
        - Наличие EDT проекта расширения
        - Корректную структуру проектов
        """
        # Проверяем конфигурацию
        conf_project = project_root / 'tests' / 'fixtures' / 'cf' / 'otusJenkinsExampleEDT'
        assert conf_project.exists(), f"EDT проект конфигурации не найден: {conf_project}"
        assert (conf_project / '.project').exists(), "Файл .project не найден в конфигурации"
        assert (conf_project / 'src').exists(), "Папка src не найдена в конфигурации"
        assert (conf_project / 'DT-INF').exists(), "Папка DT-INF не найдена в конфигурации"
        
        # Проверяем расширение
        ext_project = project_root / 'tests' / 'fixtures' / 'cfe' / 'otusJenkinsExampleEDT.Колонтитулы'
        assert ext_project.exists(), f"EDT проект расширения не найден: {ext_project}"
        assert (ext_project / '.project').exists(), "Файл .project не найден в расширении"
        assert (ext_project / 'src').exists(), "Папка src не найдена в расширении"
        assert (ext_project / 'DT-INF').exists(), "Папка DT-INF не найдена в расширении"
        
        print(f"\n✓ EDT проект конфигурации найден: {conf_project.name}")
        print(f"✓ EDT проект расширения найден: {ext_project.name}")


if __name__ == '__main__':
    # Запуск тестов с подробным выводом
    pytest.main([__file__, '-v', '-s'])

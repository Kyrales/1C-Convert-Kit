"""
Конвертер для валидации EDT проектов 1С.

Поддерживает валидацию EDT проектов с использованием EDT инструментов
(ring или 1cedtcli). Принимает на вход только EDT проекты.

Для конвертации других форматов в EDT используйте соответствующие конвертеры:
- conf2edt - для конфигураций (CF, XML, IB)
- ext2edt - для расширений (CFE, XML, IB)
- dp2edt - для обработок и отчетов (EPF, ERF, XML)
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Optional, Callable, Tuple

from ..base.converter import (
    BaseConverter,
    SourceType,
    ValidationError,
    ToolNotFoundError
)
from ..base.tools import format_command_for_log


class ValidationConverter(BaseConverter):
    """
    Конвертер для валидации EDT проектов 1С.
    
    Выполняет валидацию EDT проектов с использованием EDT инструментов
    (ring или 1cedtcli). Принимает на вход только EDT проекты.
    
    Параметры из .env:
        V8_SRC_PATH: Путь к EDT проекту (обязательно)
        V8_DST_PATH: Путь к отчету валидации или каталогу для отчета (обязательно)
        V8_EDT_VERSION: Версия EDT (опционально, по умолчанию 2024.2)
        EDTCLI_TOOL: Путь к 1cedtcli.exe (опционально)
    
    Args:
        env_vars: Словарь переменных окружения из .env файлов
        silent: Если True, подавляет вывод в консоль
        progress_callback: Опциональный callback для отчета о прогрессе
        debug: Если True, выводит отладочную информацию
    """
    
    def __init__(
        self, 
        env_vars: Dict[str, str], 
        silent: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        debug: bool = False
    ):
        super().__init__(env_vars, silent, progress_callback, debug)
    
    def get_output_extension(self) -> str:
        """
        Возвращает расширение выходного файла.
        
        Returns:
            str: '.txt' (отчет валидации в текстовом формате TSV)
        """
        return '.txt'
    
    def validate(self) -> None:
        """
        Валидирует параметры конвертации.
        
        Проверяет что источник является EDT проектом и указан путь к отчету.
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Проверка обязательных параметров
        if not self.src_path:
            raise ValidationError("Не указан параметр V8_SRC_PATH (путь к EDT проекту)")
        
        if not self.dst_path:
            raise ValidationError(
                "Не указан параметр V8_DST_PATH (путь к отчету валидации или каталогу)"
            )
        
        # Проверка существования источника
        src_path_obj = Path(self.src_path)
        if not src_path_obj.exists():
            raise ValidationError(f"Источник не найден: {self.src_path}")
        
        # Специфичная валидация конвертера
        self._validate_specific()
    
    def _validate_specific(self) -> None:
        """
        Специфичная валидация для конвертера валидации.
        
        Проверяет:
        - Что источник является EDT проектом
        - Что EDT проект имеет корректную структуру
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Проверка что источник - это EDT проект
        source_type = self.detect_source_type()
        if source_type != SourceType.EDT:
            raise ValidationError(
                f"ValidationConverter работает только с EDT проектами.\n" +
                f"Обнаружен тип источника: {source_type.value}\n" +
                f"Для конвертации других форматов в EDT используйте:\n" +
                f"  - conf2edt - для конфигураций (CF, XML, IB)\n" +
                f"  - ext2edt - для расширений (CFE, XML, IB)\n" +
                f"  - dp2edt - для обработок и отчетов (EPF, ERF, XML)"
            )
        
        # Проверяем что EDT проект существует и имеет правильную структуру
        src_path_obj = Path(self.src_path)
        dt_inf_dir = src_path_obj / 'DT-INF'
        
        if not dt_inf_dir.exists():
            raise ValidationError(
                f"EDT проект не содержит директорию DT-INF: {self.src_path}"
            )
        
        self.log_info(f"EDT проект найден: {self.src_path}")
    
    def _get_report_path(self) -> Path:
        """
        Определяет путь к файлу отчета валидации.
        
        Если V8_DST_PATH указывает на каталог - создаем файл validation_report.txt
        Если V8_DST_PATH указывает на файл - используем как есть
        
        Returns:
            Path: Путь к файлу отчета
        """
        dst = Path(self.dst_path)
        
        # Если есть расширение - это файл
        if dst.suffix:
            dst.parent.mkdir(parents=True, exist_ok=True)
            return dst
        
        # Нет расширения - это каталог
        dst.mkdir(parents=True, exist_ok=True)
        return dst / 'validation_report.txt'
    
    def _find_edt_tool(self) -> Tuple[str, str]:
        """
        Находит EDT инструмент (ring или 1cedtcli).
        
        Порядок поиска:
        1. Переменная EDTCLI_TOOL из env (приоритет)
        2. Автопоиск 1cedtcli.exe в Program Files
        3. Переменная RING_TOOL из env
        4. ring в PATH
        
        Returns:
            Tuple[str, str]: (tool_type, tool_path)
                tool_type: 'ring' или 'edtcli'
                tool_path: полный путь к инструменту
        
        Raises:
            ToolNotFoundError: Если инструменты не найдены
        """
        # 1. Проверяем EDTCLI_TOOL из env (приоритет!)
        edtcli_tool = self.env_vars.get('EDTCLI_TOOL')
        if edtcli_tool:
            edtcli_path = Path(edtcli_tool)
            if edtcli_path.exists():
                self.log_info(f"Используется EDTCLI_TOOL из переменной окружения")
                return ('edtcli', str(edtcli_path))
        
        # 2. Ищем 1cedtcli.exe автоматически
        edt_version = self.env_vars.get('V8_EDT_VERSION', '')
        program_files = os.environ.get('PROGRAMW6432', 'C:\\Program Files')
        edt_base = Path(program_files) / '1C' / '1CE' / 'components'
        
        if edt_base.exists():
            # Формируем паттерн поиска
            if edt_version:
                # Проверяем версию - если >= 2024, используем новый формат
                try:
                    version_year = int(edt_version.split('.')[0])
                    if version_year >= 2024:
                        pattern = f'1c-edt-{edt_version}*'
                    else:
                        pattern = f'1c-edt-{edt_version}*'
                except (ValueError, IndexError):
                    pattern = f'1c-edt-{edt_version}*'
            else:
                pattern = '1c-edt-*'
            
            # Ищем подходящую версию (сортируем в обратном порядке для выбора новейшей)
            matching_dirs = sorted(edt_base.glob(pattern), reverse=True)
            for edt_dir in matching_dirs:
                edtcli = edt_dir / '1cedtcli.exe'
                if edtcli.exists():
                    self.log_info(f"Найден 1cedtcli.exe: {edt_dir.name}")
                    return ('edtcli', str(edtcli))
        
        # 3. Проверяем RING_TOOL из env
        ring_tool = self.env_vars.get('RING_TOOL')
        if ring_tool:
            ring_path = Path(ring_tool)
            if ring_path.exists():
                self.log_info(f"Используется RING_TOOL из переменной окружения")
                return ('ring', str(ring_path))
        
        # 4. Ищем ring в PATH (последний приоритет)
        try:
            result = subprocess.run(
                ['where', 'ring'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                ring_path = result.stdout.strip().split('\n')[0]
                self.log_info(f"Найден ring в PATH")
                return ('ring', ring_path)
        except Exception:
            pass
        
        # Не найдено ни одного инструмента
        raise ToolNotFoundError(
            "EDT инструмент не найден.\n" +
            "Установите ring или 1C:EDT, либо укажите путь в переменных:\n" +
            "  - EDTCLI_TOOL - путь к 1cedtcli.exe (рекомендуется)\n" +
            "  - RING_TOOL - путь к ring.bat"
        )
    
    def _parse_validation_report(self, report_path: Path) -> None:
        """
        Парсит отчет валидации и выводит статистику.
        
        Отчет в текстовом формате (TSV) содержит список проблем с уровнями severity.
        Формат: Дата\tУровень\tКатегория\tПроект\tПравило\tОбъект\tСтрока\tОписание
        
        Args:
            report_path: Путь к файлу отчета
        """
        try:
            if not report_path.exists():
                self.log_warning("Файл отчета не найден")
                return
            
            # Читаем отчет
            with open(report_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if not lines:
                self.log_success("Проблем не найдено")
                return
            
            # Подсчитываем проблемы по уровням и собираем критические замечания
            # Уровни: Критическая, Значительная, Незначительная, Тривиальная
            critical = 0
            major = 0
            minor = 0
            trivial = 0
            critical_issues = []  # Список критических замечаний
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Парсим TSV строку
                parts = line.split('\t')
                if len(parts) < 2:
                    continue
                
                severity = parts[1].strip().lower()
                
                if 'критическая' in severity or 'critical' in severity:
                    critical += 1
                    # Сохраняем критическое замечание для вывода
                    if len(parts) >= 8:
                        # Формат: Дата\tУровень\tКатегория\tПроект\tПравило\tОбъект\tСтрока\tОписание
                        obj = parts[5].strip()
                        line_num = parts[6].strip()
                        description = parts[7].strip()
                        critical_issues.append(f"{obj} ({line_num}): {description}")
                elif 'значительная' in severity or 'major' in severity:
                    major += 1
                elif 'незначительная' in severity or 'minor' in severity:
                    minor += 1
                elif 'тривиальная' in severity or 'trivial' in severity:
                    trivial += 1
            
            # Выводим статистику
            total = critical + major + minor + trivial
            
            if total == 0:
                self.log_success("Проблем не найдено")
            else:
                self.log_info(f"Найдено проблем: {total}")
                if critical > 0:
                    self.log_info(f"  Критических: {critical}")
                if major > 0:
                    self.log_info(f"  Значительных: {major}")
                if minor > 0:
                    self.log_info(f"  Незначительных: {minor}")
                if trivial > 0:
                    self.log_info(f"  Тривиальных: {trivial}")
                
                # Выводим критические замечания
                if critical_issues:
                    self.log_info("")
                    self.log_info("Критические замечания:")
                    for i, issue in enumerate(critical_issues[:10], 1):  # Первые 10
                        self.log_info(f"  {i}. {issue}")
                    if len(critical_issues) > 10:
                        self.log_info(f"  ... и еще {len(critical_issues) - 10} критических замечаний")
                    
        except Exception as e:
            self.log_warning(f"Ошибка при чтении отчета: {e}")
    
    def _do_convert(self) -> int:
        """
        Выполняет валидацию EDT проекта.
        
        Использует EDT инструменты (ring или 1cedtcli) для проверки корректности проекта.
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Валидация EDT проекта")
        self.report_progress("Валидация EDT проекта", 0)
        
        try:
            # 1. Определяем путь к отчету
            report_path = self._get_report_path()
            self.log_info(f"Отчет валидации: {report_path}")
            self.report_progress("Подготовка", 10)
            
            # 2. Создаем временный workspace
            if self.temp_dir is None:
                raise ValidationError("Временная директория не инициализирована")
            
            workspace_path = self.temp_dir / 'edt_ws'
            workspace_path.mkdir(exist_ok=True)
            self.log_info(f"Workspace: {workspace_path}")
            
            # 3. Проверяем структуру EDT проекта
            edt_project = Path(self.src_path)
            self._validate_edt_structure(edt_project)
            self.report_progress("Структура проверена", 20)
            
            # 4. Находим EDT инструмент
            tool_type, tool_path = self._find_edt_tool()
            self.log_info(f"Используется инструмент: {tool_type}")
            self.report_progress("Инструмент найден", 30)
            
            # 5. Формируем команду
            if tool_type == 'ring':
                edt_version = self.env_vars.get('V8_EDT_VERSION', '2024.2')
                cmd = [
                    tool_path,
                    f'edt@{edt_version}',
                    'workspace', 'validate',
                    '--project-list', str(edt_project),
                    '--workspace-location', str(workspace_path),
                    '--file', str(report_path)
                ]
            else:  # edtcli
                cmd = [
                    tool_path,
                    '-data', str(workspace_path),
                    '-command', 'validate',
                    '--project-list', str(edt_project),
                    '--file', str(report_path)
                ]
            
            # 6. Запускаем валидацию
            self.log_info("Запуск валидации EDT проекта...")
            self.report_progress("Выполнение валидации", 40)
            
            # Выводим команду в режиме отладки
            if self.debug:
                cmd_str = format_command_for_log(cmd)
                self.logger.debug_msg(f"Команда: {cmd_str}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            self.report_progress("Валидация завершена", 80)
            
            # 7. Обрабатываем результат
            if result.returncode == 0:
                self.log_success("Валидация завершена успешно")
                self.log_info(f"Отчет сохранен: {report_path}")
                
                # Парсим отчет и выводим статистику
                self._parse_validation_report(report_path)
                
                self.report_progress("Готово", 100)
                return 0
            else:
                self.log_error(f"Валидация завершилась с ошибкой (код: {result.returncode})")
                
                # Выводим stderr если есть
                if result.stderr:
                    stderr_lines = result.stderr.strip().split('\n')
                    for line in stderr_lines[:10]:  # Первые 10 строк
                        if line.strip():
                            self.log_error(f"  {line}")
                
                # Пытаемся распарсить отчет даже при ошибке
                if report_path.exists():
                    self._parse_validation_report(report_path)
                
                if self.temp_manager:
                    self.temp_manager.preserve_on_error()
                
                return 1
                
        except Exception as e:
            self.log_error(f"Ошибка при валидации EDT проекта: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise
    
    def _validate_edt_structure(self, edt_project: Path) -> None:
        """
        Проверяет базовую структуру EDT проекта.
        
        Это временная реализация, которая проверяет наличие обязательных
        директорий и файлов в EDT проекте.
        
        Поддерживает две структуры EDT проектов:
        1. Старая структура: метаданные в DT-INF/Configuration.xml или Extension.xml
        2. Новая структура: метаданные в src/Configuration/Configuration.mdo или src/Extension/Extension.mdo
        
        Args:
            edt_project: Путь к EDT проекту
            
        Raises:
            ValidationError: Если структура проекта некорректна
        """
        self.log_info("Проверка структуры EDT проекта...")
        
        # Проверяем наличие DT-INF
        dt_inf = edt_project / 'DT-INF'
        if not dt_inf.exists():
            raise ValidationError(
                f"Отсутствует директория DT-INF в проекте: {edt_project}"
            )
        
        self.log_info("[OK] Директория DT-INF найдена")
        
        # Проверяем наличие .project файла
        project_file = edt_project / '.project'
        if not project_file.exists():
            raise ValidationError(
                f"Отсутствует файл .project в проекте: {edt_project}"
            )
        
        self.log_info("[OK] Файл .project найден")
        
        # Проверяем наличие директории src
        src_dir = edt_project / 'src'
        if not src_dir.exists():
            raise ValidationError(
                f"Отсутствует директория src в проекте: {edt_project}"
            )
        
        self.log_info("[OK] Директория src найдена")
        
        # Определяем тип проекта по структуре
        # Вариант 1: Старая структура - Configuration.xml в DT-INF
        config_xml_old = dt_inf / 'Configuration.xml'
        extension_xml_old = dt_inf / 'Extension.xml'
        
        # Вариант 2: Новая структура - Configuration.mdo в src/Configuration
        config_mdo_new = src_dir / 'Configuration' / 'Configuration.mdo'
        extension_mdo_new = src_dir / 'Extension' / 'Extension.mdo'
        
        project_type_found = False
        
        # Проверяем старую структуру
        if config_xml_old.exists():
            self.log_info("[OK] Найден Configuration.xml в DT-INF (конфигурация, старая структура)")
            project_type_found = True
        
        if extension_xml_old.exists():
            self.log_info("[OK] Найден Extension.xml в DT-INF (расширение, старая структура)")
            project_type_found = True
        
        # Проверяем новую структуру
        if config_mdo_new.exists():
            self.log_info("[OK] Найден Configuration.mdo в src/Configuration (конфигурация)")
            project_type_found = True
        
        if extension_mdo_new.exists():
            self.log_info("[OK] Найден Extension.mdo в src/Extension (расширение)")
            project_type_found = True
        
        # Если не найден ни один из вариантов
        if not project_type_found:
            raise ValidationError(
                f"EDT проект не содержит метаданных конфигурации или расширения.\n" +
                f"Ожидается один из файлов:\n" +
                f"  - DT-INF/Configuration.xml (старая структура)\n" +
                f"  - DT-INF/Extension.xml (старая структура)\n" +
                f"  - src/Configuration/Configuration.mdo (новая структура)\n" +
                f"  - src/Extension/Extension.mdo (новая структура)\n" +
                f"Проект: {edt_project}"
            )
        
        # Подсчитываем количество файлов в src
        file_count = sum(1 for _ in src_dir.rglob('*') if _.is_file())
        self.log_info(f"  Найдено файлов в src: {file_count}")
        
        self.log_success("Базовая структура EDT проекта корректна")

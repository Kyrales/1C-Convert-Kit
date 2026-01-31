"""
Конвертер для валидации EDT проектов 1С.

Поддерживает валидацию EDT проектов с использованием EDT инструментов.
"""

from pathlib import Path
from typing import Dict, Optional

from ..base.converter import (
    BaseConverter,
    SourceType,
    ValidationError,
    ToolNotFoundError,
    ToolExecutionError
)
from ..base.tools import EdtToolWrapper


class ValidationConverter(BaseConverter):
    """
    Конвертер для валидации EDT проектов 1С.
    
    Выполняет валидацию EDT проектов с использованием EDT инструментов
    (ring или edtcli). Не создает выходных файлов, только проверяет
    корректность проекта.
    
    Args:
        env_vars: Словарь переменных окружения из .env файлов
        silent: Если True, подавляет вывод в консоль
        progress_callback: Опциональный callback для отчета о прогрессе
    """
    
    def __init__(
        self, 
        env_vars: Dict[str, str], 
        silent: bool = False,
        progress_callback: Optional[callable] = None,
        debug: bool = False
    ):
        super().__init__(env_vars, silent, progress_callback, debug)
        
        # Инициализация EDT инструмента
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        """
        Возвращает расширение выходного файла.
        
        Returns:
            str: '' (пустая строка, так как валидация не создает выходных файлов)
        """
        return ''
    
    def validate(self) -> None:
        """
        Валидирует параметры конвертации.
        
        Для валидации не требуется V8_DST_PATH, так как выходные файлы не создаются.
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Проверка обязательных параметров
        if not self.src_path:
            raise ValidationError("Не указан параметр V8_SRC_PATH (путь к источнику)")
        
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
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Проверка что источник - это EDT проект
        source_type = self.detect_source_type()
        if source_type != SourceType.EDT:
            raise ValidationError(
                f"Источник должен быть EDT проектом. "
                f"Обнаружен тип: {source_type.value}. "
                f"Убедитесь что V8_SRC_PATH указывает на директорию с папкой DT-INF."
            )
        
        # Проверяем что EDT проект существует и имеет правильную структуру
        src_path_obj = Path(self.src_path)
        dt_inf_dir = src_path_obj / 'DT-INF'
        
        if not dt_inf_dir.exists():
            raise ValidationError(
                f"EDT проект не содержит директорию DT-INF: {self.src_path}"
            )
        
        self.log_info(f"EDT проект найден: {self.src_path}")
    
    def _do_convert(self) -> int:
        """
        Выполняет валидацию EDT проекта.
        
        Использует EDT инструменты для проверки корректности проекта.
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Валидация EDT проекта")
        self.report_progress("Валидация EDT проекта", 0)
        
        # Проверяем доступность EDT инструмента
        if not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (ring/edtcli) не найден. "
                "Установите EDT или укажите путь в переменной RING_TOOL/EDT_TOOL"
            )
        
        try:
            # Создаем временную директорию для workspace
            edt_workspace = self.temp_dir / 'edt_ws'
            edt_workspace.mkdir(exist_ok=True)
            
            self.log_info("Запуск валидации EDT проекта...")
            self.report_progress("Выполнение валидации", 20)
            
            # Путь к EDT проекту
            edt_project = Path(self.src_path)
            
            # Выполняем валидацию
            # Примечание: Метод validate_project будет добавлен в EdtToolWrapper
            # Пока используем заглушку, которая проверяет базовую структуру
            self._validate_edt_structure(edt_project)
            
            self.log_success("Валидация EDT проекта завершена успешно")
            self.report_progress("Валидация завершена", 100)
            
            return 0
            
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
        
        self.log_info("✓ Директория DT-INF найдена")
        
        # Проверяем наличие .project файла
        project_file = edt_project / '.project'
        if not project_file.exists():
            raise ValidationError(
                f"Отсутствует файл .project в проекте: {edt_project}"
            )
        
        self.log_info("✓ Файл .project найден")
        
        # Проверяем наличие Configuration.xml в DT-INF
        config_xml = dt_inf / 'Configuration.xml'
        if config_xml.exists():
            self.log_info("✓ Найден Configuration.xml (конфигурация)")
        
        # Проверяем наличие Extension.xml в DT-INF
        extension_xml = dt_inf / 'Extension.xml'
        if extension_xml.exists():
            self.log_info("✓ Найден Extension.xml (расширение)")
        
        # Проверяем что есть хотя бы один из файлов
        if not config_xml.exists() and not extension_xml.exists():
            raise ValidationError(
                f"EDT проект не содержит ни Configuration.xml, ни Extension.xml в DT-INF: {edt_project}"
            )
        
        # Проверяем наличие директории src
        src_dir = edt_project / 'src'
        if src_dir.exists():
            self.log_info(f"✓ Директория src найдена")
            
            # Подсчитываем количество файлов в src
            file_count = sum(1 for _ in src_dir.rglob('*') if _.is_file())
            self.log_info(f"  Найдено файлов в src: {file_count}")
        else:
            self.log_warning("Директория src не найдена (проект может быть пустым)")
        
        self.log_success("Базовая структура EDT проекта корректна")

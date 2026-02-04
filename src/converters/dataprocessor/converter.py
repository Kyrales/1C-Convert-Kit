"""
Конвертер для обработок и отчетов 1С.

Поддерживает конвертацию обработок и отчетов между форматами:
- EDT -> EPF/ERF
- XML -> EPF/ERF
"""

from pathlib import Path
from typing import Dict, Optional, List, Tuple, Callable

from ..base.converter import (
    BaseConverter,
    SourceType,
    ValidationError,
    ToolNotFoundError,
    ToolExecutionError
)
from ..base.tools import V8ToolWrapper, EdtToolWrapper


class DataProcessorConverter(BaseConverter):
    """
    Конвертер для обработок и отчетов 1С.
    
    Поддерживает конвертацию из EDT и XML в форматы EPF (обработки) и ERF (отчеты).
    Может обрабатывать множественные файлы обработок/отчетов.
    
    Args:
        env_vars: Словарь переменных окружения из .env файлов
        silent: Если True, подавляет вывод в консоль
        progress_callback: Опциональный callback для отчета о прогрессе
    """
    
    base_ib: str
    base_config: str
    v8_tool: V8ToolWrapper
    edt_tool: EdtToolWrapper
    
    def __init__(
        self, 
        env_vars: Dict[str, str], 
        silent: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        debug: bool = False
    ):
        super().__init__(env_vars, silent, progress_callback, debug)
        
        # Параметры базовой ИБ
        self.base_ib = env_vars.get('V8_BASE_IB', '')
        self.base_config = env_vars.get('V8_BASE_CONFIG', '')
        
        # Инициализация инструментов
        self.v8_tool = V8ToolWrapper(env_vars, self.logger)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        """
        Возвращает расширение выходного файла.
        
        Returns:
            str: '.epf' (по умолчанию, может быть .erf для отчетов)
        """
        return '.epf'
    
    def _validate_specific(self) -> None:
        """
        Специфичная валидация для конвертера обработок/отчетов.
        
        Проверяет:
        - Что dst_path указывает на директорию, а не на файл
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Проверка что dst_path - это директория, а не файл
        dst_path_obj = Path(self.dst_path)
        if dst_path_obj.suffix in ['.epf', '.erf']:
            raise ValidationError(
                f"V8_DST_PATH должен указывать на директорию для выходных файлов, " +
                f"а не на конкретный файл. Получено: {self.dst_path}"
            )
    
    def _do_convert(self) -> int:
        """
        Выполняет конвертацию обработок/отчетов.
        
        Определяет тип источника и вызывает соответствующий метод конвертации.
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        # Определяем тип источника
        source_type = self.detect_source_type()
        self.log_info(f"Тип источника: {source_type.value}")
        
        # Маршрутизация по типу источника
        if source_type == SourceType.EDT:
            return self._convert_from_edt()
        elif source_type == SourceType.XML:
            return self._convert_from_xml()
        else:
            raise ValidationError(
                f"Неподдерживаемый тип источника: {source_type.value}. " +
                f"Поддерживаются: EDT, XML"
            )
    
    def _prepare_base_ib(self) -> str:
        """
        Подготавливает базовую ИБ для загрузки обработок/отчетов.
        
        Использует общий helper prepare_base_infobase из base.tools.
        
        Returns:
            str: Строка подключения к ИБ
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если ошибка при создании/загрузке ИБ
        """
        from ..base.tools import prepare_base_infobase
        
        assert self.temp_dir is not None, "temp_dir должен быть инициализирован"
        
        return prepare_base_infobase(
            base_ib=self.base_ib,
            base_config=self.base_config,
            temp_dir=self.temp_dir,
            v8_tool=self.v8_tool,
            logger=self.logger,
            entity_type="обработок/отчетов"
        )
    
    def _find_processor_files(self, xml_path: Path) -> List[Tuple[Path, str, str]]:
        """
        Находит все файлы обработок и отчетов в XML директории.
        
        Args:
            xml_path: Путь к директории с XML файлами
            
        Returns:
            list: Список кортежей (xml_file_path, output_extension, output_name)
        """
        files = []
        
        # Ищем обработки в ExternalDataProcessors
        processors_dir = xml_path / 'ExternalDataProcessors'
        if processors_dir.exists():
            for xml_file in processors_dir.glob('*.xml'):
                # Имя файла без расширения
                name = xml_file.stem
                files.append((xml_file, '.epf', name))
                self.log_info(f"Найдена обработка: {name}")
        
        # Ищем отчеты в ExternalReports
        reports_dir = xml_path / 'ExternalReports'
        if reports_dir.exists():
            for xml_file in reports_dir.glob('*.xml'):
                # Имя файла без расширения
                name = xml_file.stem
                files.append((xml_file, '.erf', name))
                self.log_info(f"Найден отчет: {name}")
        
        return files
    
    def _process_files_batch(
        self,
        processor_files: List[Tuple[Path, str, str]],
        ib_connection: str,
        output_dir: Path,
        progress_base: int,
        progress_span: int
    ) -> None:
        """
        Обрабатывает пакет файлов обработок/отчетов.
        
        Args:
            processor_files: Список кортежей (xml_file, extension, name)
            ib_connection: Строка подключения к ИБ
            output_dir: Директория для выходных файлов
            progress_base: Базовое значение прогресса (начало диапазона)
            progress_span: Диапазон прогресса (размер диапазона)
        
        Raises:
            ToolExecutionError: Если ошибка при конвертации файла
        """
        # Создаем выходную директорию
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Конвертируем каждый файл
        total_files = len(processor_files)
        for idx, (xml_file, extension, name) in enumerate(processor_files, 1):
            self.log_info(f"Конвертация {idx}/{total_files}: {name}{extension}")
            
            assert self.temp_dir is not None, "temp_dir должен быть инициализирован"
            log_file = self.temp_dir / f'load_{name}.log'
            
            result = self.v8_tool.load_external_processor(
                ib_connection=ib_connection,
                xml_file=xml_file,
                output_dir=output_dir,
                log_file=log_file
            )
            
            if result != 0:
                raise ToolExecutionError(
                    f"Ошибка при конвертации {name}{extension}",
                    temp_dir=self.temp_dir
                )
            
            # Проверяем что файл создан
            output_file = output_dir / f"{name}{extension}"
            if not output_file.exists():
                raise ToolExecutionError(
                    f"Выходной файл не создан: {output_file}",
                    temp_dir=self.temp_dir
                )
            
            self.log_success(f"Создан файл: {output_file}")
            
            # Обновляем прогресс
            progress = progress_base + int((idx / total_files) * progress_span)
            self.report_progress(f"Обработано {idx}/{total_files}", progress)
    
    def _convert_from_edt(self) -> int:
        """
        Конвертирует обработки/отчеты из EDT проекта в EPF/ERF файлы.
        
        Последовательность: EDT -> XML -> EPF/ERF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Конвертация EDT -> EPF/ERF")
        self.report_progress("Конвертация EDT -> EPF/ERF", 0)
        
        # Проверяем доступность EDT инструмента
        if not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (1cedtcli/ring) не найден. " +
                "Установите EDT или укажите путь в переменной RING_TOOL/EDT_TOOL"
            )
        
        # Создаем временные директории
        assert self.temp_dir is not None, "temp_dir должен быть инициализирован"
        temp_xml = self.temp_dir / 'tmp_xml'
        _ = temp_xml.mkdir(exist_ok=True)
        
        edt_workspace = self.temp_dir / 'edt_ws'
        _ = edt_workspace.mkdir(exist_ok=True)
        
        try:
            # Этап 1: Экспорт EDT -> XML
            self.start_stage("Этап 1/3: Экспорт EDT проекта в XML...")
            self.report_progress("Экспорт EDT -> XML", 10)
            
            result = self.edt_tool.export_to_xml(
                edt_project=Path(self.src_path),
                xml_output=temp_xml,
                workspace=edt_workspace
            )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при экспорте EDT проекта в XML",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("EDT проект успешно экспортирован в XML")
            self.report_progress("Экспорт EDT -> XML завершен", 30)
            
            # Этап 2: Подготовка базовой ИБ
            self.start_stage("Этап 2/3: Подготовка базовой ИБ...")
            self.report_progress("Подготовка базовой ИБ", 40)
            
            ib_connection = self._prepare_base_ib()
            self.end_stage("Базовая ИБ готова")
            self.report_progress("Базовая ИБ готова", 50)
            
            # Этап 3: Конвертация XML -> EPF/ERF
            self.start_stage("Этап 3/3: Конвертация обработок и отчетов...")
            self.report_progress("Конвертация XML -> EPF/ERF", 60)
            
            # Находим все файлы обработок и отчетов
            processor_files = self._find_processor_files(temp_xml)
            
            if not processor_files:
                self.log_warning("Не найдено обработок или отчетов для конвертации")
                return 0
            
            self.log_info(f"Найдено файлов для конвертации: {len(processor_files)}")
            
            # Используем общий метод для обработки файлов
            self._process_files_batch(
                processor_files=processor_files,
                ib_connection=ib_connection,
                output_dir=Path(self.dst_path),
                progress_base=60,
                progress_span=35
            )
            
            self.end_stage(f"Все файлы успешно сконвертированы в: {self.dst_path}")
            self.report_progress("Конвертация завершена", 100)
            
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации EDT -> EPF/ERF: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise
    
    def _convert_from_xml(self) -> int:
        """
        Конвертирует обработки/отчеты из XML файлов в EPF/ERF файлы.
        
        Последовательность: XML -> EPF/ERF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Конвертация XML -> EPF/ERF")
        self.report_progress("Конвертация XML -> EPF/ERF", 0)
        
        try:
            # Этап 1: Подготовка базовой ИБ
            self.start_stage("Этап 1/2: Подготовка базовой ИБ...")
            self.report_progress("Подготовка базовой ИБ", 10)
            
            ib_connection = self._prepare_base_ib()
            self.end_stage("Базовая ИБ готова")
            self.report_progress("Базовая ИБ готова", 30)
            
            # Этап 2: Конвертация XML -> EPF/ERF
            self.start_stage("Этап 2/2: Конвертация обработок и отчетов...")
            self.report_progress("Конвертация XML -> EPF/ERF", 40)
            
            # Находим все файлы обработок и отчетов
            xml_path = Path(self.src_path)
            processor_files = self._find_processor_files(xml_path)
            
            if not processor_files:
                self.log_warning("Не найдено обработок или отчетов для конвертации")
                return 0
            
            self.log_info(f"Найдено файлов для конвертации: {len(processor_files)}")
            
            # Используем общий метод для обработки файлов
            self._process_files_batch(
                processor_files=processor_files,
                ib_connection=ib_connection,
                output_dir=Path(self.dst_path),
                progress_base=40,
                progress_span=55
            )
            
            self.end_stage(f"Все файлы успешно сконвертированы в: {self.dst_path}")
            self.report_progress("Конвертация завершена", 100)
            
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации XML -> EPF/ERF: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise

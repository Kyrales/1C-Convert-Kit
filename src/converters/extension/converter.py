"""
Конвертер для расширений 1С.

Поддерживает конвертацию расширений между форматами:
- EDT -> CFE
- XML -> CFE
- IB -> CFE
"""

from pathlib import Path
from typing import Dict, Optional, Callable

from ..base.converter import (
    BaseConverter,
    SourceType,
    ValidationError,
    ToolNotFoundError,
    ToolExecutionError
)
from ..base.tools import V8ToolWrapper, IbcmdToolWrapper, EdtToolWrapper
from ..base.ib_utils import parse_ib_reference


class ExtensionConverter(BaseConverter):
    """
    Конвертер для расширений 1С.
    
    Поддерживает конвертацию из EDT, XML и InfoBase в формат CFE.
    Использует инструменты 1cv8.exe (designer) или ibcmd.exe в зависимости
    от настроек.
    
    Args:
        env_vars: Словарь переменных окружения из .env файлов
        silent: Если True, подавляет вывод в консоль
        progress_callback: Опциональный callback для отчета о прогрессе
    """
    
    ext_name: str
    base_ib: str
    base_config: str
    convert_tool: str
    v8_tool: V8ToolWrapper
    ibcmd_tool: IbcmdToolWrapper
    edt_tool: EdtToolWrapper
    
    def __init__(
        self, 
        env_vars: Dict[str, str], 
        silent: bool = False,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        debug: bool = False
    ):
        super().__init__(env_vars, silent, progress_callback, debug)
        
        # Параметры расширения
        self.ext_name = env_vars.get('V8_EXT_NAME', '')
        self.base_ib = env_vars.get('V8_BASE_IB', '')
        self.base_config = env_vars.get('V8_BASE_CONFIG', '')
        self.convert_tool = env_vars.get(
            'V8_CONVERT_TOOL', 'designer'
        ).strip().lower()
        
        # Инициализация инструментов
        self.v8_tool = V8ToolWrapper(env_vars, self.logger)
        self.ibcmd_tool = IbcmdToolWrapper(env_vars, self.logger)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        """
        Возвращает расширение выходного файла.
        
        Returns:
            str: '.cfe'
        """
        return '.cfe'
    
    
    
    def _validate_specific(self) -> None:
        """
        Специфичная валидация для конвертера расширений.
        
        Проверяет:
        - Для ext2cfe: указан параметр V8_EXT_NAME и dst_path указывает на файл .cfe
        - Для ext2xml, ext2edt: dst_path указывает на директорию
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Получаем тип конвертации
        script_name = self.env_vars.get('ScriptName', '').lower()
        
        dst_path_obj = Path(self.dst_path)
        
        if script_name == 'ext2ib':
            if not self.ext_name:
                raise ValidationError(
                    "Не указан параметр V8_EXT_NAME (имя расширения)."
                )
            if self.convert_tool not in ['designer', 'ibcmd']:
                raise ValidationError(
                    "V8_CONVERT_TOOL для ext2ib должен быть designer или ibcmd, "
                    f"получено: {self.convert_tool}"
                )
            self._validate_binary_env_flag('V8_IB_UPDATE')
            is_server, server, base = parse_ib_reference(self.dst_path)
            looks_server = (
                self.dst_path.lower().startswith('/s')
                or 'srvr=' in self.dst_path.lower()
                or 'ref=' in self.dst_path.lower()
            )
            if looks_server and not (is_server and server and base):
                raise ValidationError(
                    f"Некорректная серверная ИБ в V8_DST_PATH: {self.dst_path}"
                )
            if not is_server:
                ib_path = Path(base or self.dst_path)
                if not (ib_path / '1cv8.1cd').exists():
                    raise ValidationError(
                        f"V8_DST_PATH должен указывать на существующую файловую ИБ: {self.dst_path}"
                    )
            return

        # Для конвертации в CFE файл
        if script_name == 'ext2cfe':
            # Проверка обязательного параметра V8_EXT_NAME
            if not self.ext_name:
                raise ValidationError(
                    "Не указан параметр V8_EXT_NAME (имя расширения). " +
                    "Этот параметр обязателен для конвертации расширений в CFE."
                )
            
            if dst_path_obj.suffix.lower() != '.cfe':
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на файл .cfe для {script_name}, " +
                    f"получено: {self.dst_path}"
                )
        # Для конвертации в XML или EDT
        elif script_name in ['ext2xml', 'ext2edt']:
            # Для XML и EDT нужна директория, а не файл
            if dst_path_obj.suffix:
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на директорию для {script_name}, " +
                    f"а не на файл. Получено: {self.dst_path}"
                )
        else:
            # Для неизвестных типов конвертации используем старую логику
            if not self.ext_name:
                raise ValidationError(
                    "Не указан параметр V8_EXT_NAME (имя расширения). " +
                    "Этот параметр обязателен для конвертации расширений."
                )
            
            if dst_path_obj.suffix.lower() != '.cfe':
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на файл .cfe, " +
                    f"получено: {self.dst_path}"
                )
    
    def _do_convert(self) -> int:
        """
        Выполняет конвертацию расширения.
        
        Определяет тип источника и вызывает соответствующий метод конвертации.
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        # Определяем тип источника
        source_type = self.detect_source_type()
        self.log_info(f"Тип источника: {source_type.value}")
        self.log_info(f"Имя расширения: {self.ext_name}")

        if self.env_vars.get('ScriptName', '').lower() == 'ext2ib':
            return self._convert_to_ib(source_type)
        
        # Маршрутизация по типу источника
        if source_type == SourceType.EDT:
            return self._convert_from_edt()
        elif source_type == SourceType.XML:
            return self._convert_from_xml()
        elif source_type in [SourceType.FILE_IB, SourceType.SERVER_IB]:
            return self._convert_from_ib()
        elif source_type == SourceType.CFE_FILE:
            return self._convert_from_cfe()
        else:
            raise ValidationError(
                f"Неподдерживаемый тип источника: {source_type.value}. " +
                f"Поддерживаются: EDT, XML, InfoBase, CFE"
            )

    def _convert_to_ib(self, source_type: SourceType) -> int:
        """Загружает расширение из CFE, XML или EDT в целевую ИБ."""
        if source_type not in [SourceType.CFE_FILE, SourceType.XML, SourceType.EDT]:
            raise ValidationError(
                "ext2ib поддерживает источники CFE, XML и EDT"
            )
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"

        if self.convert_tool == 'ibcmd':
            if not self.ibcmd_tool.is_available():
                raise ToolNotFoundError("ibcmd.exe не найден в системе")
        elif not self.v8_tool.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")

        source_path = Path(self.src_path)
        if source_type == SourceType.EDT:
            if not self.edt_tool.is_available():
                raise ToolNotFoundError("EDT инструмент (1cedtcli/ring) не найден")
            xml_path = self.temp_dir / 'extension_xml'
            workspace = self.temp_dir / 'edt_ws'
            xml_path.mkdir(parents=True, exist_ok=True)
            workspace.mkdir(parents=True, exist_ok=True)
            result = self.edt_tool.export_to_xml(
                edt_project=source_path,
                xml_output=xml_path,
                workspace=workspace,
            )
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при экспорте EDT проекта расширения в XML",
                    temp_dir=self.temp_dir,
                )
            source_path = xml_path

        is_server, _, file_path = parse_ib_reference(self.dst_path)
        db_path = Path('.') if is_server else Path(file_path or self.dst_path)
        if self.convert_tool == 'ibcmd':
            if source_type == SourceType.CFE_FILE:
                result = self.ibcmd_tool.import_config_from_cf(
                    db_path=db_path,
                    cf_file=source_path,
                    extension_name=self.ext_name,
                    use_server=is_server,
                )
            else:
                result = self.ibcmd_tool.import_config_from_xml(
                    db_path=db_path,
                    xml_path=source_path,
                    extension_name=self.ext_name,
                    use_server=is_server,
                )
        else:
            log_file = self.temp_dir / 'load_extension.log'
            ib_connection = self.dst_path if is_server else str(db_path)
            if source_type == SourceType.CFE_FILE:
                result = self.v8_tool.load_config_from_cf(
                    ib_connection=ib_connection,
                    cf_file=source_path,
                    log_file=log_file,
                    extension_name=self.ext_name,
                )
            else:
                result = self.v8_tool.load_config_from_files(
                    ib_connection=ib_connection,
                    xml_path=source_path,
                    log_file=log_file,
                    extension_name=self.ext_name,
                )
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при загрузке расширения в информационную базу",
                temp_dir=self.temp_dir,
            )

        self._update_infobase_if_requested(
            self.dst_path,
            self.convert_tool,
            self.v8_tool,
            self.ibcmd_tool,
            extension_name=self.ext_name,
        )
        self.report_progress("Конвертация завершена", 100)
        return 0
    
    def _prepare_base_ib(self) -> str:
        """
        Подготавливает базовую ИБ для загрузки расширения.
        
        Использует общий helper prepare_base_infobase из base.tools.
        
        Returns:
            str: Строка подключения к ИБ
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если ошибка при создании/загрузке ИБ
        """
        from ..base.tools import prepare_base_infobase
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        return prepare_base_infobase(
            base_ib=self.base_ib,
            base_config=self.base_config,
            temp_dir=self.temp_dir,
            v8_tool=self.v8_tool,
            logger=self.logger,
            entity_type="расширения"
        )
    
    def _convert_from_edt(self) -> int:
        """
        Конвертирует расширение из EDT проекта в CFE файл.
        
        Последовательность: EDT -> XML -> IB -> CFE
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Конвертация EDT -> CFE")
        self.report_progress("Конвертация EDT -> CFE", 0)
        
        # Проверяем доступность EDT инструмента
        if not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (1cedtcli/ring) не найден. " +
                "Установите EDT или укажите путь в переменной EDT_TOOL"
            )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        # Создаем временные директории
        temp_xml = self.temp_dir / 'tmp_xml'
        _ = temp_xml.mkdir(exist_ok=True)
        
        edt_workspace = self.temp_dir / 'edt_ws'
        _ = edt_workspace.mkdir(exist_ok=True)
        
        try:
            # Этап 1: Экспорт EDT -> XML
            self.start_stage("Этап 1/4: Экспорт EDT проекта в XML...")
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
            self.start_stage("Этап 2/4: Подготовка базовой ИБ...")
            self.report_progress("Подготовка базовой ИБ", 40)
            
            ib_connection = self._prepare_base_ib()
            self.end_stage("Базовая ИБ готова")
            self.report_progress("Базовая ИБ готова", 50)
            
            # Этап 3: Загрузка расширения XML -> IB
            self.start_stage("Этап 3/4: Загрузка расширения в ИБ...")
            self.report_progress("Загрузка XML -> IB", 60)
            
            log_file = self.temp_dir / 'load_extension.log'
            
            result = self.v8_tool.load_config_from_files(
                ib_connection=ib_connection,
                xml_path=temp_xml,
                log_file=log_file,
                extension_name=self.ext_name
            )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при загрузке расширения из XML",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Расширение успешно загружено в ИБ")
            self.report_progress("Загрузка XML -> IB завершена", 75)
            
            # Этап 4: Выгрузка IB -> CFE
            self.start_stage("Этап 4/4: Выгрузка расширения в CFE файл...")
            self.report_progress("Выгрузка IB -> CFE", 80)
            
            output_file = Path(self.dst_path)
            dump_log_file = self.temp_dir / 'dump_extension.log'
            
            result = self.v8_tool.dump_config(
                ib_connection=ib_connection,
                output_file=output_file,
                log_file=dump_log_file,
                extension_name=self.ext_name
            )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при выгрузке расширения в CFE файл",
                    temp_dir=self.temp_dir
                )
            
            # Проверяем что файл создан
            if not output_file.exists():
                raise ToolExecutionError(
                    f"Выходной файл не создан: {output_file}",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage(f"Расширение успешно выгружено в: {output_file}")
            self.report_progress("Конвертация завершена", 100)
            
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации EDT -> CFE: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise
    
    def _convert_from_xml(self) -> int:
        """
        Конвертирует расширение из XML файлов в CFE файл.
        
        Последовательность: XML -> IB -> CFE
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Конвертация XML -> CFE")
        self.report_progress("Конвертация XML -> CFE", 0)
        
        # Проверяем доступность инструмента
        if self.convert_tool == 'ibcmd':
            if not self.ibcmd_tool.is_available():
                raise ToolNotFoundError(
                    "ibcmd.exe не найден. " +
                    "Установите платформу 1С или укажите путь в переменной IBCMD_TOOL"
                )
        else:
            if not self.v8_tool.is_available():
                raise ToolNotFoundError(
                    "1cv8.exe не найден. " +
                    "Установите платформу 1С или укажите путь в переменной V8_TOOL"
                )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        try:
            # Этап 1: Подготовка базовой ИБ
            self.log_info("Этап 1/3: Подготовка базовой ИБ...")
            self.report_progress("Подготовка базовой ИБ", 10)
            
            ib_connection = self._prepare_base_ib()
            self.report_progress("Базовая ИБ готова", 30)
            
            # Этап 2: Загрузка расширения XML -> IB
            self.start_stage("Этап 2/3: Загрузка расширения в ИБ...")
            self.report_progress("Загрузка XML -> IB", 40)
            
            log_file = self.temp_dir / 'load_extension.log'
            
            result = self.v8_tool.load_config_from_files(
                ib_connection=ib_connection,
                xml_path=Path(self.src_path),
                log_file=log_file,
                extension_name=self.ext_name
            )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при загрузке расширения из XML",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Расширение успешно загружено в ИБ")
            self.report_progress("Загрузка XML -> IB завершена", 60)
            
            # Этап 3: Выгрузка IB -> CFE
            self.start_stage("Этап 3/3: Выгрузка расширения в CFE файл...")
            self.report_progress("Выгрузка IB -> CFE", 70)
            
            output_file = Path(self.dst_path)
            dump_log_file = self.temp_dir / 'dump_extension.log'
            
            if self.convert_tool == 'ibcmd':
                # Используем ibcmd для выгрузки
                self.log_info("Использование ibcmd для выгрузки расширения...")
                
                # Для ibcmd нужен путь к директории ИБ
                if ib_connection.startswith('/F'):
                    db_path = Path(ib_connection[2:])
                else:
                    db_path = Path(ib_connection)
                
                result = self.ibcmd_tool.save_config(
                    db_path=db_path,
                    output_file=output_file,
                    extension_name=self.ext_name
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке расширения через ibcmd",
                        temp_dir=self.temp_dir
                    )
            else:
                # Используем designer для выгрузки
                self.log_info("Использование designer для выгрузки расширения...")
                
                result = self.v8_tool.dump_config(
                    ib_connection=ib_connection,
                    output_file=output_file,
                    log_file=dump_log_file,
                    extension_name=self.ext_name
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке расширения через designer",
                        temp_dir=self.temp_dir
                    )
            
            # Проверяем что файл создан
            if not output_file.exists():
                raise ToolExecutionError(
                    f"Выходной файл не создан: {output_file}",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage(f"Расширение успешно выгружено в: {output_file}")
            self.report_progress("Конвертация завершена", 100)
            
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации XML -> CFE: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise
    
    def _convert_from_ib(self) -> int:
        """
        Конвертирует расширение из информационной базы в CFE файл.
        
        Последовательность: IB -> CFE
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Конвертация IB -> CFE")
        self.report_progress("Конвертация IB -> CFE", 0)
        
        # Проверяем доступность инструмента
        if self.convert_tool == 'ibcmd':
            if not self.ibcmd_tool.is_available():
                raise ToolNotFoundError(
                    "ibcmd.exe не найден. " +
                    "Установите платформу 1С или укажите путь в переменной IBCMD_TOOL"
                )
        else:
            if not self.v8_tool.is_available():
                raise ToolNotFoundError(
                    "1cv8.exe не найден. " +
                    "Установите платформу 1С или укажите путь в переменной V8_TOOL"
                )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        try:
            output_file = Path(self.dst_path)
            
            from ..base.ib_utils import parse_ib_reference
            is_server, _, base = parse_ib_reference(self.src_path)
            ib_connection = self.src_path if is_server else (base or self.src_path)
            
            self.log_info(f"Подключение к ИБ: {ib_connection}")
            self.log_info(f"Выгрузка расширения: {self.ext_name}")
            
            if self.convert_tool == 'ibcmd':
                # Используем ibcmd для выгрузки
                self.log_info("Использование ibcmd для выгрузки расширения...")
                self.report_progress("Выгрузка расширения", 30)
                
                if not is_server:
                    db_path = Path(base or self.src_path)
                else:
                    db_path = Path(self.src_path)
                
                result = self.ibcmd_tool.save_config(
                    db_path=db_path,
                    output_file=output_file,
                    extension_name=self.ext_name
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке расширения через ibcmd",
                        temp_dir=self.temp_dir
                    )
                
            else:
                # Используем designer для выгрузки
                self.log_info("Использование designer для выгрузки расширения...")
                self.report_progress("Выгрузка расширения", 30)
                
                log_file = self.temp_dir / 'dump_extension.log'
                
                result = self.v8_tool.dump_config(
                    ib_connection=ib_connection,
                    output_file=output_file,
                    log_file=log_file,
                    extension_name=self.ext_name
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке расширения через designer",
                        temp_dir=self.temp_dir
                    )
            
            # Проверяем что файл создан
            if not output_file.exists():
                raise ToolExecutionError(
                    f"Выходной файл не создан: {output_file}",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage(f"Расширение успешно выгружено в: {output_file}")
            self.report_progress("Конвертация завершена", 100)
            
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации IB -> CFE: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise

    
    def _convert_from_cfe(self) -> int:
        """
        Конвертирует расширение из CFE файла в XML или EDT.
        
        Последовательность: CFE -> IB -> XML/EDT
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        # Получаем тип конвертации
        script_name = self.env_vars.get('ScriptName', '').lower()
        
        if script_name == 'ext2xml':
            self.log_info("Конвертация CFE -> XML")
            self.report_progress("Конвертация CFE -> XML", 0)
            target_format = "XML"
        elif script_name == 'ext2edt':
            self.log_info("Конвертация CFE -> EDT")
            self.report_progress("Конвертация CFE -> EDT", 0)
            target_format = "EDT"
        else:
            raise ValidationError(
                f"Неподдерживаемый тип конвертации из CFE: {script_name}. " +
                f"Поддерживаются: ext2xml, ext2edt"
            )
        
        # Извлекаем имя расширения из имени файла, если не указано
        if not self.ext_name:
            cfe_name = Path(self.src_path).stem
            # Убираем расширение .Колонтитулы из имени
            if '.' in cfe_name:
                self.ext_name = cfe_name.split('.', 1)[1]
            else:
                self.ext_name = cfe_name
            self.log_info(f"Имя расширения определено из файла: {self.ext_name}")
        
        # Проверяем доступность инструментов
        if not self.v8_tool.is_available():
            raise ToolNotFoundError(
                "1cv8.exe не найден. " +
                "Установите платформу 1С или укажите путь в переменной V8_TOOL"
            )
        
        if target_format == "EDT" and not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (1cedtcli) не найден. " +
                "Установите EDT или укажите путь в переменной EDTCLI_TOOL"
            )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        try:
            # Этап 1: Подготовка базовой ИБ
            self.log_info("Этап 1/3: Подготовка базовой ИБ...")
            self.report_progress("Подготовка базовой ИБ", 10)
            
            ib_connection = self._prepare_base_ib()
            self.report_progress("Базовая ИБ готова", 30)
            
            # Этап 2: Загружаем расширение из CFE в ИБ
            self.start_stage("Этап 2/3: Загрузка расширения из CFE файла...")
            self.report_progress("Загрузка расширения", 40)
            
            cfe_file = Path(self.src_path)
            load_log_file = self.temp_dir / 'load_cfe.log'
            
            # Формируем команду загрузки CFE
            ib_path_str = str(ib_connection).replace('\\', '/')
            ib_conn_str = f'File={ib_path_str};'
            
            cmd = [
                str(self.v8_tool.tool_path),
                'DESIGNER',
                '/IBConnectionString', ib_conn_str,
                '/DisableStartupDialogs',
                '/Out', str(load_log_file),
                '/LoadCfg', str(cfe_file),
                '-Extension', self.ext_name
            ]
            
            import subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при загрузке CFE файла в ИБ",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Расширение загружено в ИБ")
            self.report_progress("Расширение загружено", 60)
            
            # Этап 3: Выгружаем в целевой формат
            if target_format == "XML":
                self.start_stage("Этап 3/3: Выгрузка расширения в XML...")
                self.report_progress("Выгрузка в XML", 70)
                
                # Определяем имя выходной директории
                cfe_name = Path(self.src_path).stem
                output_dir = Path(self.dst_path) / cfe_name
                self._maybe_clean_dir(output_dir, 'V8_EXT_CLEAN_DST', 'V8_EXT_CLEAN_DST')
                output_dir.mkdir(parents=True, exist_ok=True)
                
                dump_log_file = self.temp_dir / 'dump_xml.log'
                
                # Формируем команду выгрузки в XML
                cmd = [
                    str(self.v8_tool.tool_path),
                    'DESIGNER',
                    '/IBConnectionString', ib_conn_str,
                    '/DisableStartupDialogs',
                    '/Out', str(dump_log_file),
                    '/DumpConfigToFiles', str(output_dir),
                    '-Extension', self.ext_name
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='cp1251',
                    errors='replace'
                )
                
                if result.returncode != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке расширения в XML",
                        temp_dir=self.temp_dir
                    )
                
                # Проверяем что XML файлы созданы
                config_xml = output_dir / 'Configuration.xml'
                if not config_xml.exists():
                    raise ToolExecutionError(
                        f"Файл Configuration.xml не создан: {config_xml}",
                        temp_dir=self.temp_dir
                    )
                
                self.end_stage(f"Расширение успешно выгружено в XML: {output_dir}")
                
            else:  # EDT
                self.start_stage("Этап 3/3: Выгрузка расширения в EDT...")
                self.report_progress("Выгрузка в EDT", 70)
                
                # Определяем имя выходной директории
                cfe_name = Path(self.src_path).stem
                output_dir = Path(self.dst_path) / cfe_name
                self._maybe_clean_dir(output_dir, 'V8_EXT_CLEAN_DST', 'V8_EXT_CLEAN_DST')
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Сначала выгружаем в XML
                temp_xml = self.temp_dir / 'tmp_xml'
                _ = temp_xml.mkdir(exist_ok=True)
                
                dump_log_file = self.temp_dir / 'dump_xml.log'
                
                cmd = [
                    str(self.v8_tool.tool_path),
                    'DESIGNER',
                    '/IBConnectionString', ib_conn_str,
                    '/DisableStartupDialogs',
                    '/Out', str(dump_log_file),
                    '/DumpConfigToFiles', str(temp_xml),
                    '-Extension', self.ext_name
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding='cp1251',
                    errors='replace'
                )
                
                if result.returncode != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке расширения в XML",
                        temp_dir=self.temp_dir
                    )
                
                # Затем импортируем XML в EDT
                edt_workspace = self.temp_dir / 'edt_ws'
                
                # Используем метод из EdtToolWrapper
                result = self.edt_tool.import_configuration_files_to_edt_project(
                    xml_source_path=temp_xml,
                    edt_project_path=output_dir,
                    workspace_path=edt_workspace,
                    entity_type="расширения"
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при импорте расширения в EDT",
                        temp_dir=self.temp_dir
                    )
                
                self.end_stage(f"Расширение успешно выгружено в EDT: {output_dir}")
            
            self.report_progress("Конвертация завершена", 100)
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации CFE -> {target_format}: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise

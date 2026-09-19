"""
Конвертер для конфигураций 1С.

Поддерживает конвертацию конфигураций между форматами:
- EDT -> CF
- XML -> CF
- IB -> CF
"""

from pathlib import Path
from typing import Dict, Optional, Callable, Union

from ..base.converter import (
    BaseConverter,
    SourceType,
    ValidationError,
    ToolNotFoundError,
    ToolExecutionError
)
from ..base.tools import V8ToolWrapper, IbcmdToolWrapper, EdtToolWrapper
from ..base.ib_utils import parse_ib_reference


class ConfigurationConverter(BaseConverter):
    """
    Конвертер для конфигураций 1С.
    
    Поддерживает конвертацию из EDT, XML и InfoBase в формат CF.
    Использует инструменты 1cv8.exe (designer) или ibcmd.exe в зависимости
    от настроек.
    
    Args:
        env_vars: Словарь переменных окружения из .env файлов
        silent: Если True, подавляет вывод в консоль
        progress_callback: Опциональный callback для отчета о прогрессе
    """
    
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
        
        # Инициализация инструментов
        convert_tool = env_vars.get('V8_CONVERT_TOOL', 'designer').strip().lower()
        if convert_tool == 'ibmcd':
            convert_tool = 'ibcmd'
        self.convert_tool = convert_tool
        self._ib_update_finished = False
        self.v8_tool = V8ToolWrapper(env_vars, self.logger)
        self.ibcmd_tool = IbcmdToolWrapper(env_vars, self.logger)
        self.edt_tool = EdtToolWrapper(env_vars, self.logger)
    
    def get_output_extension(self) -> str:
        """
        Возвращает расширение выходного файла.
        
        Returns:
            str: '.cf'
        """
        return '.cf'

    def report_progress(self, stage: str, percent: int):
        """Не сообщает 100% до завершения запрошенного обновления ИБ."""
        update_pending = (
            self.env_vars.get('V8_IB_UPDATE', '0').strip() == '1'
            and self.env_vars.get('ScriptName', '').lower() in ['conf2ib', 'dt2ib']
            and not self._ib_update_finished
        )
        if stage == "Конвертация завершена" and percent == 100 and update_pending:
            return
        super().report_progress(stage, percent)
    
    def _validate_specific(self) -> None:
        """
        Специфичная валидация для конвертера конфигураций.
        
        Проверяет:
        - Для conf2cf: dst_path указывает на файл с расширением .cf
        - Для conf2xml, conf2edt: dst_path указывает на директорию
        - Для conf2ib: dst_path указывает на файловую ИБ (каталог или /F<путь>) или серверную строку /S<сервер>\\<база>
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Получаем тип конвертации
        script_name = self.env_vars.get('ScriptName', '').lower()

        if script_name in ['conf2ib', 'dt2ib']:
            self._validate_binary_env_flag('V8_IB_UPDATE')

        if script_name in ['dt2ib', 'ib2dt'] and self.convert_tool not in [
            'designer',
            'ibcmd',
        ]:
            raise ValidationError(
                "V8_CONVERT_TOOL для DT-сценариев должен быть designer или ibcmd, "
                f"получено: {self.convert_tool}"
            )
        
        dst_path_obj = Path(self.dst_path)
        
        if script_name == 'conf2cf':
            if dst_path_obj.suffix.lower() != '.cf':
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на файл .cf для {script_name}, " +
                    f"получено: {self.dst_path}"
                )
        elif script_name in ['conf2ib', 'dt2ib']:
            if script_name == 'dt2ib' and Path(self.src_path).suffix.lower() != '.dt':
                raise ValidationError(
                    f"V8_SRC_PATH должен указывать на файл .dt для dt2ib, получено: {self.src_path}"
                )
            dst = self.dst_path
            dst_is_server, dst_server, dst_name = parse_ib_reference(dst)
            dst_looks_server = (
                dst.lower().startswith('/s') or
                'srvr=' in dst.lower() or
                'ref=' in dst.lower()
            )
            if dst_looks_server and not (
                dst_is_server and dst_server and dst_name
            ):
                raise ValidationError(
                    f"Некорректная серверная ИБ в V8_DST_PATH: {dst}"
                )
            if dst_is_server:
                return
            if dst.startswith('/F'):
                if not Path(dst[2:]).exists() and Path(dst[2:]).suffix:
                    raise ValidationError(
                        f"Неверный путь к файловой ИБ: {dst}"
                    )
                return
            if dst_path_obj.suffix:
                raise ValidationError(
                    f"V8_DST_PATH для {script_name} должен указывать на каталог ИБ или строку /F... или /S..., получено: {self.dst_path}"
                )
        elif script_name == 'ib2dt':
            if dst_path_obj.suffix.lower() != '.dt':
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на файл .dt для ib2dt, получено: {self.dst_path}"
                )
            src_is_server, src_server, src_name = parse_ib_reference(
                self.src_path
            )
            src_looks_server = (
                self.src_path.lower().startswith('/s') or
                'srvr=' in self.src_path.lower() or
                'ref=' in self.src_path.lower()
            )
            if src_looks_server and not (
                src_is_server and src_server and src_name
            ):
                raise ValidationError(
                    "Некорректная серверная ИБ в V8_SRC_PATH: " +
                    self.src_path
                )
            if self.detect_source_type() not in [
                SourceType.FILE_IB,
                SourceType.SERVER_IB,
            ]:
                raise ValidationError(
                    f"V8_SRC_PATH должен указывать на информационную базу для ib2dt, получено: {self.src_path}"
                )
        # Для конвертации в XML или EDT
        elif script_name in ['conf2xml', 'conf2edt']:
            if dst_path_obj.suffix:
                raise ValidationError(
                    message=f"V8_DST_PATH должен указывать на директорию для {script_name}, " +
                    f"а не на файл. Получено: {self.dst_path}"
                )
        else:
            # Для неизвестных типов конвертации используем старую логику
            if dst_path_obj.suffix.lower() != '.cf':
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на файл .cf, " +
                    f"получено: {self.dst_path}"
                )
    
    def _do_convert(self) -> int:
        """
        Выполняет конвертацию конфигурации.
        
        Определяет тип источника и вызывает соответствующий метод конвертации.
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        # Определяем тип источника
        source_type = self.detect_source_type()
        self.log_info(f"Тип источника: {source_type.value}")
        
        # Маршрутизация по типу источника
        if source_type == SourceType.EDT:
            result = self._convert_from_edt()
        elif source_type == SourceType.XML:
            result = self._convert_from_xml()
        elif source_type in [SourceType.FILE_IB, SourceType.SERVER_IB]:
            result = self._convert_from_ib()
        elif source_type == SourceType.CF_FILE:
            result = self._convert_from_cf()
        elif source_type == SourceType.DT_FILE:
            result = self._convert_from_dt()
        else:
            raise ValidationError(
                f"Неподдерживаемый тип источника: {source_type.value}. " +
                f"Поддерживаются: EDT, XML, InfoBase, CF, DT"
            )

        if (
            result == 0
            and self.env_vars.get('ScriptName', '').lower() in ['conf2ib', 'dt2ib']
        ):
            self._update_infobase_if_requested(
                self.dst_path,
                self.convert_tool,
                self.v8_tool,
                self.ibcmd_tool,
            )
            self._ib_update_finished = True
            self.report_progress("Конвертация завершена", 100)
        return result

    def _convert_from_dt(self) -> int:
        """Восстанавливает DT-файл в файловую или серверную ИБ."""
        if self.env_vars.get('ScriptName', '').lower() != 'dt2ib':
            raise ValidationError("DT-файл поддерживается только в сценарии dt2ib")

        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        dt_file = Path(self.src_path)
        ib_dir = self._get_file_ib_path_from_value(self.dst_path)
        self.report_progress("Восстановление DT -> IB", 20)

        if self.convert_tool == 'ibcmd':
            if not self.ibcmd_tool.is_available():
                raise ToolNotFoundError("ibcmd.exe не найден в системе")
            if ib_dir is None:
                self._set_server_ib_env(self.dst_path)
                db_path = Path('.')
            else:
                self._ensure_dir(ib_dir)
                db_path = ib_dir
            result = self.ibcmd_tool.restore_infobase(
                db_path,
                dt_file,
                use_server=ib_dir is None
            )
        else:
            if not self.v8_tool.is_available():
                raise ToolNotFoundError("1cv8.exe не найден в системе")
            if ib_dir is not None and not (ib_dir / '1cv8.1cd').exists():
                self._ensure_dir(ib_dir)
                self._create_file_ib_if_missing(
                    ib_dir, self.temp_dir / 'create_ib.log'
                )
            ib_connection = self.dst_path if ib_dir is None else str(ib_dir)
            result = self.v8_tool.restore_infobase(
                ib_connection, dt_file, self.temp_dir / 'restore_ib.log'
            )

        if result != 0:
            raise ToolExecutionError(
                "Ошибка при восстановлении информационной базы из DT",
                temp_dir=self.temp_dir
            )
        self.report_progress("Конвертация завершена", 100)
        return 0

    def _get_file_ib_path_from_value(self, value: str) -> Optional[Path]:
        is_server, _, base = parse_ib_reference(value)
        if is_server:
            return None
        if base:
            return Path(base)
        return Path(value)

    def _ensure_dir(self, path: Path) -> None:
        _ = path.mkdir(parents=True, exist_ok=True)

    def _make_ib_connection_string(self, ib_dir: Path) -> str:
        ib_dir_str = str(ib_dir).replace('\\', '/')
        return f"File={ib_dir_str};"

    def _set_server_ib_env(self, ib_path: str) -> None:
        is_server, server, name = parse_ib_reference(ib_path)
        if not is_server:
            return
        if not server or not name:
            raise ValidationError(f"Некорректный путь серверной ИБ: {ib_path}")
        if not self.env_vars.get('V8_IB_SERVER'):
            self.env_vars['V8_IB_SERVER'] = server
        if not self.env_vars.get('V8_IB_NAME'):
            self.env_vars['V8_IB_NAME'] = name

    def _create_file_ib_if_missing(self, ib_dir: Path, log_file: Path) -> None:
        if (ib_dir / '1cv8.1cd').exists():
            return
        ib_connection = self._make_ib_connection_string(ib_dir)
        result = self.v8_tool.create_infobase(ib_connection, log_file)
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при создании ИБ",
                temp_dir=self.temp_dir
            )

    def _load_xml_into_file_ib(self, ib_dir: Path, xml_path: Path, log_file: Path) -> None:
        result = self.v8_tool.load_config_from_files(
            ib_connection=str(ib_dir),
            xml_path=xml_path,
            log_file=log_file
        )
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при загрузке конфигурации из XML",
                temp_dir=self.temp_dir
            )

    def _dump_file_ib_to_cf(self, ib_connection: Union[str, Path], output_file: Path, log_file: Path) -> None:
        result = self.v8_tool.dump_config(
            ib_connection=str(ib_connection),
            output_file=output_file,
            log_file=log_file
        )
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при выгрузке конфигурации в CF файл",
                temp_dir=self.temp_dir
            )

    def _dump_file_ib_to_xml(self, ib_connection: Union[str, Path], output_dir: Path, log_file: Path) -> None:
        result = self.v8_tool.dump_config_to_files(
            ib_connection=str(ib_connection),
            output_dir=output_dir,
            log_file=log_file
        )
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при выгрузке конфигурации в XML",
                temp_dir=self.temp_dir
            )
    
    def _convert_from_edt(self) -> int:
        """
        Конвертирует конфигурацию из EDT проекта в CF файл.
        
        Последовательность: EDT -> XML -> IB -> CF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        script_name = self.env_vars.get('ScriptName', '').lower()
        if script_name == 'conf2xml':
            self.log_info("Конвертация EDT -> XML")
            self.report_progress("Конвертация EDT -> XML", 0)
        elif script_name == 'conf2ib':
            self.log_info("Конвертация EDT -> IB")
            self.report_progress("Конвертация EDT -> IB", 0)
        else:
            self.log_info("Конвертация EDT -> CF")
            self.report_progress("Конвертация EDT -> CF", 0)
        
        # Проверяем доступность EDT инструмента
        if not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (1cedtcli/ring) не найден. " +
                "Установите EDT или укажите путь в переменной RING_TOOL/EDT_TOOL"
            )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        try:
            if script_name == 'conf2xml':
                edt_workspace = self.temp_dir / 'edt_ws'
                _ = edt_workspace.mkdir(exist_ok=True)
                dst_dir = Path(self.dst_path)
                self._maybe_clean_dir(dst_dir, 'V8_CONF_CLEAN_DST', 'V8_CONF_CLEAN_DST')
                _ = dst_dir.mkdir(parents=True, exist_ok=True)
                self.start_stage("Экспорт EDT проекта в XML")
                self.report_progress("Экспорт EDT -> XML", 10)
                result = self.edt_tool.export_to_xml(
                    edt_project=Path(self.src_path),
                    xml_output=dst_dir,
                    workspace=edt_workspace
                )
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при экспорте EDT проекта в XML",
                        temp_dir=self.temp_dir
                    )
                config_xml = dst_dir / 'Configuration.xml'
                if not config_xml.exists():
                    raise ToolExecutionError(
                        f"Файл Configuration.xml не создан: {config_xml}",
                        temp_dir=self.temp_dir
                    )
                self.end_stage("EDT проект успешно экспортирован в XML")
                self.report_progress("Конвертация завершена", 100)
                return 0
            elif script_name == 'conf2ib':
                temp_xml = self.temp_dir / 'tmp_xml'
                self._ensure_dir(temp_xml)
                edt_workspace = self.temp_dir / 'edt_ws'
                self._ensure_dir(edt_workspace)
                self.start_stage("Экспорт EDT проекта в XML")
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
                self.start_stage("Загрузка конфигурации в ИБ")
                self.report_progress("Загрузка XML -> IB", 50)
                ib_dir = self._get_file_ib_path_from_value(self.dst_path)
                if self.convert_tool == 'ibcmd':
                    if not self.ibcmd_tool.is_available():
                        raise ToolNotFoundError(
                            "ibcmd.exe не найден. " +
                            "Установите платформу 1С или укажите путь в переменной IBCMD_TOOL"
                        )
                    if ib_dir is None:
                        # Серверная ИБ: используем ibcmd с серверными параметрами
                        self._set_server_ib_env(self.dst_path)
                        result = self.ibcmd_tool.import_config_from_xml(
                            db_path=Path('.'),
                            xml_path=temp_xml,
                            use_server=True,
                        )
                    else:
                        # Файловая ИБ
                        self._ensure_dir(ib_dir)
                        if (ib_dir / '1cv8.1cd').exists():
                            result = self.ibcmd_tool.import_config_from_xml(
                                db_path=ib_dir,
                                xml_path=temp_xml,
                                use_server=False,
                            )
                        else:
                            result = self.ibcmd_tool.create_infobase_with_config(
                                db_path=ib_dir,
                                xml_path=temp_xml
                            )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при создании ИБ и загрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                else:
                    if ib_dir is None:
                        load_log = self.temp_dir / 'load_config_server.log'
                        result = self.v8_tool.load_config_from_files(
                            ib_connection=self.dst_path,
                            xml_path=temp_xml,
                            log_file=load_log
                        )
                    else:
                        self._ensure_dir(ib_dir)
                        create_log = self.temp_dir / 'create_ib.log'
                        self._create_file_ib_if_missing(ib_dir, create_log)
                        load_log = self.temp_dir / 'load_config.log'
                        self._load_xml_into_file_ib(ib_dir, temp_xml, load_log)
                self.end_stage("Конфигурация успешно загружена в ИБ")
                self.report_progress("Конвертация завершена", 100)
                return 0
            else:
                temp_xml = self.temp_dir / 'tmp_xml'
                self._ensure_dir(temp_xml)
                temp_db = self.temp_dir / 'tmp_db'
                self._ensure_dir(temp_db)
                edt_workspace = self.temp_dir / 'edt_ws'
                self._ensure_dir(edt_workspace)
                self.start_stage("Этап 1/3: Экспорт EDT проекта в XML")
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
                self.report_progress("Экспорт EDT -> XML завершен", 40)
                if self.convert_tool == 'ibcmd':
                    if not self.ibcmd_tool.is_available():
                        raise ToolNotFoundError(
                            "ibcmd.exe не найден. " +
                            "Установите платформу 1С или укажите путь в переменной IBCMD_TOOL"
                        )
                    self.start_stage("Этап 2/3: Создание временной ИБ и загрузка конфигурации")
                    self.report_progress("Загрузка XML -> IB", 50)
                    result = self.ibcmd_tool.create_infobase_with_config(
                        db_path=temp_db,
                        xml_path=temp_xml
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при создании ИБ и загрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                    self.end_stage("Конфигурация успешно загружена в ИБ")
                    self.report_progress("Загрузка XML -> IB завершена", 70)
                    self.start_stage("Этап 3/3: Выгрузка конфигурации в CF файл")
                    self.report_progress("Выгрузка IB -> CF", 80)
                    output_file = Path(self.dst_path)
                    result = self.ibcmd_tool.save_config(
                        db_path=temp_db,
                        output_file=output_file
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при выгрузке конфигурации в CF файл через ibcmd",
                            temp_dir=self.temp_dir
                        )
                else:
                    if not self.v8_tool.is_available():
                        raise ToolNotFoundError(
                            "1cv8.exe не найден. " +
                            "Установите платформу 1С или укажите путь в переменной V8_TOOL"
                        )
                    self.start_stage("Этап 2/3: Создание временной ИБ и загрузка конфигурации")
                    self.report_progress("Загрузка XML -> IB", 50)
                    create_ib_log = self.temp_dir / 'create_ib.log'
                    load_config_log = self.temp_dir / 'load_config.log'
                    self._create_file_ib_if_missing(temp_db, create_ib_log)
                    self._load_xml_into_file_ib(temp_db, temp_xml, load_config_log)
                    self.end_stage("Конфигурация успешно загружена в ИБ")
                    self.report_progress("Загрузка XML -> IB завершена", 70)
                    self.start_stage("Этап 3/3: Выгрузка конфигурации в CF файл")
                    self.report_progress("Выгрузка IB -> CF", 80)
                    output_file = Path(self.dst_path)
                    dump_log_file = self.temp_dir / 'dump_config.log'
                    self._dump_file_ib_to_cf(temp_db, output_file, dump_log_file)
                if not output_file.exists():
                    raise ToolExecutionError(
                        f"Выходной файл не создан: {output_file}",
                        temp_dir=self.temp_dir
                    )
                self.end_stage(f"Конфигурация успешно выгружена в: {output_file}")
                self.report_progress("Конвертация завершена", 100)
                return 0
        except Exception as e:
            self.log_error(f"Ошибка при конвертации из EDT: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise
    
    def _convert_from_xml(self) -> int:
        """
        Конвертирует конфигурацию из XML файлов в CF файл.
        
        Последовательность: XML -> IB -> CF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        script_name = self.env_vars.get('ScriptName', '').lower()
        if script_name == 'conf2ib':
            self.log_info("Конвертация XML -> IB")
            self.report_progress("Конвертация XML -> IB", 0)
        elif script_name == 'conf2xml':
            self.log_info("Конвертация XML -> XML")
            self.report_progress("Конвертация XML -> XML", 0)
        else:
            self.log_info("Конвертация XML -> CF")
            self.report_progress("Конвертация XML -> CF", 0)
        
        if script_name == 'conf2ib':
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
        elif script_name != 'conf2xml':
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
            if script_name == 'conf2ib':
                ib_dir = self._get_file_ib_path_from_value(self.dst_path)
                if self.convert_tool == 'ibcmd':
                    self.report_progress("Создание ИБ и загрузка конфигурации", 20)
                    src_path_obj = Path(self.src_path)
                    if ib_dir is None:
                        # Серверная ИБ: используем ibcmd
                        self._set_server_ib_env(self.dst_path)
                        if src_path_obj.suffix.lower() == '.cf':
                            result = self.ibcmd_tool.import_config_from_cf(
                                db_path=Path('.'),
                                cf_file=src_path_obj,
                                use_server=True,
                            )
                        else:
                            result = self.ibcmd_tool.import_config_from_xml(
                                db_path=Path('.'),
                                xml_path=src_path_obj,
                                use_server=True,
                            )
                    else:
                        # Файловая ИБ
                        self._ensure_dir(ib_dir)
                        if (ib_dir / '1cv8.1cd').exists():
                            if src_path_obj.suffix.lower() == '.cf':
                                result = self.ibcmd_tool.import_config_from_cf(
                                    db_path=ib_dir,
                                    cf_file=src_path_obj,
                                    use_server=False,
                                )
                            else:
                                result = self.ibcmd_tool.import_config_from_xml(
                                    db_path=ib_dir,
                                    xml_path=src_path_obj,
                                    use_server=False,
                                )
                        else:
                            # Создание файловой ИБ с конфигурацией из XML
                            result = self.ibcmd_tool.create_infobase_with_config(
                                db_path=ib_dir,
                                xml_path=src_path_obj
                            )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при создании ИБ и загрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                    self.end_stage("ИБ создана и конфигурация загружена")
                    self.report_progress("Конвертация завершена", 100)
                    return 0
                else:
                    if ib_dir is None:
                        load_log = self.temp_dir / 'load_config_server.log'
                        result = self.v8_tool.load_config_from_files(
                            ib_connection=self.dst_path,
                            xml_path=Path(self.src_path),
                            log_file=load_log
                        )
                        if result != 0:
                            raise ToolExecutionError(
                                "Ошибка при загрузке конфигурации из XML в серверную ИБ",
                                temp_dir=self.temp_dir
                            )
                        self.end_stage("Конфигурация загружена в серверную ИБ")
                        self.report_progress("Конвертация завершена", 100)
                        return 0
                    else:
                        create_log = self.temp_dir / 'create_ib.log'
                        self._ensure_dir(ib_dir)
                        self._create_file_ib_if_missing(ib_dir, create_log)
                        load_log = self.temp_dir / 'load_config.log'
                        self._load_xml_into_file_ib(ib_dir, Path(self.src_path), load_log)
                        self.end_stage("Конфигурация загружена в ИБ")
                        self.report_progress("Конвертация завершена", 100)
                        return 0
            elif script_name == 'conf2xml':
                import shutil
                dst_dir = Path(self.dst_path)
                src_dir = Path(self.src_path)
                if str(dst_dir.resolve()) == str(src_dir.resolve()):
                    self.report_progress("Конвертация завершена", 100)
                    return 0
                self._ensure_dir(dst_dir)
                self._maybe_clean_dir(dst_dir, 'V8_CONF_CLEAN_DST', 'V8_CONF_CLEAN_DST')
                for item in src_dir.iterdir():
                    target = dst_dir / item.name
                    if item.is_dir():
                        if target.exists():
                            pass
                        _ = shutil.copytree(item, target, dirs_exist_ok=True)
                    else:
                        _ = shutil.copy2(item, target)
                self.report_progress("Конвертация завершена", 100)
                return 0
            else:
                temp_db = self.temp_dir / 'tmp_db'
                self._ensure_dir(temp_db)
                output_file = Path(self.dst_path)
                if self.convert_tool == 'ibcmd':
                    self.log_info("Использование ibcmd для конвертации XML -> CF")
                    self.report_progress("Создание ИБ и загрузка конфигурации", 20)
                    result = self.ibcmd_tool.create_infobase_with_config(
                        db_path=temp_db,
                        xml_path=Path(self.src_path)
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при создании ИБ и загрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                    self.end_stage("ИБ создана и конфигурация загружена")
                    self.report_progress("Сохранение конфигурации в CF", 60)
                    result = self.ibcmd_tool.save_config(
                        db_path=temp_db,
                        output_file=output_file
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при сохранении конфигурации в CF файл через ibcmd",
                            temp_dir=self.temp_dir
                        )
                else:
                    self.log_info("Использование designer для конвертации XML -> CF")
                    self.start_stage("Этап 1/3: Создание временной ИБ")
                    self.report_progress("Создание ИБ", 20)
                    log_file = self.temp_dir / 'create_ib.log'
                    self._create_file_ib_if_missing(temp_db, log_file)
                    self.end_stage("Временная ИБ создана")
                    self.start_stage("Этап 2/3: Загрузка конфигурации из XML")
                    self.report_progress("Загрузка XML -> IB", 40)
                    load_log_file = self.temp_dir / 'load_config.log'
                    self._load_xml_into_file_ib(temp_db, Path(self.src_path), load_log_file)
                    self.end_stage("Конфигурация загружена в ИБ")
                    self.start_stage("Этап 3/3: Выгрузка конфигурации в CF файл")
                    self.report_progress("Выгрузка IB -> CF", 70)
                    dump_log_file = self.temp_dir / 'dump_config.log'
                    self._dump_file_ib_to_cf(temp_db, output_file, dump_log_file)
                if not output_file.exists():
                    raise ToolExecutionError(
                        f"Выходной файл не создан: {output_file}",
                        temp_dir=self.temp_dir
                    )
                self.end_stage(f"Конфигурация успешно выгружена в: {output_file}")
                self.report_progress("Конвертация завершена", 100)
                return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации XML -> CF: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise
        
        return 0
    
    def _convert_from_ib(self) -> int:
        """
        Конвертирует конфигурацию из информационной базы в CF файл.
        
        Последовательность: IB -> CF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        script_name = self.env_vars.get('ScriptName', '').lower()
        if script_name == 'conf2xml':
            self.log_info("Конвертация IB -> XML")
            self.report_progress("Конвертация IB -> XML", 0)
        elif script_name == 'conf2ib':
            self.log_info("Конвертация IB -> IB")
            self.report_progress("Конвертация IB -> IB", 0)
        elif script_name == 'ib2dt':
            self.log_info("Конвертация IB -> DT")
            self.report_progress("Конвертация IB -> DT", 0)
        else:
            self.log_info("Конвертация IB -> CF")
            self.report_progress("Конвертация IB -> CF", 0)
        
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
        if self.convert_tool == 'ibcmd' and self.src_path.startswith('/S'):
            self._set_server_ib_env(self.src_path)
        
        try:
            if script_name == 'ib2dt':
                output_file = Path(self.dst_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                ib_dir = self._get_file_ib_path_from_value(self.src_path)
                if self.convert_tool == 'ibcmd':
                    db_path = Path('.') if ib_dir is None else ib_dir
                    result = self.ibcmd_tool.dump_infobase(
                        db_path,
                        output_file,
                        use_server=ib_dir is None
                    )
                else:
                    ib_connection = self.src_path if ib_dir is None else str(ib_dir)
                    result = self.v8_tool.dump_infobase(
                        ib_connection, output_file, self.temp_dir / 'dump_ib.log'
                    )
                if result != 0 or not output_file.exists():
                    raise ToolExecutionError(
                        "Ошибка при выгрузке информационной базы в DT",
                        temp_dir=self.temp_dir
                    )
                self.report_progress("Конвертация завершена", 100)
                return 0
            if script_name == 'conf2xml':
                ib_dir = self._get_file_ib_path_from_value(self.src_path)
                output_dir = Path(self.dst_path)
                self._ensure_dir(output_dir)
                self._maybe_clean_dir(output_dir, 'V8_CONF_CLEAN_DST', 'V8_CONF_CLEAN_DST')
                dump_log_file = self.temp_dir / 'dump_xml.log'
                if self.convert_tool == 'ibcmd':
                    self.log_info("Использование ibcmd для выгрузки конфигурации")
                    self.report_progress("Выгрузка конфигурации", 30)
                    if self.src_path.startswith('/F'):
                        db_path = Path(self.src_path[2:])
                    else:
                        db_path = Path(self.src_path)
                    result = self.ibcmd_tool.export_config_to_files(
                        db_path=db_path,
                        output_dir=output_dir
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при выгрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                else:
                    ib_conn = self.src_path if ib_dir is None else str(ib_dir)
                    self._dump_file_ib_to_xml(ib_conn, output_dir, dump_log_file)
                config_xml = output_dir / 'Configuration.xml'
                if not config_xml.exists():
                    raise ToolExecutionError(
                        f"Файл Configuration.xml не создан: {config_xml}",
                        temp_dir=self.temp_dir
                    )
                self.log_success(f"Конфигурация успешно выгружена в XML: {output_dir}")
                self.report_progress("Конвертация завершена", 100)
                return 0
            elif script_name == 'conf2ib':
                dst = self.dst_path
                src_norm = self.src_path
                dst_norm = dst
                if src_norm == dst_norm or (src_norm.startswith('/F') and dst_norm.startswith('/F') and src_norm[2:] == dst_norm[2:]):
                    self.report_progress("Конвертация завершена", 100)
                    return 0
                raise ValidationError("Конвертация IB -> IB в другую базу не поддерживается в текущей реализации")
            elif script_name == 'conf2edt':
                ib_dir = self._get_file_ib_path_from_value(self.src_path)
                if not self.edt_tool.is_available():
                    raise ToolNotFoundError(
                        "EDT инструмент (1cedtcli/ring) не найден. " +
                        "Установите EDT или укажите путь в переменной RING_TOOL/EDTCLI_TOOL"
                    )
                self.start_stage("Этап 1/2: Выгрузка конфигурации из ИБ в XML...")
                self.report_progress("Выгрузка IB -> XML", 40)
                temp_xml = self.temp_dir / 'tmp_xml'
                self._ensure_dir(temp_xml)
                dump_log_file = self.temp_dir / 'dump_xml.log'
                if self.convert_tool == 'ibcmd':
                    self.log_info("Использование ibcmd для выгрузки конфигурации")
                    self.report_progress("Выгрузка конфигурации", 40)
                    if self.src_path.startswith('/F'):
                        db_path = Path(self.src_path[2:])
                    else:
                        db_path = Path(self.src_path)
                    result = self.ibcmd_tool.export_config_to_files(
                        db_path=db_path,
                        output_dir=temp_xml
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при выгрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                else:
                    ib_conn = self.src_path if ib_dir is None else str(ib_dir)
                    self._dump_file_ib_to_xml(ib_conn, temp_xml, dump_log_file)
                self.end_stage("Конфигурация выгружена в XML")
                
                self.start_stage("Этап 2/2: Импорт конфигурации в EDT проект...")
                self.report_progress("Импорт XML -> EDT", 70)
                output_dir = Path(self.dst_path)
                edt_workspace = self.temp_dir / 'edt_ws'
                self._ensure_dir(edt_workspace)
                result = self.edt_tool.import_configuration_files_to_edt_project(
                    xml_source_path=temp_xml,
                    edt_project_path=output_dir,
                    workspace_path=edt_workspace,
                    entity_type="конфигурации"
                )
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при импорте конфигурации в EDT",
                        temp_dir=self.temp_dir
                    )
                self.end_stage(f"Конфигурация успешно выгружена в EDT: {output_dir}")
                self.report_progress("Конвертация завершена", 100)
                return 0
            else:
                output_file = Path(self.dst_path)
                if self.convert_tool != 'ibcmd':
                    self.log_info("Использование designer для выгрузки конфигурации")
                    self.report_progress("Выгрузка конфигурации", 30)
                    log_file = self.temp_dir / 'dump_config.log'
                    ib_dir = self._get_file_ib_path_from_value(self.src_path)
                    ib_conn = self.src_path if ib_dir is None else str(ib_dir)
                    self._dump_file_ib_to_cf(ib_conn, output_file, log_file)
                else:
                    self.log_info("Использование ibcmd для выгрузки конфигурации")
                    self.report_progress("Выгрузка конфигурации", 30)
                    if self.src_path.startswith('/F'):
                        db_path = Path(self.src_path[2:])
                    else:
                        db_path = Path(self.src_path)
                    result = self.ibcmd_tool.save_config(
                        db_path=db_path,
                        output_file=output_file
                    )
                    if result != 0:
                        raise ToolExecutionError(
                            "Ошибка при выгрузке конфигурации через ibcmd",
                            temp_dir=self.temp_dir
                        )
                if not output_file.exists():
                    raise ToolExecutionError(
                        f"Выходной файл не создан: {output_file}",
                        temp_dir=self.temp_dir
                    )
                self.log_success(f"Конфигурация успешно выгружена в: {output_file}")
                self.report_progress("Конвертация завершена", 100)
                return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации IB -> CF: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise

    
    def _convert_from_cf(self) -> int:
        """
        Конвертирует конфигурацию из CF файла в XML или EDT.
        
        Последовательность: CF -> IB -> XML/EDT
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        # Получаем тип конвертации
        script_name = self.env_vars.get('ScriptName', '').lower()
        
        if script_name == 'conf2xml':
            self.log_info("Конвертация CF -> XML")
            self.report_progress("Конвертация CF -> XML", 0)
            target_format = "XML"
        elif script_name == 'conf2edt':
            self.log_info("Конвертация CF -> EDT")
            self.report_progress("Конвертация CF -> EDT", 0)
            target_format = "EDT"
        elif script_name == 'conf2ib':
            self.log_info("Конвертация CF -> IB")
            self.report_progress("Конвертация CF -> IB", 0)
            target_format = "IB"
        else:
            raise ValidationError(
                f"Неподдерживаемый тип конвертации из CF: {script_name}. " +
                f"Поддерживаются: conf2xml, conf2edt"
            )
        
        # Проверяем доступность инструментов
        use_ibcmd_for_intermediate_steps = self.convert_tool == 'ibcmd'

        if use_ibcmd_for_intermediate_steps:
            if not self.ibcmd_tool.is_available():
                raise ToolNotFoundError(
                    "ibcmd.exe не найден. " +
                    "Установите платформу 1С или укажите путь в переменной IBCMD_TOOL"
                )
        elif not self.v8_tool.is_available():
            raise ToolNotFoundError(
                "1cv8.exe не найден. " +
                "Установите платформу 1С или укажите путь в переменной V8_TOOL"
            )

        if target_format == "EDT" and not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (1cedtcli/ring) не найден. " +
                "Установите EDT или укажите путь в переменной RING_TOOL/EDTCLI_TOOL"
            )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        try:
            # Прямая загрузка CF в целевую ИБ
            if target_format == "IB":
                cf_file = Path(self.src_path)
                self.start_stage("Загрузка CF в целевую ИБ")
                self.report_progress("Загрузка конфигурации", 40)
                if self.convert_tool == 'ibcmd' and self.ibcmd_tool.is_available():
                    dst_is_server = self._get_file_ib_path_from_value(self.dst_path) is None
                    if dst_is_server:
                        self._set_server_ib_env(self.dst_path)
                        result = self.ibcmd_tool.import_config_from_cf(
                            db_path=Path('.'),
                            cf_file=cf_file,
                            use_server=True,
                        )
                    else:
                        dst_ib_dir = self._get_file_ib_path_from_value(self.dst_path)
                        assert dst_ib_dir is not None
                        self._ensure_dir(dst_ib_dir)
                        result = self.ibcmd_tool.import_config_from_cf(
                            db_path=dst_ib_dir,
                            cf_file=cf_file,
                            use_server=False,
                        )
                else:
                    load_log_file = self.temp_dir / 'load_cf.log'
                    dst_is_server = self._get_file_ib_path_from_value(self.dst_path) is None
                    if dst_is_server:
                        result = self.v8_tool.load_config_from_cf(
                            ib_connection=self.dst_path,
                            cf_file=cf_file,
                            log_file=load_log_file
                        )
                    else:
                        dst_ib_dir = self._get_file_ib_path_from_value(self.dst_path)
                        assert dst_ib_dir is not None
                        self._ensure_dir(dst_ib_dir)
                        result = self.v8_tool.load_config_from_cf(
                            ib_connection=str(dst_ib_dir),
                            cf_file=cf_file,
                            log_file=load_log_file
                        )
                if result != 0:
                    raise ToolExecutionError("Ошибка при загрузке CF файла в целевую ИБ", temp_dir=self.temp_dir)
                self.end_stage("Конфигурация успешно загружена в ИБ")
                self.report_progress("Конвертация завершена", 100)
                return 0
            
            # Этап 1: Создаем временную ИБ
            if self.convert_tool != 'ibcmd':
                self.start_stage("Этап 1/3: Создание временной ИБ...")
                self.report_progress("Создание временной ИБ", 10)
            
            temp_db = self.temp_dir / 'tmp_db'
            _ = temp_db.mkdir(exist_ok=True)
            
            if self.convert_tool == 'ibcmd':
                self._ensure_dir(temp_db)
            else:
                ib_path_str = str(temp_db).replace('\\', '/')
                ib_connection_string = f'File={ib_path_str};'
                log_file = self.temp_dir / 'create_ib.log'
                
                result = self.v8_tool.create_infobase(ib_connection_string, log_file)
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при создании временной ИБ",
                        temp_dir=self.temp_dir
                    )
            
            if self.convert_tool != 'ibcmd':
                self.end_stage("Временная ИБ создана")
                self.report_progress("Временная ИБ создана", 30)
            
            # Этап 2: Загружаем конфигурацию из CF в ИБ
            if self.convert_tool == 'ibcmd':
                self.start_stage("Этап 1/2: Создание временной ИБ с загрузкой конфигурации из CF файла...")
                self.report_progress("Создание временной ИБ и загрузка конфигурации", 20)
            else:
                self.start_stage("Этап 2/3: Загрузка конфигурации из CF файла...")
                self.report_progress("Загрузка конфигурации", 40)
            
            cf_file = Path(self.src_path)
            if self.convert_tool == 'ibcmd':
                result = self.ibcmd_tool.create_infobase_with_config(
                    db_path=temp_db,
                    cf_file=cf_file
                )
            else:
                load_log_file = self.temp_dir / 'load_cf.log'
                result = self.v8_tool.load_config_from_cf(
                    ib_connection=str(temp_db),
                    cf_file=cf_file,
                    log_file=load_log_file
                )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при загрузке CF файла в ИБ",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Конфигурация загружена в ИБ")
            self.report_progress("Конфигурация загружена", 60)
            
            # Этап 3: Выгружаем в целевой формат
            if target_format == "XML":
                if self.convert_tool == 'ibcmd':
                    self.start_stage("Этап 2/2: Выгрузка конфигурации в XML...")
                else:
                    self.start_stage("Этап 3/3: Выгрузка конфигурации в XML...")
                self.report_progress("Выгрузка в XML", 70)
                
                # Для XML сохраняем совместимость: V8_DST_PATH трактуется как корневой каталог,
                # внутри которого создается папка с именем исходного CF.
                cf_name = Path(self.src_path).stem
                output_dir = Path(self.dst_path) / cf_name
                self._maybe_clean_dir(output_dir, 'V8_CONF_CLEAN_DST', 'V8_CONF_CLEAN_DST')
                output_dir.mkdir(parents=True, exist_ok=True)
                
                dump_log_file = self.temp_dir / 'dump_xml.log'
                
                if self.convert_tool == 'ibcmd':
                    result = self.ibcmd_tool.export_config_to_files(
                        db_path=temp_db,
                        output_dir=output_dir
                    )
                else:
                    result = self.v8_tool.dump_config_to_files(
                        ib_connection=str(temp_db),
                        output_dir=output_dir,
                        log_file=dump_log_file
                    )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке конфигурации в XML",
                        temp_dir=self.temp_dir
                    )
                
                # Проверяем что XML файлы созданы
                config_xml = output_dir / 'Configuration.xml'
                if not config_xml.exists():
                    raise ToolExecutionError(
                        f"Файл Configuration.xml не создан: {config_xml}",
                        temp_dir=self.temp_dir
                    )
                
                self.end_stage(f"Конфигурация успешно выгружена в XML: {output_dir}")
                
            else:  # EDT
                if self.convert_tool == 'ibcmd':
                    self.start_stage("Этап 2/2: Выгрузка конфигурации в EDT...")
                else:
                    self.start_stage("Этап 3/3: Выгрузка конфигурации в EDT...")
                self.report_progress("Выгрузка в EDT", 70)
                
                output_dir = Path(self.dst_path)
                self._maybe_clean_dir(output_dir, 'V8_CONF_CLEAN_DST', 'V8_CONF_CLEAN_DST')
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Сначала выгружаем в XML
                temp_xml = self.temp_dir / 'tmp_xml'
                _ = temp_xml.mkdir(exist_ok=True)
                
                dump_log_file = self.temp_dir / 'dump_xml.log'
                if self.convert_tool == 'ibcmd':
                    result = self.ibcmd_tool.export_config_to_files(
                        db_path=temp_db,
                        output_dir=temp_xml
                    )
                else:
                    result = self.v8_tool.dump_config_to_files(
                        ib_connection=str(temp_db),
                        output_dir=temp_xml,
                        log_file=dump_log_file
                    )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке конфигурации в XML",
                        temp_dir=self.temp_dir
                    )
                
                # Затем импортируем XML в EDT
                edt_workspace = self.temp_dir / 'edt_ws'
                
                # Используем метод из EdtToolWrapper
                result = self.edt_tool.import_configuration_files_to_edt_project(
                    xml_source_path=temp_xml,
                    edt_project_path=output_dir,
                    workspace_path=edt_workspace,
                    entity_type="конфигурации"
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при импорте конфигурации в EDT",
                        temp_dir=self.temp_dir
                    )
                
                self.end_stage(f"Конфигурация успешно выгружена в EDT: {output_dir}")
            
            self.report_progress("Конвертация завершена", 100)
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации CF -> {target_format}: {e}")
            if self.temp_manager:
                self.temp_manager.preserve_on_error()
            raise

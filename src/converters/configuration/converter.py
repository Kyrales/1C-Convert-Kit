"""
Конвертер для конфигураций 1С.

Поддерживает конвертацию конфигураций между форматами:
- EDT -> CF
- XML -> CF
- IB -> CF
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
        self.convert_tool = env_vars.get('V8_CONVERT_TOOL', 'designer')
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
    
    def _validate_specific(self) -> None:
        """
        Специфичная валидация для конвертера конфигураций.
        
        Проверяет:
        - Для conf2cf: dst_path указывает на файл с расширением .cf
        - Для conf2xml, conf2edt: dst_path указывает на директорию
        
        Raises:
            ValidationError: Если параметры некорректны
        """
        # Получаем тип конвертации
        script_name = self.env_vars.get('ScriptName', '').lower()
        
        dst_path_obj = Path(self.dst_path)
        
        # Для конвертации в CF файл
        if script_name in ['conf2cf', 'conf2ib']:
            if dst_path_obj.suffix.lower() != '.cf':
                raise ValidationError(
                    f"V8_DST_PATH должен указывать на файл .cf для {script_name}, " +
                    f"получено: {self.dst_path}"
                )
        # Для конвертации в XML или EDT
        elif script_name in ['conf2xml', 'conf2edt']:
            # Для XML и EDT нужна директория, а не файл
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
            return self._convert_from_edt()
        elif source_type == SourceType.XML:
            return self._convert_from_xml()
        elif source_type in [SourceType.FILE_IB, SourceType.SERVER_IB]:
            return self._convert_from_ib()
        elif source_type == SourceType.CF_FILE:
            return self._convert_from_cf()
        else:
            raise ValidationError(
                f"Неподдерживаемый тип источника: {source_type.value}. " +
                f"Поддерживаются: EDT, XML, InfoBase, CF"
            )
    
    def _convert_from_edt(self) -> int:
        """
        Конвертирует конфигурацию из EDT проекта в CF файл.
        
        Последовательность: EDT -> XML -> IB -> CF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
        self.log_info("Конвертация EDT -> CF")
        self.report_progress("Конвертация EDT -> CF", 0)
        
        # Проверяем доступность EDT инструмента
        if not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (ring/edtcli) не найден. " +
                "Установите EDT или укажите путь в переменной RING_TOOL/EDT_TOOL"
            )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        # Создаем временные директории
        temp_xml = self.temp_dir / 'tmp_xml'
        _ = temp_xml.mkdir(exist_ok=True)
        
        temp_db = self.temp_dir / 'tmp_db'
        _ = temp_db.mkdir(exist_ok=True)
        
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
            self.report_progress("Экспорт EDT -> XML завершен", 40)
            
            # Этап 2: Загрузка XML -> IB
            self.start_stage("Этап 2/3: Создание временной ИБ и загрузка конфигурации...")
            self.report_progress("Загрузка XML -> IB", 50)
            
            # Формируем строку подключения к временной ИБ
            # Для CREATEINFOBASE используется формат: File=путь; (БЕЗ кавычек вокруг пути!)
            # Используем прямые слэши для совместимости
            temp_db_str = str(temp_db).replace('\\', '/')
            ib_connection_create = f'File={temp_db_str};'
            # Для DESIGNER передаем просто путь (метод добавит /F сам)
            ib_connection_designer = str(temp_db)
            create_ib_log = self.temp_dir / 'create_ib.log'
            load_config_log = self.temp_dir / 'load_config.log'
            
            # Создаем ИБ
            # Сообщение выводится внутри v8_tool.create_infobase()
            result = self.v8_tool.create_infobase(ib_connection_create, create_ib_log)
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при создании временной ИБ",
                    temp_dir=self.temp_dir
                )
            
            # Загружаем конфигурацию из XML
            # Сообщение выводится внутри v8_tool.load_config_from_files()
            result = self.v8_tool.load_config_from_files(
                ib_connection=ib_connection_designer,
                xml_path=temp_xml,
                log_file=load_config_log
            )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при загрузке конфигурации из XML",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Конфигурация успешно загружена в ИБ")
            self.report_progress("Загрузка XML -> IB завершена", 70)
            
            # Этап 3: Выгрузка IB -> CF
            self.start_stage("Этап 3/3: Выгрузка конфигурации в CF файл...")
            self.report_progress("Выгрузка IB -> CF", 80)
            
            output_file = Path(self.dst_path)
            dump_log_file = self.temp_dir / 'dump_config.log'
            
            result = self.v8_tool.dump_config(
                ib_connection=ib_connection_designer,
                output_file=output_file,
                log_file=dump_log_file
            )
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при выгрузке конфигурации в CF файл",
                    temp_dir=self.temp_dir
                )
            
            # Проверяем что файл создан
            if not output_file.exists():
                raise ToolExecutionError(
                    f"Выходной файл не создан: {output_file}",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage(f"Конфигурация успешно выгружена в: {output_file}")
            self.report_progress("Конвертация завершена", 100)
            
            return 0
            
        except Exception as e:
            self.log_error(f"Ошибка при конвертации EDT -> CF: {e}")
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
        self.log_info("Конвертация XML -> CF")
        self.report_progress("Конвертация XML -> CF", 0)
        
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
        
        # Создаем временную директорию для ИБ
        temp_db = self.temp_dir / 'tmp_db'
        _ = temp_db.mkdir(exist_ok=True)
        
        try:
            if self.convert_tool == 'ibcmd':
                # Используем ibcmd для конвертации
                self.log_info("Использование ibcmd для конвертации...")
                self.report_progress("Создание ИБ и загрузка конфигурации", 20)
                
                # ibcmd создает ИБ и загружает конфигурацию одной командой
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
                
                # Сохраняем конфигурацию в CF файл
                output_file = Path(self.dst_path)
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
                # Используем designer (1cv8.exe) для конвертации
                self.log_info("Использование designer для конвертации...")
                
                # Этап 1: Создание ИБ
                self.start_stage("Этап 1/3: Создание временной ИБ...")
                self.report_progress("Создание ИБ", 20)
                
                ib_connection = f"/F{temp_db}"
                log_file = self.temp_dir / 'create_ib.log'
                
                result = self.v8_tool.create_infobase(ib_connection, log_file)
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при создании временной ИБ",
                        temp_dir=self.temp_dir
                    )
                
                self.end_stage("Временная ИБ создана")
                
                # Этап 2: Загрузка конфигурации из XML
                self.start_stage("Этап 2/3: Загрузка конфигурации из XML...")
                self.report_progress("Загрузка XML -> IB", 40)
                
                load_log_file = self.temp_dir / 'load_config.log'
                result = self.v8_tool.load_config_from_files(
                    ib_connection=ib_connection,
                    xml_path=Path(self.src_path),
                    log_file=load_log_file
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при загрузке конфигурации из XML",
                        temp_dir=self.temp_dir
                    )
                
                self.end_stage("Конфигурация загружена в ИБ")
                
                # Этап 3: Выгрузка в CF
                self.start_stage("Этап 3/3: Выгрузка конфигурации в CF файл...")
                self.report_progress("Выгрузка IB -> CF", 70)
                
                output_file = Path(self.dst_path)
                dump_log_file = self.temp_dir / 'dump_config.log'
                
                result = self.v8_tool.dump_config(
                    ib_connection=ib_connection,
                    output_file=output_file,
                    log_file=dump_log_file
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке конфигурации в CF файл",
                        temp_dir=self.temp_dir
                    )
            
            # Проверяем что файл создан
            output_file = Path(self.dst_path)
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
    
    def _convert_from_ib(self) -> int:
        """
        Конвертирует конфигурацию из информационной базы в CF файл.
        
        Последовательность: IB -> CF
        
        Returns:
            int: Код возврата (0 - успех, 1 - ошибка)
        """
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
        
        try:
            output_file = Path(self.dst_path)
            
            # Формируем строку подключения
            if self.src_path.startswith('/S') or self.src_path.startswith('/F'):
                ib_connection = self.src_path
            else:
                ib_connection = f"/F{self.src_path}"
            
            self.log_info(f"Подключение к ИБ: {ib_connection}")
            
            if self.convert_tool == 'ibcmd':
                # Используем ibcmd для выгрузки
                self.log_info("Использование ibcmd для выгрузки конфигурации...")
                self.report_progress("Выгрузка конфигурации", 30)
                
                # Для ibcmd нужен путь к директории ИБ
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
                
            else:
                # Используем designer для выгрузки
                self.log_info("Использование designer для выгрузки конфигурации...")
                self.report_progress("Выгрузка конфигурации", 30)
                
                log_file = self.temp_dir / 'dump_config.log'
                
                result = self.v8_tool.dump_config(
                    ib_connection=ib_connection,
                    output_file=output_file,
                    log_file=log_file
                )
                
                if result != 0:
                    raise ToolExecutionError(
                        "Ошибка при выгрузке конфигурации через designer",
                        temp_dir=self.temp_dir
                    )
            
            # Проверяем что файл создан
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
        else:
            raise ValidationError(
                f"Неподдерживаемый тип конвертации из CF: {script_name}. " +
                f"Поддерживаются: conf2xml, conf2edt"
            )
        
        # Проверяем доступность инструментов
        if not self.v8_tool.is_available():
            raise ToolNotFoundError(
                "1cv8.exe не найден. " +
                "Установите платформу 1С или укажите путь в переменной V8_TOOL"
            )
        
        if target_format == "EDT" and not self.edt_tool.is_available():
            raise ToolNotFoundError(
                "EDT инструмент (ring/edtcli) не найден. " +
                "Установите EDT или укажите путь в переменной RING_TOOL/EDTCLI_TOOL"
            )
        
        # Проверяем что temp_dir создана
        assert self.temp_dir is not None, "temp_dir должна быть создана перед конвертацией"
        
        try:
            # Этап 1: Создаем временную ИБ
            self.start_stage("Этап 1/3: Создание временной ИБ...")
            self.report_progress("Создание временной ИБ", 10)
            
            temp_db = self.temp_dir / 'tmp_db'
            _ = temp_db.mkdir(exist_ok=True)
            
            ib_path_str = str(temp_db).replace('\\', '/')
            ib_connection_string = f'File={ib_path_str};'
            log_file = self.temp_dir / 'create_ib.log'
            
            result = self.v8_tool.create_infobase(ib_connection_string, log_file)
            
            if result != 0:
                raise ToolExecutionError(
                    "Ошибка при создании временной ИБ",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Временная ИБ создана")
            self.report_progress("Временная ИБ создана", 30)
            
            # Этап 2: Загружаем конфигурацию из CF в ИБ
            self.start_stage("Этап 2/3: Загрузка конфигурации из CF файла...")
            self.report_progress("Загрузка конфигурации", 40)
            
            cf_file = Path(self.src_path)
            load_log_file = self.temp_dir / 'load_cf.log'
            
            # Формируем команду загрузки CF
            ib_conn_str = f'File={ib_path_str};'
            cmd = [
                str(self.v8_tool.tool_path),
                'DESIGNER',
                '/IBConnectionString', ib_conn_str,
                '/DisableStartupDialogs',
                '/Out', str(load_log_file),
                '/LoadCfg', str(cf_file)
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
                    "Ошибка при загрузке CF файла в ИБ",
                    temp_dir=self.temp_dir
                )
            
            self.end_stage("Конфигурация загружена в ИБ")
            self.report_progress("Конфигурация загружена", 60)
            
            # Этап 3: Выгружаем в целевой формат
            if target_format == "XML":
                self.start_stage("Этап 3/3: Выгрузка конфигурации в XML...")
                self.report_progress("Выгрузка в XML", 70)
                
                # Определяем имя выходной директории
                cf_name = Path(self.src_path).stem
                output_dir = Path(self.dst_path) / cf_name
                output_dir.mkdir(parents=True, exist_ok=True)
                
                dump_log_file = self.temp_dir / 'dump_xml.log'
                
                # Формируем команду выгрузки в XML
                cmd = [
                    str(self.v8_tool.tool_path),
                    'DESIGNER',
                    '/IBConnectionString', ib_conn_str,
                    '/DisableStartupDialogs',
                    '/Out', str(dump_log_file),
                    '/DumpConfigToFiles', str(output_dir)
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
                self.start_stage("Этап 3/3: Выгрузка конфигурации в EDT...")
                self.report_progress("Выгрузка в EDT", 70)
                
                # Определяем имя выходной директории
                cf_name = Path(self.src_path).stem
                output_dir = Path(self.dst_path) / cf_name
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
                    '/DumpConfigToFiles', str(temp_xml)
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

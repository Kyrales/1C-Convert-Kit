"""
Абстракции для работы с инструментами 1С.

Содержит обертки для работы с 1cv8.exe (designer), ibcmd.exe и EDT инструментами.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, List

from .converter import Logger, ToolNotFoundError, ToolExecutionError


class ToolWrapper(ABC):
    """
    Базовый класс для оберток инструментов 1С.
    
    Args:
        env_vars: Словарь переменных окружения
        logger: Логгер для вывода сообщений
    """
    
    env_vars: Dict[str, str]
    logger: Logger
    tool_path: Optional[Path]
    
    def __init__(self, env_vars: Dict[str, str], logger: Logger):
        self.env_vars = env_vars
        self.logger = logger
        self.tool_path = None
    
    def _log_command(self, cmd: List[str]):
        """
        Выводит команду в лог если включен режим отладки.
        
        Args:
            cmd: Список аргументов команды
        """
        if self.logger.debug:
            # Формируем строку команды
            cmd_str = ' '.join(f'"{arg}"' if ' ' in str(arg) else str(arg) for arg in cmd)
            self.logger.debug_msg(f"Команда: {cmd_str}")
    
    @abstractmethod
    def find_tool(self) -> Optional[Path]:
        """
        Находит инструмент в системе.
        
        Returns:
            Path или None: Путь к инструменту или None если не найден
        """
        pass
    
    @abstractmethod
    def execute(self, *args: str, **kwargs: str) -> "subprocess.CompletedProcess[str]":
        """
        Выполняет команду инструмента.
        
        Args:
            *args: Позиционные аргументы команды
            **kwargs: Именованные аргументы команды
        
        Returns:
            CompletedProcess[str]: Результат выполнения команды
        """
        pass
    
    def is_available(self) -> bool:
        """
        Проверяет доступность инструмента.
        
        Returns:
            bool: True если инструмент доступен
        """
        if self.tool_path is None:
            self.tool_path = self.find_tool()
        return self.tool_path is not None


class V8ToolWrapper(ToolWrapper):
    """
    Обертка для работы с 1cv8.exe (Designer).
    
    Предоставляет методы для создания ИБ, загрузки/выгрузки конфигураций,
    работы с расширениями и внешними обработками.
    """
    
    def find_tool(self) -> Optional[Path]:
        """
        Находит 1cv8.exe в системе.
        
        Returns:
            Path или None: Путь к 1cv8.exe или None если не найден
        """
        # Проверяем переменную V8_TOOL
        if 'V8_TOOL' in self.env_vars:
            tool_path = Path(self.env_vars['V8_TOOL'].strip('"'))
            if tool_path.exists():
                return tool_path
        
        # Ищем по версии V8_VERSION
        version = self.env_vars.get('V8_VERSION', '8.3.23.2040')
        default_path = Path(f"C:/Program Files/1cv8/{version}/bin/1cv8.exe")
        if default_path.exists():
            return default_path
        
        # Альтернативный путь (x86)
        alt_path = Path(f"C:/Program Files (x86)/1cv8/{version}/bin/1cv8.exe")
        if alt_path.exists():
            return alt_path
        
        return None
    
    def execute(self, *args: str, **kwargs: str) -> "subprocess.CompletedProcess[str]":
        """
        Выполняет команду 1cv8.exe.
        
        Args:
            *args: Позиционные аргументы команды
            **kwargs: Именованные аргументы команды
        
        Returns:
            CompletedProcess[str]: Результат выполнения команды
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        # Реализация будет добавлена позже
        raise NotImplementedError("Метод execute будет реализован в следующих задачах")
    
    def create_infobase(self, ib_connection: str, log_file: Path) -> int:
        """
        Создает информационную базу.
        
        Args:
            ib_connection: Строка подключения к ИБ (например: File=C:/temp/db;)
            log_file: Путь к лог-файлу
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        self.logger.info(f"Создание информационной базы...")
        
        # Формируем команду как список аргументов
        # CREATEINFOBASE требует формат: File=path; (без кавычек вокруг пути)
        cmd = [
            str(self.tool_path),
            'CREATEINFOBASE',
            ib_connection,
            '/DisableStartupDialogs',
            f'/Out{log_file}'
        ]
        
        # Выводим команду в режиме отладки
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            # Проверяем лог на ошибки
            if log_file.exists():
                from .converter import ToolOutputParser
                errors = ToolOutputParser.parse_designer_log(log_file)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при создании ИБ",
                        tool_output=error_msg
                    )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")
    
    def load_config_from_files(
        self, 
        ib_connection: str, 
        xml_path: Path,
        log_file: Path, 
        extension_name: Optional[str] = None
    ) -> int:
        """
        Загружает конфигурацию или расширение из XML файлов.
        
        Args:
            ib_connection: Строка подключения к ИБ (путь к папке ИБ)
            xml_path: Путь к XML файлам
            log_file: Путь к лог-файлу
            extension_name: Имя расширения (если загружается расширение)
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        if extension_name:
            self.logger.info(f"Загрузка расширения '{extension_name}' из XML файлов...")
        else:
            self.logger.info(f"Загрузка конфигурации из XML файлов...")
        
        # Формируем команду как список аргументов
        # Используем /IBConnectionString для DESIGNER
        ib_path_str = str(ib_connection).replace('\\', '/')
        ib_conn_string = f'File={ib_path_str};'
        
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            f'/Out{log_file}',
            f'/LoadConfigFromFiles{xml_path}'
        ]
        
        if extension_name:
            cmd.extend(['-Extension', extension_name])
        
        # Добавляем учетные данные если указаны
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        if ib_user:
            cmd.extend([f'/N{ib_user}'])
        if ib_pwd:
            cmd.extend([f'/P{ib_pwd}'])
        
        # Выводим команду в режиме отладки
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            # Проверяем лог на ошибки
            if log_file.exists():
                from .converter import ToolOutputParser
                errors = ToolOutputParser.parse_designer_log(log_file)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при загрузке из XML",
                        tool_output=error_msg
                    )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")
    
    def dump_config(
        self, 
        ib_connection: str, 
        output_file: Path,
        log_file: Path, 
        extension_name: Optional[str] = None
    ) -> int:
        """
        Выгружает конфигурацию или расширение в .cf/.cfe файл.
        
        Args:
            ib_connection: Строка подключения к ИБ (путь к папке ИБ)
            output_file: Путь к выходному файлу (.cf или .cfe)
            log_file: Путь к лог-файлу
            extension_name: Имя расширения (если выгружается расширение)
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        if extension_name:
            self.logger.info(f"Выгрузка расширения '{extension_name}' в файл {output_file}...")
        else:
            self.logger.info(f"Выгрузка конфигурации в файл {output_file}...")
        
        # Формируем команду как список аргументов
        # Используем /IBConnectionString для DESIGNER
        ib_path_str = str(ib_connection).replace('\\', '/')
        ib_conn_string = f'File={ib_path_str};'
        
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            f'/Out{log_file}',
            f'/DumpCfg{output_file}'
        ]
        
        if extension_name:
            cmd.extend(['-Extension', extension_name])
        
        # Добавляем учетные данные если указаны
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        if ib_user:
            cmd.extend([f'/N{ib_user}'])
        if ib_pwd:
            cmd.extend([f'/P{ib_pwd}'])
        
        # Выводим команду в режиме отладки

        
        self._log_command(cmd)


        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            # Проверяем лог на ошибки
            if log_file.exists():
                from .converter import ToolOutputParser
                errors = ToolOutputParser.parse_designer_log(log_file)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при выгрузке конфигурации",
                        tool_output=error_msg
                    )
            
            # Проверяем что файл создан
            if not output_file.exists():
                raise ToolExecutionError(f"Выходной файл не создан: {output_file}")
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")
    
    def load_external_processor(
        self, 
        ib_connection: str, 
        xml_file: Path,
        output_dir: Path, 
        log_file: Path
    ) -> int:
        """
        Загружает внешнюю обработку/отчет из XML в EPF/ERF.
        
        Args:
            ib_connection: Строка подключения к ИБ (путь к папке ИБ)
            xml_file: Путь к XML файлу обработки/отчета
            output_dir: Директория для выходного файла
            log_file: Путь к лог-файлу
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        self.logger.info(f"Загрузка внешней обработки/отчета из {xml_file}...")
        
        # Формируем команду как список аргументов
        # Используем /IBConnectionString для DESIGNER
        ib_path_str = str(ib_connection).replace('\\', '/')
        ib_conn_string = f'File={ib_path_str};'
        
        # Команда /LoadExternalDataProcessorOrReportFromFiles требует два параметра:
        # 1. Путь к XML файлу обработки/отчета
        # 2. Путь к выходной директории (не файлу!)
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            f'/Out{log_file}',
            f'/LoadExternalDataProcessorOrReportFromFiles',
            str(xml_file),
            str(output_dir)
        ]
        
        # Добавляем учетные данные если указаны
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        if ib_user:
            cmd.extend([f'/N{ib_user}'])
        if ib_pwd:
            cmd.extend([f'/P{ib_pwd}'])
        
        # Выводим команду в режиме отладки

        
        self._log_command(cmd)


        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            # Проверяем лог на ошибки
            if log_file.exists():
                from .converter import ToolOutputParser
                errors = ToolOutputParser.parse_designer_log(log_file)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при загрузке обработки/отчета",
                        tool_output=error_msg
                    )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")


class IbcmdToolWrapper(ToolWrapper):
    """
    Обертка для работы с ibcmd.exe.
    
    Предоставляет методы для создания ИБ и сохранения конфигураций.
    """
    
    def find_tool(self) -> Optional[Path]:
        """
        Находит ibcmd.exe в системе.
        
        Returns:
            Path или None: Путь к ibcmd.exe или None если не найден
        """
        # Проверяем переменную IBCMD_TOOL
        if 'IBCMD_TOOL' in self.env_vars:
            tool_path = Path(self.env_vars['IBCMD_TOOL'].strip('"'))
            if tool_path.exists():
                return tool_path
        
        # Ищем по версии V8_VERSION
        version = self.env_vars.get('V8_VERSION', '8.3.23.2040')
        default_path = Path(f"C:/Program Files/1cv8/{version}/bin/ibcmd.exe")
        if default_path.exists():
            return default_path
        
        # Альтернативный путь (x86)
        alt_path = Path(f"C:/Program Files (x86)/1cv8/{version}/bin/ibcmd.exe")
        if alt_path.exists():
            return alt_path
        
        return None
    
    def execute(self, *args: str, **kwargs: str) -> "subprocess.CompletedProcess[str]":
        """
        Выполняет команду ibcmd.exe.
        
        Args:
            *args: Позиционные аргументы команды
            **kwargs: Именованные аргументы команды
        
        Returns:
            CompletedProcess[str]: Результат выполнения команды
        """
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")
        
        # Реализация будет добавлена позже
        raise NotImplementedError("Метод execute будет реализован в следующих задачах")
    
    def create_infobase_with_config(self, db_path: Path, xml_path: Path) -> int:
        """
        Создает ИБ и загружает конфигурацию из XML.
        
        Args:
            db_path: Путь к создаваемой ИБ
            xml_path: Путь к XML файлам конфигурации
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")
        
        self.logger.info(f"Создание ИБ с конфигурацией из XML...")
        
        # Получаем путь к данным ibcmd
        ibcmd_data = self.env_vars.get('IBCMD_DATA', str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data'))
        
        # Команда: ibcmd infobase create --data=<data> --db-path=<path> --create-database --import=<xml>
        cmd = [
            str(self.tool_path),
            'infobase', 'create',
            f'--data={ibcmd_data}',
            f'--db-path={db_path}',
            '--create-database',
            f'--import={xml_path}'
        ]
        
        # Выводим команду в режиме отладки

        
        self._log_command(cmd)


        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    f"Ошибка при создании ИБ с конфигурацией",
                    tool_output=result.stderr or result.stdout
                )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")
    
    def save_config(
        self, 
        db_path: Path, 
        output_file: Path,
        extension_name: Optional[str] = None
    ) -> int:
        """
        Сохраняет конфигурацию или расширение в файл.
        
        Args:
            db_path: Путь к ИБ
            output_file: Путь к выходному файлу (.cf или .cfe)
            extension_name: Имя расширения (если сохраняется расширение)
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")
        
        if extension_name:
            self.logger.info(f"Сохранение расширения '{extension_name}' в файл {output_file}...")
        else:
            self.logger.info(f"Сохранение конфигурации в файл {output_file}...")
        
        # Получаем путь к данным ibcmd
        ibcmd_data = self.env_vars.get('IBCMD_DATA', str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data'))
        
        # Получаем учетные данные
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        
        # Проверяем тип ИБ (файловая или серверная)
        ib_server = self.env_vars.get('V8_IB_SERVER', '')
        
        if ib_server:
            # Серверная ИБ
            ib_name = self.env_vars.get('V8_IB_NAME', '')
            db_srv_dbms = self.env_vars.get('V8_DB_SRV_DBMS', 'MSSQLServer')
            db_srv_usr = self.env_vars.get('V8_DB_SRV_USR', '')
            db_srv_pwd = self.env_vars.get('V8_DB_SRV_PWD', '')
            
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'save',
                f'--data={ibcmd_data}',
                f'--dbms={db_srv_dbms}',
                f'--db-server={ib_server}',
                f'--db-name={ib_name}',
                f'--db-user={db_srv_usr}',
                f'--db-pwd={db_srv_pwd}',
                f'--user={ib_user}',
                f'--password={ib_pwd}',
                str(output_file)
            ]
        else:
            # Файловая ИБ
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'save',
                f'--data={ibcmd_data}',
                f'--db-path={db_path}',
                f'--user={ib_user}',
                f'--password={ib_pwd}',
                str(output_file)
            ]
        
        # Добавляем параметр расширения если указан
        if extension_name:
            cmd.extend(['--extension', extension_name])
        
        # Выводим команду в режиме отладки

        
        self._log_command(cmd)


        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    f"Ошибка при сохранении конфигурации",
                    tool_output=result.stderr or result.stdout
                )
            
            # Проверяем что файл создан
            if not output_file.exists():
                raise ToolExecutionError(f"Выходной файл не создан: {output_file}")
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")


class EdtToolWrapper(ToolWrapper):
    """
    Обертка для работы с EDT инструментами (ring / edtcli).
    
    Предоставляет методы для экспорта EDT проектов в XML.
    """
    
    use_ring: bool
    use_edtcli: bool
    
    def __init__(self, env_vars: Dict[str, str], logger: Logger):
        super().__init__(env_vars, logger)
        self.use_ring = False
        self.use_edtcli = False
    
    def find_tool(self) -> Optional[Path]:
        """
        Находит ring или edtcli в системе.
        
        Returns:
            Path или None: Путь к инструменту или None если не найден
        """
        # Сначала ищем edtcli (приоритет выше, так как более надежный)
        edtcli_path = self._find_edtcli()
        if edtcli_path:
            self.use_edtcli = True
            return edtcli_path
        
        # Затем ищем ring
        ring_path = self._find_ring()
        if ring_path:
            self.use_ring = True
            return ring_path
        
        return None
    
    def _find_ring(self) -> Optional[Path]:
        """
        Ищет ring.bat в PATH.
        
        Returns:
            Path или None: Путь к ring.bat или None если не найден
        """
        # Проверяем переменную RING_TOOL
        if 'RING_TOOL' in self.env_vars:
            tool_path = Path(self.env_vars['RING_TOOL'].strip('"'))
            if tool_path.exists():
                return tool_path
        
        # Ищем в PATH
        try:
            result = subprocess.run(
                ['where', 'ring.bat'],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                ring_path = Path(result.stdout.strip().split('\n')[0])
                if ring_path.exists():
                    return ring_path
        except Exception:
            pass
        
        return None
    
    def _find_edtcli(self) -> Optional[Path]:
        """
        Ищет 1cedtcli.exe.
        
        Returns:
            Path или None: Путь к 1cedtcli.exe или None если не найден
        """
        # Проверяем переменную EDTCLI_TOOL
        if 'EDTCLI_TOOL' in self.env_vars:
            tool_path = Path(self.env_vars['EDTCLI_TOOL'].strip('"'))
            if tool_path.exists():
                return tool_path
        
        # Ищем по версии V8_EDT_VERSION
        edt_version = self.env_vars.get('V8_EDT_VERSION', '2023.3')
        default_path = Path(f"C:/Program Files/1cv8/{edt_version}/1cedtcli.exe")
        if default_path.exists():
            return default_path
        
        return None
    
    def execute(self, *args: str, **kwargs: str) -> "subprocess.CompletedProcess[str]":
        """
        Выполняет команду EDT инструмента.
        
        Args:
            *args: Позиционные аргументы команды
            **kwargs: Именованные аргументы команды
        
        Returns:
            CompletedProcess[str]: Результат выполнения команды
        """
        if not self.is_available():
            raise ToolNotFoundError("EDT инструмент (ring/edtcli) не найден в системе")
        
        # Реализация будет добавлена позже
        raise NotImplementedError("Метод execute будет реализован в следующих задачах")
    
    def export_to_xml(
        self, 
        edt_project: Path, 
        xml_output: Path,
        workspace: Path
    ) -> int:
        """
        Экспортирует EDT проект в XML.
        
        Args:
            edt_project: Путь к EDT проекту
            xml_output: Путь для выходных XML файлов
            workspace: Путь к workspace EDT
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("EDT инструмент (ring/edtcli) не найден в системе")
        
        self.logger.info(f"Экспорт EDT проекта в XML...")
        
        # Создаем директории если не существуют
        xml_output.mkdir(parents=True, exist_ok=True)
        workspace.mkdir(parents=True, exist_ok=True)
        
        if self.use_edtcli:
            # Используем edtcli
            # Команда: 1cedtcli.exe -data <workspace> -command export --project <project> --configuration-files <xml>
            cmd = [
                str(self.tool_path),
                '-data', str(workspace),
                '-command', 'export',
                '--project', str(edt_project),
                '--configuration-files', str(xml_output)
            ]
        elif self.use_ring:
            # Используем ring
            # Команда: ring.bat edt@<version> workspace export --project <project> --configuration-files <xml> --workspace-location <workspace>
            edt_version = self.env_vars.get('V8_EDT_VERSION', '2023.3')
            cmd = [
                str(self.tool_path),
                f'edt@{edt_version}',
                'workspace', 'export',
                '--project', str(edt_project),
                '--configuration-files', str(xml_output),
                '--workspace-location', str(workspace)
            ]
        else:
            raise ToolNotFoundError("EDT инструмент не определен")
        
        # Выводим команду в режиме отладки

        
        self._log_command(cmd)


        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace',
                shell=self.use_ring  # ring.bat требует shell=True на Windows
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    f"Ошибка при экспорте EDT проекта",
                    tool_output=result.stderr or result.stdout
                )
            
            # Проверяем что XML файлы созданы
            # Для конфигураций создается Configuration.xml
            # Для обработок/отчетов создается ExternalDataProcessors/*.xml или ExternalReports/*.xml
            has_config = (xml_output / 'Configuration.xml').exists()
            has_processors = (xml_output / 'ExternalDataProcessors').exists()
            has_reports = (xml_output / 'ExternalReports').exists()
            
            if not (has_config or has_processors or has_reports):
                raise ToolExecutionError(
                    f"XML файлы не созданы в {xml_output}",
                    tool_output=result.stdout
                )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска EDT инструмента: {e}")

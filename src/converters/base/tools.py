"""
Абстракции для работы с инструментами 1С.

Содержит обертки для работы с 1cv8.exe (designer), ibcmd.exe и EDT инструментами.
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, List, Tuple, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import subprocess

from .converter import Logger, ToolNotFoundError, ToolExecutionError
from .ib_utils import parse_ib_reference


def format_command_for_log(cmd: List[str]) -> str:
    """
    Форматирует команду для вывода в лог.
    
    Берет в кавычки аргументы с пробелами, двоеточием и специальными символами.
    Используется для единообразного логирования команд в режиме отладки.
    
    Args:
        cmd: Список аргументов команды
        
    Returns:
        str: Отформатированная строка команды для CMD
    """
    def needs_quotes(arg: str) -> bool:
        """Проверяет, нужны ли кавычки для аргумента."""
        # Двоеточие добавлено для путей Windows (C:\path)
        special_chars = [' ', ':', ';', '&', '|', '<', '>', '^', '(', ')']
        return any(char in arg for char in special_chars)
    
    cmd_parts = []
    for arg in cmd:
        arg_str = str(arg)
        if needs_quotes(arg_str):
            # Экранируем внутренние кавычки если есть
            arg_str = arg_str.replace('"', '\\"')
            cmd_parts.append(f'"{arg_str}"')
        else:
            cmd_parts.append(arg_str)
    
    return ' '.join(cmd_parts)


class ToolWrapper(ABC):
    """
    Базовый класс для оберток инструментов 1С.
    
    Args:
        env_vars: Словарь переменных окружения
        logger: Логгер для вывода сообщений
    """
    
    env_vars: Dict[str, str]
    logger: Logger

    @staticmethod
    def parse_ib_reference(value: str) -> Tuple[bool, str, str]:
        """
        Определяет тип подключения к ИБ и извлекает параметры.
        
        На вход могут подаваться:
        - /Sserver\\base или /Sserver/base
        - /FПутьКФайловойБазе
        - Srvr="server";Ref="base";
        - File="C:/path/to/db";
        - Прямой путь к файловой базе
        
        Returns:
            Tuple[bool, str, str]: (isServer, server, base_or_path)
        """
        s = (value or "").strip()
        if not s:
            return False, "", ""
        sl = s.lower()
        # Server in Srvr=..;Ref=..; format
        if 'srvr=' in sl and 'ref=' in sl:
            import re
            m = re.search(r'(?i)srvr\s*=\s*"?([^";]+)"?;.*?ref\s*=\s*"?([^";]+)"?', s)
            if m:
                server = m.group(1).strip('\\/ ')
                base = m.group(2).strip('\\/ ')
                return True, server, base
        # /Sserver\base or /Sserver/base
        if sl.startswith('/s'):
            rest = s[2:]
            if rest.startswith('\\') or rest.startswith('/'):
                rest = rest[1:]
            rest = rest.replace('/', '\\')
            parts = rest.split('\\', 1)
            server = parts[0].strip('\\/ ')
            base = (parts[1] if len(parts) > 1 else '').strip('\\/ ')
            return True, server, base
        # File connection
        if sl.startswith('/f'):
            path = s[2:].lstrip('\\/')
            return False, "", path
        if 'file=' in sl:
            import re
            m = re.search(r'(?i)file\s*=\s*"?([^";]+)"?', s)
            if m:
                path = m.group(1).strip()
                return False, "", path
        # Assume filesystem path
        return False, "", s
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
            safe_cmd = []
            for arg in cmd:
                arg_lower = str(arg).lower()
                if arg_lower.startswith('--password='):
                    safe_cmd.append('--password=***')
                elif arg_lower.startswith('--db-pwd='):
                    safe_cmd.append('--db-pwd=***')
                elif str(arg).startswith('/P'):
                    safe_cmd.append('/P***')
                else:
                    safe_cmd.append(str(arg))
            cmd_str = format_command_for_log(safe_cmd)
            self.logger.debug_msg(f"Команда: {cmd_str}")
            self.logger.debug_msg("Примечание: Команда отформатирована для копирования в CMD")
    
    @abstractmethod
    def find_tool(self) -> Optional[Path]:
        """
        Находит инструмент в системе.
        
        Returns:
            Path или None: Путь к инструменту или None если не найден
        """
        pass
    
    @abstractmethod
    def execute(self, *args: str, **kwargs: str) -> subprocess.CompletedProcess[str]:
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
        version = self.env_vars.get('V8_VERSION', '8.3.27.1989')
        default_path = Path(f"C:/Program Files/1cv8/{version}/bin/1cv8.exe")
        if default_path.exists():
            return default_path
        
        # Альтернативный путь (x86)
        alt_path = Path(f"C:/Program Files (x86)/1cv8/{version}/bin/1cv8.exe")
        if alt_path.exists():
            return alt_path
        
        return None
    
    def _append_ib_credentials(self, cmd: List[str]) -> None:
        """
        Добавляет учетные данные к команде 1cv8.exe.
        
        Добавляет параметры /N (имя пользователя) и /P (пароль) к команде,
        если они указаны в переменных окружения V8_IB_USER и V8_IB_PWD.
        
        Args:
            cmd: Список аргументов команды (модифицируется in-place)
        """
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        if ib_user:
            cmd.extend([f'/N{ib_user}'])
        if ib_pwd:
            cmd.extend([f'/P{ib_pwd}'])
    
    def _build_ib_connection_string(self, ib_connection: str) -> str:
        """
        Формирует строку для /IBConnectionString с учетом типа ИБ.
        
        Поддерживает:
        - Файловую базу: путь или 'File=...;'
        - Серверную базу: '/Sserver\\base' или 'Srvr=...;Ref=...;'
        """
        is_server, server, base = parse_ib_reference(ib_connection)
        if is_server:
            return f"Srvr={server};Ref={base};"
        # файловая ИБ
        ib_path_str = base if base else ib_connection
        ib_path_str = ib_path_str.replace('\\', '/')
        return f"File={ib_path_str};"
    
    def execute(self, *args: str, **kwargs: str) -> subprocess.CompletedProcess[str]:
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
            '/Out', str(log_file)
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
            
            # Проверяем лог на ошибки и предупреждения
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(log_file, self.logger)
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
        ib_conn_string = self._build_ib_connection_string(str(ib_connection))
        
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/LoadConfigFromFiles', str(xml_path)
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
            
            # Проверяем лог на ошибки и предупреждения
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(log_file, self.logger)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при загрузке из XML",
                        tool_output=error_msg
                    )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")

    def dump_infobase(
        self,
        ib_connection: str,
        output_file: Path,
        log_file: Path
    ) -> int:
        """Выгружает информационную базу в DT-файл через DESIGNER."""
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")

        self.logger.info(f"Выгрузка информационной базы в DT: {output_file}...")
        temp_output = output_file.with_name(
            f'.{output_file.stem}.{uuid4().hex}.tmp.dt'
        )
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', self._build_ib_connection_string(ib_connection),
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/DumpIB', str(temp_output)
        ]
        self._append_ib_credentials(cmd)
        self._log_command(cmd)

        try:
            if log_file.exists():
                log_file.unlink()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            errors = []
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(
                    log_file, self.logger
                )
            if errors:
                raise ToolExecutionError(
                    "Ошибка при выгрузке информационной базы в DT",
                    tool_output='\n'.join(errors)
                )
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при выгрузке информационной базы в DT",
                    tool_output=result.stderr or result.stdout
                )
            if not temp_output.exists():
                raise ToolExecutionError(f"Выходной файл не создан: {temp_output}")
            temp_output.replace(output_file)
            return result.returncode
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")
        finally:
            if temp_output.exists():
                temp_output.unlink()

    def restore_infobase(
        self,
        ib_connection: str,
        dt_file: Path,
        log_file: Path
    ) -> int:
        """Восстанавливает DT-файл в информационную базу через DESIGNER."""
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")

        self.logger.info(f"Восстановление информационной базы из DT: {dt_file}...")
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', self._build_ib_connection_string(ib_connection),
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/RestoreIB', str(dt_file)
        ]
        self._append_ib_credentials(cmd)
        self._log_command(cmd)

        try:
            if log_file.exists():
                log_file.unlink()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            errors = []
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(
                    log_file, self.logger
                )
            if errors:
                raise ToolExecutionError(
                    "Ошибка при восстановлении информационной базы из DT",
                    tool_output='\n'.join(errors)
                )
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при восстановлении информационной базы из DT",
                    tool_output=result.stderr or result.stdout
                )
            return result.returncode
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")

    def update_database_configuration(
        self,
        ib_connection: str,
        log_file: Path,
        extension_name: Optional[str] = None,
    ) -> int:
        """Обновляет конфигурацию базы данных через DESIGNER."""
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")

        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', self._build_ib_connection_string(ib_connection),
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/UpdateDBCfg',
        ]
        self._append_ib_credentials(cmd)
        if extension_name:
            cmd.extend(['-Extension', extension_name])
        self._log_command(cmd)

        try:
            if log_file.exists():
                log_file.unlink()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace',
            )
            errors = []
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(
                    log_file, self.logger
                )
            if errors or result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при обновлении конфигурации информационной базы",
                    tool_output='\n'.join(errors) or result.stderr or result.stdout,
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
        ib_conn_string = self._build_ib_connection_string(str(ib_connection))
        
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/DumpCfg', str(output_file)
        ]
        
        if extension_name:
            cmd.extend(['-Extension', extension_name])
        
        # Добавляем учетные данные если указаны
        self._append_ib_credentials(cmd)
        
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
            
            # Проверяем лог на ошибки и предупреждения
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(log_file, self.logger)
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

    def dump_config_to_files(
        self,
        ib_connection: str,
        output_dir: Path,
        log_file: Path
    ) -> int:
        """
        Выгружает конфигурацию в XML файлы.
        
        Args:
            ib_connection: Строка подключения к ИБ (путь к папке ИБ)
            output_dir: Директория для выгрузки XML
            log_file: Путь к лог-файлу
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        self.logger.info(f"Выгрузка конфигурации в XML: {output_dir}...")
        
        ib_conn_string = self._build_ib_connection_string(str(ib_connection))
        
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/DumpConfigToFiles', str(output_dir)
        ]
        
        self._append_ib_credentials(cmd)
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(log_file, self.logger)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при выгрузке конфигурации",
                        tool_output=error_msg
                    )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска 1cv8.exe: {e}")

    def load_config_from_cf(
        self,
        ib_connection: str,
        cf_file: Path,
        log_file: Path,
        extension_name: Optional[str] = None,
    ) -> int:
        """
        Загружает конфигурацию из CF файла в ИБ.
        
        Args:
            ib_connection: Строка подключения к ИБ (путь к папке ИБ)
            cf_file: Путь к CF файлу
            log_file: Путь к лог-файлу
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("1cv8.exe не найден в системе")
        
        self.logger.info(f"Загрузка конфигурации из CF: {cf_file}...")
        
        ib_conn_string = self._build_ib_connection_string(str(ib_connection))
        
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/LoadCfg', str(cf_file)
        ]

        if extension_name:
            cmd.extend(['-Extension', extension_name])
        
        self._append_ib_credentials(cmd)
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='cp1251',
                errors='replace'
            )
            
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(log_file, self.logger)
                if errors:
                    error_msg = '\n'.join(errors)
                    raise ToolExecutionError(
                        f"Ошибка при загрузке CF",
                        tool_output=error_msg
                    )
            
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
        ib_conn_string = self._build_ib_connection_string(str(ib_connection))
        
        # Команда /LoadExternalDataProcessorOrReportFromFiles требует два параметра:
        # 1. Путь к XML файлу обработки/отчета
        # 2. Путь к выходной директории (не файлу!)
        cmd = [
            str(self.tool_path),
            'DESIGNER',
            '/IBConnectionString', ib_conn_string,
            '/DisableStartupDialogs',
            '/Out', str(log_file),
            '/LoadExternalDataProcessorOrReportFromFiles', str(xml_file),
            str(output_dir)
        ]
        
        # Добавляем учетные данные если указаны
        self._append_ib_credentials(cmd)
        
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
            
            # Проверяем лог на ошибки и предупреждения
            if log_file.exists():
                from .converter import ToolOutputParser
                errors, _ = ToolOutputParser.parse_designer_log(log_file, self.logger)
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

    def __init__(self, env_vars: Dict[str, str], logger: Logger):
        super().__init__(env_vars, logger)
        self.last_import_tool = 'ibcmd'
    
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
        version = self.env_vars.get('V8_VERSION', '8.3.27.1989')
        default_path = Path(f"C:/Program Files/1cv8/{version}/bin/ibcmd.exe")
        if default_path.exists():
            return default_path
        
        # Альтернативный путь (x86)
        alt_path = Path(f"C:/Program Files (x86)/1cv8/{version}/bin/ibcmd.exe")
        if alt_path.exists():
            return alt_path
        
        return None
    
    def _resolve_server_ib(self) -> Tuple[str, str]:
        """
        Определяет параметры серверной ИБ (сервер и имя базы) из переменных окружения.
        
        Логика:
        - Берёт V8_IB_SERVER/V8_IB_NAME, если заданы
        - Иначе пытается распарсить из путей вида '/Sserver\\base' по ключам V8_SRC_PATH, V8_DST_PATH
        
        Returns:
            tuple[str, str]: (server, name) или ('', '') если серверная ИБ не указана
        """
        ib_server = self.env_vars.get('V8_IB_SERVER', '')
        ib_name = self.env_vars.get('V8_IB_NAME', '')
        if ib_server and ib_name:
            return ib_server, ib_name
        
        for key in ('V8_SRC_PATH', 'V8_DST_PATH'):
            val = self.env_vars.get(key, '')
            is_server, server, base = parse_ib_reference(val)
            if is_server and server and base:
                ib_server = server
                ib_name = base
                break
        return ib_server, ib_name

    def _designer_server_connection(
        self, fallback_server: str, fallback_name: str
    ) -> str:
        """Возвращает кластерную ссылку ИБ для fallback через DESIGNER."""
        for key in ('V8_DST_PATH', 'V8_SRC_PATH'):
            value = self.env_vars.get(key, '')
            is_server, server, name = parse_ib_reference(value)
            if is_server and server and name:
                return value
        return f'/S{fallback_server}\\{fallback_name}'
    
    def execute(self, *args: str, **kwargs: str) -> subprocess.CompletedProcess[str]:
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
    
    def create_infobase_with_config(
        self,
        db_path: Path,
        xml_path: Optional[Path] = None,
        cf_file: Optional[Path] = None
    ) -> int:
        """
        Создает ИБ и загружает конфигурацию из XML или CF.
        
        Args:
            db_path: Путь к создаваемой ИБ
            xml_path: Путь к XML файлам конфигурации
            cf_file: Путь к CF файлу конфигурации
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")

        if (xml_path is None and cf_file is None) or (xml_path is not None and cf_file is not None):
            raise ValueError("Нужно указать ровно один источник: xml_path или cf_file")

        if cf_file is not None:
            self.logger.info(f"Создание ИБ с конфигурацией из CF: {cf_file}...")
        else:
            self.logger.info(f"Создание ИБ с конфигурацией из XML...")
        
        # Получаем путь к данным ibcmd
        ibcmd_data = self.env_vars.get('IBCMD_DATA', str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data'))
        
        # Команда:
        # - XML: ibcmd infobase create --data=<data> --db-path=<path> --create-database --import=<xml>
        # - CF:  ibcmd infobase create --data=<data> --db-path=<path> --create-database --load=<cf>
        cmd = [
            str(self.tool_path),
            'infobase', 'create',
            f'--data={ibcmd_data}',
            f'--db-path={db_path}',
            '--create-database',
        ]

        if cf_file is not None:
            cmd.append(f'--load={cf_file}')
        else:
            assert xml_path is not None
            cmd.append(f'--import={xml_path}')
        
        # Выводим команду в режиме отладки

        
        self._log_command(cmd)


        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
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

    def _infobase_connection_args(
        self,
        db_path: Path,
        *,
        use_server: bool = False
    ) -> List[str]:
        """Возвращает параметры подключения ibcmd к файловой или серверной ИБ."""
        ibcmd_data = self.env_vars.get(
            'IBCMD_DATA',
            str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data')
        )
        args = [f'--data={ibcmd_data}']
        if use_server:
            ib_server, ib_name = self._resolve_server_ib()
            if not ib_server or not ib_name:
                raise ToolExecutionError(
                    "Не заданы сервер и имя базы данных для ibcmd"
                )
            args.extend([
                f"--dbms={self.env_vars.get('V8_DB_SRV_DBMS', 'MSSQLServer')}",
                f'--db-server={ib_server}',
                f'--db-name={ib_name}',
                f"--db-user={self.env_vars.get('V8_DB_SRV_USR', '')}",
                f"--db-pwd={self.env_vars.get('V8_DB_SRV_PWD', '')}",
            ])
        else:
            args.append(f'--db-path={db_path}')
        args.extend([
            f"--user={self.env_vars.get('V8_IB_USER', '')}",
            f"--password={self.env_vars.get('V8_IB_PWD', '')}",
        ])
        return args

    def dump_infobase(
        self,
        db_path: Path,
        output_file: Path,
        *,
        use_server: bool = False
    ) -> int:
        """Выгружает информационную базу в DT-файл через ibcmd."""
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")

        self.logger.info(f"Выгрузка информационной базы в DT: {output_file}...")
        cmd = [str(self.tool_path), 'infobase', 'dump']
        cmd.extend(
            self._infobase_connection_args(db_path, use_server=use_server)
        )
        cmd.append(str(output_file))
        self._log_command(cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при выгрузке информационной базы в DT",
                    tool_output=result.stderr or result.stdout
                )
            if not output_file.exists():
                raise ToolExecutionError(f"Выходной файл не создан: {output_file}")
            return result.returncode
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")

    def restore_infobase(
        self,
        db_path: Path,
        dt_file: Path,
        *,
        use_server: bool = False
    ) -> int:
        """Восстанавливает DT-файл в информационную базу через ibcmd."""
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")

        self.logger.info(f"Восстановление информационной базы из DT: {dt_file}...")
        cmd = [str(self.tool_path), 'infobase', 'restore']
        cmd.extend(
            self._infobase_connection_args(db_path, use_server=use_server)
        )
        if not use_server and not (db_path / '1cv8.1cd').exists():
            cmd.append('--create-database')
        cmd.extend(['--force', str(dt_file)])
        self._log_command(cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при восстановлении информационной базы из DT",
                    tool_output=result.stderr or result.stdout
                )
            return result.returncode
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")

    def update_database_configuration(
        self,
        db_path: Path,
        *,
        use_server: bool = False,
        extension_name: Optional[str] = None,
    ) -> int:
        """Обновляет конфигурацию базы данных через ibcmd."""
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")

        cmd = [str(self.tool_path), 'infobase', 'config', 'apply']
        cmd.extend(
            self._infobase_connection_args(db_path, use_server=use_server)
        )
        if extension_name:
            cmd.append(f'--extension={extension_name}')
        cmd.append('--force')
        self._log_command(cmd)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
            )
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при обновлении конфигурации информационной базы",
                    tool_output=result.stderr or result.stdout,
                )
            return result.returncode
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")
    
    def import_config_from_xml(
        self,
        db_path: Path,
        xml_path: Path,
        extension_name: Optional[str] = None,
        use_server: Optional[bool] = None,
    ) -> int:
        """
        Импортирует конфигурацию в существующую ИБ из XML (файловую или серверную).
        
        Поддерживает два режима:
        - Файловая ИБ: --db-path=<path>
        - Серверная ИБ: --dbms/--db-server/--db-name (+ учетные данные БД)
        
        Args:
            db_path: Путь к существующей файловой ИБ (игнорируется для серверного режима)
            xml_path: Путь к XML файлам конфигурации
        
        Returns:
            int: Код возврата (0 - успех)
        
        Raises:
            ToolNotFoundError: Если ibcmd.exe не найден
            ToolExecutionError: Если выполнение ibcmd завершилось ошибкой
        
        Примеры:
            Файловая ИБ:
                >>> from pathlib import Path
                >>> ibcmd.import_config_from_xml(
                ...     db_path=Path('C:/temp/tmp_db'),
                ...     xml_path=Path('C:/temp/tmp_xml')
                ... )
            
            Серверная ИБ (MSSQLServer):
                >>> env = {
                ...     'IBCMD_TOOL': r'C:/Program Files/1cv8/8.3.27.1989/bin/ibcmd.exe',
                ...     'V8_IB_SERVER': 'kantor',
                ...     'V8_IB_NAME': 'test_for_1c_convert_kit_2ib',
                ...     'V8_DB_SRV_DBMS': 'MSSQLServer',
                ...     'V8_DB_SRV_USR': 'sa',
                ...     'V8_DB_SRV_PWD': 'password'
                ... }
                >>> logger = Logger(silent=False)
                >>> ibcmd = IbcmdToolWrapper(env, logger)
                >>> ibcmd.import_config_from_xml(
                ...     db_path=Path('.'),  # игнорируется для серверного режима
                ...     xml_path=Path('F:/1C/Projects/1c-convert-kit/tests/fixtures/cf/ConfXML')
                ... )
        """
        self.last_import_tool = 'ibcmd'
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")
        
        self.logger.info(f"Импорт конфигурации в существующую ИБ из XML...")
        
        ibcmd_data = self.env_vars.get('IBCMD_DATA', str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data'))
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        ib_server, ib_name = self._resolve_server_ib()

        if use_server is False:
            ib_server, ib_name = '', ''
        elif use_server is True and not (ib_server and ib_name):
            raise ToolExecutionError(
                "Не заданы сервер и имя базы данных для ibcmd"
            )
        
        if ib_server and ib_name:
            db_srv_dbms = self.env_vars.get('V8_DB_SRV_DBMS', 'MSSQLServer')
            db_srv_usr = self.env_vars.get('V8_DB_SRV_USR', '')
            db_srv_pwd = self.env_vars.get('V8_DB_SRV_PWD', '')
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'import',
                f'--data={ibcmd_data}',
                f'--dbms={db_srv_dbms}',
                f'--db-server={ib_server}',
                f'--db-name={ib_name}',
                f'--db-user={db_srv_usr}',
                f'--db-pwd={db_srv_pwd}',
                f'--user={ib_user}',
                f'--password={ib_pwd}',
            ]
        else:
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'import',
                f'--data={ibcmd_data}',
                f'--db-path={db_path}',
                f'--user={ib_user}',
                f'--password={ib_pwd}',
            ]

        if extension_name:
            cmd.append(f'--extension={extension_name}')
        cmd.append(str(xml_path))
        
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                if ib_server and ib_name:
                    # Fallback: используем DESIGNER для серверной ИБ
                    v8 = V8ToolWrapper(self.env_vars, self.logger)
                    log_file = Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_fallback_load_xml.log'
                    ib_connection = self._designer_server_connection(
                        ib_server, ib_name
                    )
                    self.logger.warning("Не удалось выполнить ibcmd import для серверной ИБ, выполняется загрузка через DESIGNER (fallback)")
                    v8_result = v8.load_config_from_files(
                        ib_connection,
                        xml_path,
                        log_file,
                        extension_name=extension_name,
                    )
                    if v8_result == 0:
                        self.last_import_tool = 'designer'
                        return 0
                raise ToolExecutionError(
                    f"Ошибка при импорте конфигурации",
                    tool_output=result.stderr or result.stdout
                )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")

    def export_config_to_files(
        self,
        db_path: Path,
        output_dir: Path,
        extension_name: Optional[str] = None
    ) -> int:
        """
        Выгружает конфигурацию или расширение в XML файлы.
        
        Args:
            db_path: Путь к ИБ
            output_dir: Директория для выгрузки XML
            extension_name: Имя расширения (если выгружается расширение)
            
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")
        
        if extension_name:
            self.logger.info(f"Выгрузка расширения '{extension_name}' в XML: {output_dir}...")
        else:
            self.logger.info(f"Выгрузка конфигурации в XML: {output_dir}...")
        
        ibcmd_data = self.env_vars.get('IBCMD_DATA', str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data'))
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        ib_server, ib_name = self._resolve_server_ib()
        
        export_flags = ['--force']
        if (output_dir / 'Configuration.xml').exists() and (output_dir / 'ConfigDumpInfo.xml').exists():
            export_flags.append('--sync')
        
        if ib_server and ib_name:
            db_srv_dbms = self.env_vars.get('V8_DB_SRV_DBMS', 'MSSQLServer')
            db_srv_usr = self.env_vars.get('V8_DB_SRV_USR', '')
            db_srv_pwd = self.env_vars.get('V8_DB_SRV_PWD', '')
            
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'export',
                f'--data={ibcmd_data}',
                f'--dbms={db_srv_dbms}',
                f'--db-server={ib_server}',
                f'--db-name={ib_name}',
                f'--db-user={db_srv_usr}',
                f'--db-pwd={db_srv_pwd}',
                f'--user={ib_user}',
                f'--password={ib_pwd}'
            ]
        else:
            # Используется только для файловых баз или для прямого указания пути к хранилищу данных автономного сервера
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'export',
                f'--data={ibcmd_data}',
                f'--db-path={db_path}',
                f'--user={ib_user}',
                f'--password={ib_pwd}'
            ]
        
        if extension_name:
            cmd.extend(['--extension', extension_name])
        
        cmd.extend(export_flags)
        cmd.append(str(output_dir))
        
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                raise ToolExecutionError(
                    "Ошибка при выгрузке конфигурации в XML",
                    tool_output=result.stderr or result.stdout
                )
            
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска ibcmd.exe: {e}")
    
    def import_config_from_cf(
        self,
        db_path: Path,
        cf_file: Path,
        extension_name: Optional[str] = None,
        use_server: Optional[bool] = None,
    ) -> int:
        """
        Импортирует конфигурацию из CF файла в существующую ИБ (файловую или серверную).
        
        Поддерживает:
        - Файловая ИБ: --db-path=<path>
        - Серверная ИБ: --dbms/--db-server/--db-name (+ учетные данные БД)
        
        Args:
            db_path: Путь к существующей файловой ИБ (игнорируется для серверного режима)
            cf_file: Путь к CF файлу конфигурации
        
        Returns:
            int: Код возврата (0 - успех)
        
        Raises:
            ToolNotFoundError: Если ibcmd.exe не найден
            ToolExecutionError: Если выполнение ibcmd завершилось ошибкой
        
        Примеры:
            Серверная ИБ (PostgreSQL):
                >>> env = {
                ...     'IBCMD_TOOL': r'C:/Program Files/1cv8/8.3.27.1989/bin/ibcmd.exe',
                ...     'V8_IB_SERVER': 'db-srv-01',
                ...     'V8_IB_NAME': 'my_prod_base',
                ...     'V8_DB_SRV_DBMS': 'PostgreSQL',
                ...     'V8_DB_SRV_USR': 'postgres',
                ...     'V8_DB_SRV_PWD': 'YourDbPassword',
                ...     'V8_IB_USER': 'Admin1C',
                ...     'V8_IB_PWD': 'AdminPassword1C',
                ...     'V8_TEMP': r'C:/temp'
                ... }
                >>> logger = Logger(silent=False)
                >>> ibcmd = IbcmdToolWrapper(env, logger)
                >>> ibcmd.import_config_from_cf(
                ...     db_path=Path('.'),
                ...     cf_file=Path('C:/Builds/update.cf')
                ... )
            
            Файловая ИБ:
                >>> ibcmd.import_config_from_cf(
                ...     db_path=Path('C:/temp/tmp_db'),
                ...     cf_file=Path('C:/Builds/update.cf')
                ... )
        """
        self.last_import_tool = 'ibcmd'
        if not self.is_available():
            raise ToolNotFoundError("ibcmd.exe не найден в системе")
        
        self.logger.info(f"Загрузка конфигурации из CF: {cf_file}...")
        
        ibcmd_data = self.env_vars.get('IBCMD_DATA', str(Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_data'))
        ib_user = self.env_vars.get('V8_IB_USER', '')
        ib_pwd = self.env_vars.get('V8_IB_PWD', '')
        ib_server, ib_name = self._resolve_server_ib()

        if use_server is False:
            ib_server, ib_name = '', ''
        elif use_server is True and not (ib_server and ib_name):
            raise ToolExecutionError(
                "Не заданы сервер и имя базы данных для ibcmd"
            )
        
        if ib_server and ib_name:
            db_srv_dbms = self.env_vars.get('V8_DB_SRV_DBMS', 'MSSQLServer')
            db_srv_usr = self.env_vars.get('V8_DB_SRV_USR', '')
            db_srv_pwd = self.env_vars.get('V8_DB_SRV_PWD', '')
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'load',
                f'--data={ibcmd_data}',
                f'--dbms={db_srv_dbms}',
                f'--db-server={ib_server}',
                f'--db-name={ib_name}',
                f'--db-user={db_srv_usr}',
                f'--db-pwd={db_srv_pwd}',
                f'--user={ib_user}',
                f'--password={ib_pwd}',
                '--force',
            ]
        else:
            cmd = [
                str(self.tool_path),
                'infobase', 'config', 'load',
                f'--data={ibcmd_data}',
                f'--db-path={db_path}',
                f'--user={ib_user}',
                f'--password={ib_pwd}',
                '--force',
            ]

        if extension_name:
            cmd.append(f'--extension={extension_name}')
        cmd.append(str(cf_file))
        
        self._log_command(cmd)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                if ib_server and ib_name:
                    # Fallback: DESIGNER для серверной ИБ
                    v8 = V8ToolWrapper(self.env_vars, self.logger)
                    log_file = Path(self.env_vars.get('V8_TEMP', 'temp')) / 'ibcmd_fallback_load_cf.log'
                    ib_connection = self._designer_server_connection(
                        ib_server, ib_name
                    )
                    self.logger.warning("Не удалось выполнить ibcmd load для серверной ИБ, выполняется загрузка через DESIGNER (fallback)")
                    v8_result = v8.load_config_from_cf(
                        ib_connection,
                        cf_file,
                        log_file,
                        extension_name=extension_name,
                    )
                    if v8_result == 0:
                        self.last_import_tool = 'designer'
                        return 0
                raise ToolExecutionError(
                    f"Ошибка при загрузке конфигурации из CF",
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
        ib_server, ib_name = self._resolve_server_ib()
        
        if ib_server and ib_name:
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
                encoding='utf-8',
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
        Находит 1cedtcli или ring  в системе.
        
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
        edt_version = self.env_vars.get('V8_EDT_VERSION', '2025.1.5')
        default_path = Path(f"C:/Program Files/1cv8/{edt_version}/1cedtcli.exe")
        if default_path.exists():
            return default_path
        
        return None
    
    def execute(self, *args: str, **kwargs: str) -> subprocess.CompletedProcess[str]:
        """
        Выполняет команду EDT инструмента.
        
        Args:
            *args: Позиционные аргументы команды
            **kwargs: Именованные аргументы команды
        
        Returns:
            CompletedProcess[str]: Результат выполнения команды
        """
        if not self.is_available():
            raise ToolNotFoundError("EDT инструмент (1cedtcli/ring) не найден в системе")
        
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
            raise ToolNotFoundError("EDT инструмент (1cedtcli/ring) не найден в системе")
        
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
            edt_version = self.env_vars.get('V8_EDT_VERSION', '2025.1.5')
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
    
    def import_configuration_files_to_edt_project(
        self,
        xml_source_path: Path,
        edt_project_path: Path,
        workspace_path: Path,
        *,
        entity_type: str = "конфигурации"
    ) -> int:
        """
        Импортирует XML файлы в EDT проект.
        
        Args:
            xml_source_path: Путь к XML файлам
            edt_project_path: Путь к EDT проекту (будет создан)
            workspace_path: Путь к workspace EDT
            entity_type: Тип сущности для сообщений (конфигурации/расширения)
        
        Returns:
            int: Код возврата (0 - успех)
            
        Raises:
            ToolNotFoundError: Если инструмент не найден
            ToolExecutionError: Если выполнение завершилось с ошибкой
        """
        if not self.is_available():
            raise ToolNotFoundError("EDT инструмент (1cedtcli/ring) не найден в системе")
        
        self.logger.info(f"Импорт {entity_type} в EDT проект...")
        
        # Создаем директории если не существуют
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Формируем команду в зависимости от инструмента
        if self.use_edtcli:
            # Используем edtcli
            # Команда: 1cedtcli.exe -data <workspace> -command import --project <project> --configuration-files <xml>
            cmd = [
                str(self.tool_path),
                '-data', str(workspace_path),
                '-command', 'import',
                '--project', str(edt_project_path),
                '--configuration-files', str(xml_source_path)
            ]
        elif self.use_ring:
            # Используем ring
            # Команда: ring.bat edt@<version> workspace import --project <project> --configuration-files <xml> --workspace-location <workspace>
            edt_version = self.env_vars.get('V8_EDT_VERSION', '2025.1.5')
            cmd = [
                str(self.tool_path),
                f'edt@{edt_version}',
                'workspace', 'import',
                '--project', str(edt_project_path),
                '--configuration-files', str(xml_source_path),
                '--workspace-location', str(workspace_path)
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
                    f"Ошибка при импорте {entity_type} в EDT",
                    tool_output=result.stderr or result.stdout
                )
            
            # Проверяем что EDT проект создан
            project_file = edt_project_path / '.project'
            if not project_file.exists():
                raise ToolExecutionError(
                    f"Файл .project не создан: {project_file}",
                    tool_output=result.stdout
                )
            
            self.logger.success(f"Импорт {entity_type} в EDT завершен успешно")
            return result.returncode
            
        except subprocess.SubprocessError as e:
            raise ToolExecutionError(f"Ошибка запуска EDT инструмента: {e}")



def prepare_base_infobase(
    *,
    base_ib: Optional[str],
    base_config: Optional[str],
    temp_dir: Path,
    v8_tool: V8ToolWrapper,
    logger: Logger,
    entity_type: str = "обработок/отчетов"
) -> str:
    """
    Подготавливает базовую ИБ для загрузки обработок/отчетов/расширений.
    
    Логика:
    1. Если указан base_ib - использовать существующую ИБ
    2. Если указан base_config - создать ИБ и загрузить конфигурацию
    3. Иначе - создать пустую ИБ
    
    Args:
        base_ib: Путь к существующей ИБ (V8_BASE_IB)
        base_config: Путь к конфигурации для загрузки (V8_BASE_CONFIG)
        temp_dir: Директория для временных файлов
        v8_tool: Обертка для работы с 1cv8.exe
        logger: Логгер для вывода сообщений
        entity_type: Тип сущности для сообщений (по умолчанию "обработок/отчетов")
    
    Returns:
        str: Строка подключения к ИБ
        
    Raises:
        ValidationError: Если базовая ИБ не найдена
        ToolNotFoundError: Если инструмент не найден
        ToolExecutionError: Если ошибка при создании/загрузке ИБ
    """
    logger.info(f"Подготовка базовой информационной базы для {entity_type}...")
    
    # Случай 1: Используем существующую ИБ
    if base_ib:
        logger.info(f"Использование существующей ИБ: {base_ib}")
        
        is_server, server, base = parse_ib_reference(base_ib)
        if is_server:
            ib_connection = f'/S{server}\\{base}'
        else:
            ib_connection = base if base else base_ib
        
        # Проверяем существование ИБ (только для файловых)
        if not is_server:
            base_ib_path = Path(base if base else base_ib)
            if not base_ib_path.exists():
                from .converter import ValidationError
                raise ValidationError(f"Базовая ИБ не найдена: {base_ib}")
        
        return ib_connection
    
    # Случай 2: Создаем ИБ и загружаем конфигурацию
    if base_config:
        logger.info(f"Создание ИБ с конфигурацией: {base_config}")
        
        # Проверяем доступность инструмента
        if not v8_tool.is_available():
            raise ToolNotFoundError(
                "1cv8.exe не найден. " +
                "Установите платформу 1С или укажите путь в переменной V8_TOOL"
            )
        
        # Создаем временную ИБ
        temp_db = temp_dir / 'base_ib'
        temp_db.mkdir(exist_ok=True)
        
        # Формируем строку подключения для CREATEINFOBASE (File=path;)
        temp_db_str = str(temp_db).replace('\\', '/')
        ib_connection_create = f'File={temp_db_str};'
        ib_connection = str(temp_db)  # Для последующих операций
        log_file = temp_dir / 'create_base_ib.log'
        
        # Создаем ИБ
        # Сообщение выводится внутри v8_tool.create_infobase()
        result = v8_tool.create_infobase(ib_connection_create, log_file)
        
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при создании базовой ИБ",
                temp_dir=temp_dir
            )
        
        # Загружаем конфигурацию
        logger.info("Загрузка базовой конфигурации...")
        load_log_file = temp_dir / 'load_base_config.log'
        
        result = v8_tool.load_config_from_files(
            ib_connection=ib_connection,
            xml_path=Path(base_config),
            log_file=load_log_file
        )
        
        if result != 0:
            raise ToolExecutionError(
                "Ошибка при загрузке базовой конфигурации",
                temp_dir=temp_dir
            )
        
        logger.success("Базовая ИБ создана и конфигурация загружена")
        return ib_connection
    
    # Случай 3: Создаем пустую ИБ
    logger.info(f"Создание пустой ИБ для {entity_type}...")
    
    # Проверяем доступность инструмента
    if not v8_tool.is_available():
        raise ToolNotFoundError(
            "1cv8.exe не найден. " +
            "Установите платформу 1С или укажите путь в переменной V8_TOOL"
        )
    
    # Создаем временную ИБ
    temp_db = temp_dir / 'base_ib'
    temp_db.mkdir(exist_ok=True)
    
    # Формируем строку подключения для CREATEINFOBASE (File=path;)
    temp_db_str = str(temp_db).replace('\\', '/')
    ib_connection_create = f'File={temp_db_str};'
    ib_connection = str(temp_db)  # Для последующих операций
    log_file = temp_dir / 'create_empty_ib.log'
    
    result = v8_tool.create_infobase(ib_connection_create, log_file)
    
    if result != 0:
        raise ToolExecutionError(
            "Ошибка при создании пустой ИБ",
            temp_dir=temp_dir
        )
    
    logger.success("Пустая ИБ создана")
    return ib_connection

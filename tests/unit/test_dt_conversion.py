"""Unit-тесты сценариев DT <-> информационная база."""

import subprocess
from pathlib import Path

import pytest

from src.converters.base.converter import (
    Logger,
    SourceDetector,
    SourceType,
    ToolExecutionError,
    ValidationError,
)
from src.converters.base.tools import IbcmdToolWrapper, V8ToolWrapper
from src.converters.configuration.converter import ConfigurationConverter


def test_source_detector_recognizes_dt_file(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"stub")

    assert SourceDetector.detect(str(dt_file)) is SourceType.DT_FILE


@pytest.mark.parametrize(
    ("script_name", "src_name", "dst_name"),
    [
        ("dt2ib", "backup.cf", "target_ib"),
        ("ib2dt", "source_ib", "backup.cf"),
    ],
)
def test_dt_scenarios_reject_wrong_file_extensions(
    tmp_path, script_name, src_name, dst_name
):
    src = tmp_path / src_name
    if src.suffix:
        src.write_bytes(b"stub")
    else:
        src.mkdir()
        (src / "1cv8.1cd").write_bytes(b"stub")

    converter = ConfigurationConverter(
        {
            "ScriptName": script_name,
            "V8_SRC_PATH": str(src),
            "V8_DST_PATH": str(tmp_path / dst_name),
        },
        silent=True,
    )

    with pytest.raises(ValidationError):
        converter.validate()


def test_ib2dt_rejects_non_infobase_source(tmp_path):
    src_cf = tmp_path / "configuration.cf"
    src_cf.write_bytes(b"stub")
    converter = ConfigurationConverter(
        {
            "ScriptName": "ib2dt",
            "V8_SRC_PATH": str(src_cf),
            "V8_DST_PATH": str(tmp_path / "backup.dt"),
        },
        silent=True,
    )

    with pytest.raises(ValidationError):
        converter.validate()


def test_dt_scenarios_reject_unknown_convert_tool(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"stub")
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(tmp_path / "target_ib"),
            "V8_CONVERT_TOOL": "ibcmdd",
        },
        silent=True,
    )

    with pytest.raises(ValidationError):
        converter.validate()


@pytest.mark.parametrize(
    ("script_name", "src_path", "dst_path"),
    [
        ("dt2ib", "backup.dt", "/Sserver"),
        ("dt2ib", "backup.dt", 'Srvr="server";Ref="";'),
        ("ib2dt", "/Sserver", "backup.dt"),
        ("ib2dt", 'Srvr="server";Ref="";', "backup.dt"),
    ],
)
def test_dt_scenarios_reject_incomplete_server_reference(
    tmp_path, script_name, src_path, dst_path
):
    if src_path == "backup.dt":
        src_path = str(tmp_path / src_path)
        Path(src_path).write_bytes(b"dt")
    if dst_path == "backup.dt":
        dst_path = str(tmp_path / dst_path)

    converter = ConfigurationConverter(
        {
            "ScriptName": script_name,
            "V8_SRC_PATH": src_path,
            "V8_DST_PATH": dst_path,
        },
        silent=True,
    )

    with pytest.raises(ValidationError):
        converter.validate()


@pytest.mark.parametrize("convert_tool", ["designer", "ibcmd"])
def test_dt2ib_routes_restore_to_selected_tool(tmp_path, convert_tool):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"stub")
    target_ib = tmp_path / "target_ib"
    target_ib.mkdir()
    (target_ib / "1cv8.1cd").write_bytes(b"existing")

    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_CONVERT_TOOL": convert_tool,
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.v8_tool.is_available = lambda: True
    converter.ibcmd_tool.is_available = lambda: True
    converter.v8_tool.restore_infobase = (
        lambda ib_connection, dt_file, log_file: calls.append(
            ("designer", ib_connection, dt_file)
        )
        or 0
    )
    converter.ibcmd_tool.restore_infobase = (
        lambda db_path, dt_file, **kwargs: calls.append(
            ("ibcmd", db_path, dt_file)
        )
        or 0
    )

    converter.validate()
    assert converter.convert() == 0
    assert calls[0][0] == convert_tool
    assert str(calls[0][1]) == str(target_ib)
    assert calls[0][2] == dt_file


@pytest.mark.parametrize("convert_tool", ["designer", "ibcmd"])
def test_ib2dt_routes_dump_to_selected_tool(tmp_path, convert_tool):
    source_ib = tmp_path / "source_ib"
    source_ib.mkdir()
    (source_ib / "1cv8.1cd").write_bytes(b"stub")
    dt_file = tmp_path / "backup.dt"

    converter = ConfigurationConverter(
        {
            "ScriptName": "ib2dt",
            "V8_SRC_PATH": str(source_ib),
            "V8_DST_PATH": str(dt_file),
            "V8_CONVERT_TOOL": convert_tool,
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.v8_tool.is_available = lambda: True
    converter.ibcmd_tool.is_available = lambda: True

    def dump(tool_name, ib_connection, output_file, *args):
        calls.append((tool_name, ib_connection, output_file))
        output_file.write_bytes(b"dt")
        return 0

    converter.v8_tool.dump_infobase = (
        lambda ib_connection, output_file, log_file: dump(
            "designer", ib_connection, output_file, log_file
        )
    )
    converter.ibcmd_tool.dump_infobase = (
        lambda db_path, output_file, **kwargs: dump(
            "ibcmd", db_path, output_file
        )
    )

    converter.validate()
    assert converter.convert() == 0
    assert calls[0][0] == convert_tool
    assert str(calls[0][1]) == str(source_ib)
    assert calls[0][2] == dt_file
    assert dt_file.read_bytes() == b"dt"


def test_designer_dt_commands_use_dumpib_and_restoreib(tmp_path, monkeypatch):
    tool = tmp_path / "1cv8.exe"
    tool.write_bytes(b"")
    dt_file = tmp_path / "backup.dt"
    log_file = tmp_path / "operation.log"
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        if "/DumpIB" in cmd:
            Path(cmd[cmd.index("/DumpIB") + 1]).write_bytes(b"dt")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("src.converters.base.tools.subprocess.run", fake_run)
    wrapper = V8ToolWrapper({"V8_TOOL": str(tool)}, Logger(silent=True))

    assert wrapper.dump_infobase("/Sserver\\base", dt_file, log_file) == 0
    assert wrapper.restore_infobase("/Sserver\\base", dt_file, log_file) == 0
    assert commands[0][1:4] == ["DESIGNER", "/IBConnectionString", "Srvr=server;Ref=base;"]
    assert commands[0][-2] == "/DumpIB"
    assert commands[0][-1].endswith(".dt")
    assert commands[1][-2:] == ["/RestoreIB", str(dt_file)]


@pytest.mark.parametrize("operation", ["dump", "restore"])
def test_designer_dt_commands_reject_error_in_out_log(
    tmp_path, monkeypatch, operation
):
    tool = tmp_path / "1cv8.exe"
    tool.write_bytes(b"")
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"previous backup")
    log_file = tmp_path / "operation.log"

    def fake_run(cmd, **kwargs):
        log_file.write_text("Ошибка выполнения операции", encoding="utf-8")
        if "/DumpIB" in cmd:
            Path(cmd[cmd.index("/DumpIB") + 1]).write_bytes(b"invalid new dump")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("src.converters.base.tools.subprocess.run", fake_run)
    wrapper = V8ToolWrapper({"V8_TOOL": str(tool)}, Logger(silent=True))

    with pytest.raises(ToolExecutionError, match="DT"):
        if operation == "dump":
            wrapper.dump_infobase("/Sserver\\base", dt_file, log_file)
        else:
            wrapper.restore_infobase("/Sserver\\base", dt_file, log_file)

    assert dt_file.read_bytes() == b"previous backup"


@pytest.mark.parametrize("operation", ["dump", "restore"])
def test_designer_dt_commands_ignore_stale_out_log(
    tmp_path, monkeypatch, operation
):
    tool = tmp_path / "1cv8.exe"
    tool.write_bytes(b"")
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    log_file = tmp_path / "operation.log"
    log_file.write_text("Ошибка от предыдущего запуска", encoding="utf-8")

    def fake_run(cmd, **kwargs):
        if "/DumpIB" in cmd:
            Path(cmd[cmd.index("/DumpIB") + 1]).write_bytes(b"fresh dt")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("src.converters.base.tools.subprocess.run", fake_run)
    wrapper = V8ToolWrapper({"V8_TOOL": str(tool)}, Logger(silent=True))

    if operation == "dump":
        assert wrapper.dump_infobase("/Sserver\\base", dt_file, log_file) == 0
        assert dt_file.read_bytes() == b"fresh dt"
    else:
        assert wrapper.restore_infobase("/Sserver\\base", dt_file, log_file) == 0


def test_ibcmd_dt_commands_use_server_database_parameters(tmp_path, monkeypatch):
    tool = tmp_path / "ibcmd.exe"
    tool.write_bytes(b"")
    dt_file = tmp_path / "backup.dt"
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        if cmd[2] == "dump":
            dt_file.write_bytes(b"dt")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("src.converters.base.tools.subprocess.run", fake_run)
    wrapper = IbcmdToolWrapper(
        {
            "IBCMD_TOOL": str(tool),
            "V8_SRC_PATH": "/Sserver\\base",
            "V8_DB_SRV_DBMS": "PostgreSQL",
            "V8_DB_SRV_USR": "db_user",
            "V8_DB_SRV_PWD": "db_password",
            "V8_IB_USER": "ib_user",
            "V8_IB_PWD": "ib_password",
            "IBCMD_DATA": str(tmp_path / "ibcmd_data"),
        },
        Logger(silent=True),
    )

    assert wrapper.dump_infobase(Path("."), dt_file, use_server=True) == 0
    assert wrapper.restore_infobase(Path("."), dt_file, use_server=True) == 0
    expected_options = {
        f"--data={tmp_path / 'ibcmd_data'}",
        "--dbms=PostgreSQL",
        "--db-server=server",
        "--db-name=base",
        "--db-user=db_user",
        "--db-pwd=db_password",
        "--user=ib_user",
        "--password=ib_password",
    }
    assert commands[0][1:3] == ["infobase", "dump"]
    assert expected_options <= set(commands[0])
    assert commands[0][-1] == str(dt_file)
    assert commands[1][1:3] == ["infobase", "restore"]
    assert expected_options <= set(commands[1])
    assert "--force" in commands[1]
    assert "--create-database" not in commands[1]
    assert commands[1][-1] == str(dt_file)


def test_ibcmd_restore_creates_missing_file_database(tmp_path, monkeypatch):
    tool = tmp_path / "ibcmd.exe"
    tool.write_bytes(b"")
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = tmp_path / "new_ib"
    target_ib.mkdir()
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("src.converters.base.tools.subprocess.run", fake_run)
    wrapper = IbcmdToolWrapper(
        {"IBCMD_TOOL": str(tool), "IBCMD_DATA": str(tmp_path / "ibcmd_data")},
        Logger(silent=True),
    )

    assert wrapper.restore_infobase(target_ib, dt_file) == 0
    assert f"--db-path={target_ib}" in commands[0]
    assert "--create-database" in commands[0]


@pytest.mark.parametrize("operation", ["dump", "restore"])
def test_ibcmd_file_dt_commands_ignore_global_server_settings(
    tmp_path, monkeypatch, operation
):
    tool = tmp_path / "ibcmd.exe"
    tool.write_bytes(b"")
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    file_ib = tmp_path / "file_ib"
    file_ib.mkdir()
    (file_ib / "1cv8.1cd").write_bytes(b"db")
    commands = []

    def fake_run(cmd, **kwargs):
        commands.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr("src.converters.base.tools.subprocess.run", fake_run)
    wrapper = IbcmdToolWrapper(
        {
            "IBCMD_TOOL": str(tool),
            "V8_IB_SERVER": "production-server",
            "V8_IB_NAME": "production-base",
        },
        Logger(silent=True),
    )

    if operation == "dump":
        assert wrapper.dump_infobase(file_ib, dt_file, use_server=False) == 0
    else:
        assert wrapper.restore_infobase(file_ib, dt_file, use_server=False) == 0

    assert f"--db-path={file_ib}" in commands[0]
    assert not any(arg.startswith("--db-server=") for arg in commands[0])


def test_server_reference_keeps_explicit_database_parameters(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    env = {
        "ScriptName": "dt2ib",
        "V8_SRC_PATH": str(dt_file),
        "V8_DST_PATH": "/Scluster-server\\explicit-base",
        "V8_CONVERT_TOOL": "ibcmd",
        "V8_IB_SERVER": "database-server",
        "V8_IB_NAME": "stale-base",
    }
    converter = ConfigurationConverter(env, silent=True)

    converter._set_server_ib_env(env["V8_DST_PATH"])

    assert env["V8_IB_SERVER"] == "database-server"
    assert env["V8_IB_NAME"] == "stale-base"


def test_debug_command_masks_passwords(tmp_path):
    messages = []
    logger = Logger(silent=False, debug=True)
    logger.debug_msg = messages.append
    wrapper = IbcmdToolWrapper({}, logger)

    wrapper._log_command(
        [
            "ibcmd.exe",
            "--password=ib-secret",
            "--db-pwd=db-secret",
            "/Pdesigner-secret",
        ]
    )

    log = "\n".join(messages)
    assert "ib-secret" not in log
    assert "db-secret" not in log
    assert "designer-secret" not in log
    assert "***" in log


def test_conversion_reports_temp_directory_on_tool_error(tmp_path, capsys):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = tmp_path / "target_ib"
    target_ib.mkdir()
    (target_ib / "1cv8.1cd").write_bytes(b"db")
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=False,
    )
    converter.v8_tool.is_available = lambda: True
    converter.v8_tool.restore_infobase = lambda *args, **kwargs: (_ for _ in ()).throw(
        ToolExecutionError("restore failed")
    )

    assert converter.convert() == 1
    output = capsys.readouterr().out
    assert "Временные файлы сохранены" in output
    assert str(converter.temp_dir) in output

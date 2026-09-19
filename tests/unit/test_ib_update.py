"""Проверки управляемого обновления конфигурации информационной базы."""

import subprocess
from pathlib import Path

import pytest

from src.converters.base.converter import Logger, ValidationError
from src.converters.base.tools import IbcmdToolWrapper, V8ToolWrapper
from src.converters.configuration.converter import ConfigurationConverter
from src.converters.extension.converter import ExtensionConverter


def _file_ib(path: Path) -> Path:
    path.mkdir()
    (path / "1cv8.1cd").write_bytes(b"db")
    return path


def test_dt2ib_updates_database_after_restore_when_enabled(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.v8_tool.is_available = lambda: True
    converter.v8_tool.restore_infobase = (
        lambda *args, **kwargs: calls.append("restore") or 0
    )
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update") or 0
    )

    assert converter.convert() == 0
    assert calls == ["restore", "update"]


def test_dt2ib_reports_completion_only_after_update(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = _file_ib(tmp_path / "target_ib")
    events = []
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
        progress_callback=lambda stage, percent: events.append((stage, percent)),
    )
    converter.v8_tool.is_available = lambda: True
    converter.v8_tool.restore_infobase = lambda *args, **kwargs: 0
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: events.append(("update", 95)) or 0
    )

    assert converter.convert() == 0
    assert events[-2:] == [("update", 95), ("Конвертация завершена", 100)]
    assert events.count(("Конвертация завершена", 100)) == 1


def test_dt2ib_does_not_update_database_by_default(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.v8_tool.is_available = lambda: True
    converter.v8_tool.restore_infobase = (
        lambda *args, **kwargs: calls.append("restore") or 0
    )
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update") or 0
    )

    assert converter.convert() == 0
    assert calls == ["restore"]


def test_dt2ib_fails_when_requested_update_fails(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    converter.v8_tool.is_available = lambda: True
    converter.v8_tool.restore_infobase = lambda *args, **kwargs: 0
    converter.v8_tool.update_database_configuration = lambda *args, **kwargs: 1

    assert converter.convert() == 1


def test_dt2ib_does_not_update_after_failed_restore(tmp_path):
    dt_file = tmp_path / "backup.dt"
    dt_file.write_bytes(b"dt")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ConfigurationConverter(
        {
            "ScriptName": "dt2ib",
            "V8_SRC_PATH": str(dt_file),
            "V8_DST_PATH": str(target_ib),
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    converter.v8_tool.is_available = lambda: True
    calls = []
    converter.v8_tool.restore_infobase = lambda *args, **kwargs: 1
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update") or 0
    )

    assert converter.convert() == 1
    assert calls == []


@pytest.mark.parametrize("script_name", ["dt2ib", "conf2ib"])
def test_configuration_scenarios_reject_invalid_ib_update_flag(
    tmp_path, script_name
):
    source = tmp_path / ("backup.dt" if script_name == "dt2ib" else "config.cf")
    source.write_bytes(b"data")
    converter = ConfigurationConverter(
        {
            "ScriptName": script_name,
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": str(tmp_path / "target_ib"),
            "V8_IB_UPDATE": "yes",
        },
        silent=True,
    )

    with pytest.raises(ValidationError, match="V8_IB_UPDATE"):
        converter.validate()


@pytest.mark.parametrize("convert_tool", ["designer", "ibcmd"])
def test_conf2ib_updates_existing_database_when_enabled(tmp_path, convert_tool):
    source = tmp_path / "config.cf"
    source.write_bytes(b"cf")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ConfigurationConverter(
        {
            "ScriptName": "conf2ib",
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": str(target_ib),
            "V8_CONVERT_TOOL": convert_tool,
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.v8_tool.is_available = lambda: True
    converter.ibcmd_tool.is_available = lambda: True
    converter.v8_tool.load_config_from_cf = (
        lambda *args, **kwargs: calls.append("load") or 0
    )
    converter.ibcmd_tool.import_config_from_cf = (
        lambda *args, **kwargs: calls.append("load") or 0
    )
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update") or 0
    )
    converter.ibcmd_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update") or 0
    )

    assert converter.convert() == 0
    assert calls == ["load", "update"]


def test_conf2ib_with_ibcmd_does_not_require_designer(tmp_path):
    source = tmp_path / "config.cf"
    source.write_bytes(b"cf")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ConfigurationConverter(
        {
            "ScriptName": "conf2ib",
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": str(target_ib),
            "V8_CONVERT_TOOL": "ibcmd",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    converter.v8_tool.is_available = lambda: False
    converter.ibcmd_tool.is_available = lambda: True
    converter.ibcmd_tool.import_config_from_cf = lambda *args, **kwargs: 0

    assert converter.convert() == 0


@pytest.mark.parametrize("source_kind", ["cfe", "xml", "edt"])
def test_ext2ib_loads_each_supported_source_into_existing_database(
    tmp_path, source_kind
):
    if source_kind == "cfe":
        source = tmp_path / "extension.cfe"
        source.write_bytes(b"cfe")
    else:
        source = tmp_path / source_kind
        source.mkdir()
        marker = "Configuration.xml" if source_kind == "xml" else "DT-INF"
        (source / marker).write_text("stub", encoding="utf-8")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ExtensionConverter(
        {
            "ScriptName": "ext2ib",
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": str(target_ib),
            "V8_EXT_NAME": "TestExtension",
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.v8_tool.is_available = lambda: True
    converter.edt_tool.is_available = lambda: True

    def export_to_xml(edt_project, xml_output, workspace):
        calls.append("export")
        xml_output.mkdir(parents=True, exist_ok=True)
        (xml_output / "Configuration.xml").write_text("stub", encoding="utf-8")
        return 0

    converter.edt_tool.export_to_xml = export_to_xml
    converter.v8_tool.load_config_from_cf = (
        lambda *args, **kwargs: calls.append("load") or 0
    )
    converter.v8_tool.load_config_from_files = (
        lambda *args, **kwargs: calls.append("load") or 0
    )
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update") or 0
    )

    converter.validate()
    assert converter.convert() == 0
    expected = ["export", "load", "update"] if source_kind == "edt" else ["load", "update"]
    assert calls == expected


def test_ext2ib_ibcmd_loads_and_applies_named_extension_to_server(tmp_path):
    source = tmp_path / "extension.cfe"
    source.write_bytes(b"cfe")
    converter = ExtensionConverter(
        {
            "ScriptName": "ext2ib",
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": "/Scluster\\base",
            "V8_EXT_NAME": "TestExtension",
            "V8_CONVERT_TOOL": "ibcmd",
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.ibcmd_tool.is_available = lambda: True
    converter.ibcmd_tool.import_config_from_cf = (
        lambda *args, **kwargs: calls.append(("load", kwargs)) or 0
    )
    converter.ibcmd_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append(("update", kwargs)) or 0
    )

    converter.validate()
    assert converter.convert() == 0
    assert calls == [
        ("load", {"db_path": Path("."), "cf_file": source,
                  "extension_name": "TestExtension", "use_server": True}),
        ("update", {"db_path": Path("."), "use_server": True,
                    "extension_name": "TestExtension"}),
    ]


def test_conf2ib_updates_with_designer_after_ibcmd_import_fallback(tmp_path):
    source = tmp_path / "config.cf"
    source.write_bytes(b"cf")
    converter = ConfigurationConverter(
        {
            "ScriptName": "conf2ib",
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": "/Scluster\\base",
            "V8_CONVERT_TOOL": "ibcmd",
            "V8_IB_UPDATE": "1",
            "V8_TEMP": str(tmp_path / "temp"),
        },
        silent=True,
    )
    calls = []
    converter.ibcmd_tool.is_available = lambda: True

    def import_with_fallback(*args, **kwargs):
        converter.ibcmd_tool.last_import_tool = "designer"
        calls.append("load-designer")
        return 0

    converter.ibcmd_tool.import_config_from_cf = import_with_fallback
    converter.ibcmd_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update-ibcmd") or 0
    )
    converter.v8_tool.update_database_configuration = (
        lambda *args, **kwargs: calls.append("update-designer") or 0
    )

    assert converter.convert() == 0
    assert calls == ["load-designer", "update-designer"]


def test_ext2ib_rejects_invalid_ib_update_flag(tmp_path):
    source = tmp_path / "extension.cfe"
    source.write_bytes(b"cfe")
    target_ib = _file_ib(tmp_path / "target_ib")
    converter = ExtensionConverter(
        {
            "ScriptName": "ext2ib",
            "V8_SRC_PATH": str(source),
            "V8_DST_PATH": str(target_ib),
            "V8_EXT_NAME": "TestExtension",
            "V8_IB_UPDATE": "true",
        },
        silent=True,
    )

    with pytest.raises(ValidationError, match="V8_IB_UPDATE"):
        converter.validate()


@pytest.mark.parametrize("extension_name", [None, "TestExtension"])
def test_designer_update_database_configuration_command(
    tmp_path, monkeypatch, extension_name
):
    tool = tmp_path / "1cv8.exe"
    tool.write_bytes(b"")
    commands = []
    monkeypatch.setattr(
        "src.converters.base.tools.subprocess.run",
        lambda cmd, **kwargs: commands.append(cmd)
        or subprocess.CompletedProcess(cmd, 0, "", ""),
    )
    wrapper = V8ToolWrapper({"V8_TOOL": str(tool)}, Logger(silent=True))

    assert wrapper.update_database_configuration(
        "/Sserver\\base", tmp_path / "update.log", extension_name=extension_name
    ) == 0
    assert commands[0][1:4] == [
        "DESIGNER", "/IBConnectionString", "Srvr=server;Ref=base;"
    ]
    assert "/UpdateDBCfg" in commands[0]
    if extension_name:
        assert commands[0][-2:] == ["-Extension", extension_name]


def test_ibcmd_update_database_configuration_command(tmp_path, monkeypatch):
    tool = tmp_path / "ibcmd.exe"
    tool.write_bytes(b"")
    commands = []
    monkeypatch.setattr(
        "src.converters.base.tools.subprocess.run",
        lambda cmd, **kwargs: commands.append(cmd)
        or subprocess.CompletedProcess(cmd, 0, "", ""),
    )
    wrapper = IbcmdToolWrapper(
        {"IBCMD_TOOL": str(tool), "V8_DST_PATH": "/Sserver\\base"},
        Logger(silent=True),
    )

    assert wrapper.update_database_configuration(
        Path("."), use_server=True, extension_name="TestExtension"
    ) == 0
    assert commands[0][1:4] == ["infobase", "config", "apply"]
    assert "--db-server=server" in commands[0]
    assert "--db-name=base" in commands[0]
    assert "--extension=TestExtension" in commands[0]
    assert "--force" in commands[0]


@pytest.mark.parametrize("source_kind", ["cf", "xml"])
def test_ibcmd_loads_named_extension_into_file_database(
    tmp_path, monkeypatch, source_kind
):
    tool = tmp_path / "ibcmd.exe"
    tool.write_bytes(b"")
    source = tmp_path / ("extension.cfe" if source_kind == "cf" else "xml")
    if source_kind == "cf":
        source.write_bytes(b"cfe")
    else:
        source.mkdir()
    target_ib = _file_ib(tmp_path / "target_ib")
    commands = []
    monkeypatch.setattr(
        "src.converters.base.tools.subprocess.run",
        lambda cmd, **kwargs: commands.append(cmd)
        or subprocess.CompletedProcess(cmd, 0, "", ""),
    )
    wrapper = IbcmdToolWrapper(
        {
            "IBCMD_TOOL": str(tool),
            "V8_IB_SERVER": "unrelated-server",
            "V8_IB_NAME": "unrelated-base",
        },
        Logger(silent=True),
    )

    if source_kind == "cf":
        result = wrapper.import_config_from_cf(
            target_ib,
            source,
            extension_name="TestExtension",
            use_server=False,
        )
    else:
        result = wrapper.import_config_from_xml(
            target_ib,
            source,
            extension_name="TestExtension",
            use_server=False,
        )

    assert result == 0
    assert f"--db-path={target_ib}" in commands[0]
    assert "--extension=TestExtension" in commands[0]
    assert not any(arg.startswith("--db-server=") for arg in commands[0])


def test_ibcmd_server_import_fallback_uses_cluster_destination(
    tmp_path, monkeypatch
):
    tool = tmp_path / "ibcmd.exe"
    tool.write_bytes(b"")
    source = tmp_path / "config.cf"
    source.write_bytes(b"cf")
    captured = []
    monkeypatch.setattr(
        "src.converters.base.tools.subprocess.run",
        lambda cmd, **kwargs: subprocess.CompletedProcess(
            cmd, 1, "", "ibcmd import failed"
        ),
    )
    monkeypatch.setattr(
        V8ToolWrapper,
        "load_config_from_cf",
        lambda self, ib_connection, cf_file, log_file, extension_name=None:
        captured.append(ib_connection) or 0,
    )
    wrapper = IbcmdToolWrapper(
        {
            "IBCMD_TOOL": str(tool),
            "V8_TOOL": str(tmp_path / "1cv8.exe"),
            "V8_DST_PATH": "/Scluster-server\\cluster-ref",
            "V8_IB_SERVER": "physical-db-server",
            "V8_IB_NAME": "physical-db-name",
        },
        Logger(silent=True),
    )

    assert wrapper.import_config_from_cf(
        Path('.'), source, use_server=True
    ) == 0
    assert captured == ["/Scluster-server\\cluster-ref"]
    assert wrapper.last_import_tool == "designer"

"""
Unit-тесты для ConfigurationConverter.
"""

from pathlib import Path

from src.converters.configuration.converter import ConfigurationConverter


def test_conf2edt_from_cf_uses_dst_path_as_project_path(tmp_path):
    """Для CF -> EDT V8_DST_PATH используется как путь итогового EDT проекта."""
    src_cf = tmp_path / "demo_otus_edt.cf"
    src_cf.write_text("stub", encoding="utf-8")
    dst_project = tmp_path / "otus_edt"

    env_vars = {
        "ScriptName": "conf2edt",
        "V8_SRC_PATH": str(src_cf),
        "V8_DST_PATH": str(dst_project),
        "V8_TEMP_AFTER_CLEAN": "0",
    }
    converter = ConfigurationConverter(env_vars, silent=True)

    captured = {}

    converter.v8_tool.is_available = lambda: True
    converter.edt_tool.is_available = lambda: True
    converter.v8_tool.create_infobase = lambda ib_connection, log_file: 0
    converter.v8_tool.load_config_from_cf = lambda ib_connection, cf_file, log_file: 0

    def dump_config_to_files(ib_connection, output_dir, log_file):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "Configuration.xml").write_text("<Configuration/>", encoding="utf-8")
        return 0

    def import_to_edt(xml_source_path, edt_project_path, workspace_path, entity_type):
        captured["edt_project_path"] = edt_project_path
        edt_project_path.mkdir(parents=True, exist_ok=True)
        (edt_project_path / ".project").write_text("stub", encoding="utf-8")
        return 0

    converter.v8_tool.dump_config_to_files = dump_config_to_files
    converter.edt_tool.import_configuration_files_to_edt_project = import_to_edt

    exit_code = converter.convert()

    assert exit_code == 0
    assert captured["edt_project_path"] == dst_project


def test_conf2edt_from_ib_uses_dst_path_as_project_path(tmp_path):
    """Для IB -> EDT V8_DST_PATH используется как путь итогового EDT проекта."""
    src_ib = tmp_path / "demo_ib"
    src_ib.mkdir()
    (src_ib / "1cv8.1cd").write_text("stub", encoding="utf-8")
    dst_project = tmp_path / "otus_edt"

    env_vars = {
        "ScriptName": "conf2edt",
        "V8_SRC_PATH": f"/F{src_ib}",
        "V8_DST_PATH": str(dst_project),
        "V8_TEMP_AFTER_CLEAN": "0",
    }
    converter = ConfigurationConverter(env_vars, silent=True)

    captured = {}

    converter.edt_tool.is_available = lambda: True
    converter.v8_tool.is_available = lambda: True

    def dump_config_to_files(ib_connection, output_dir, log_file):
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "Configuration.xml").write_text("<Configuration/>", encoding="utf-8")
        return 0

    def import_to_edt(xml_source_path, edt_project_path, workspace_path, entity_type):
        captured["edt_project_path"] = edt_project_path
        edt_project_path.mkdir(parents=True, exist_ok=True)
        (edt_project_path / ".project").write_text("stub", encoding="utf-8")
        return 0

    converter.v8_tool.dump_config_to_files = dump_config_to_files
    converter.edt_tool.import_configuration_files_to_edt_project = import_to_edt

    exit_code = converter.convert()

    assert exit_code == 0
    assert captured["edt_project_path"] == dst_project


def test_conf2edt_from_cf_uses_ibcmd_for_intermediate_steps(tmp_path):
    """Для CF -> EDT с V8_CONVERT_TOOL=ibcmd должны использоваться ibcmd create/export."""
    src_cf = tmp_path / "demo_otus_edt.cf"
    src_cf.write_text("stub", encoding="utf-8")
    dst_project = tmp_path / "otus_edt"

    env_vars = {
        "ScriptName": "conf2edt",
        "V8_SRC_PATH": str(src_cf),
        "V8_DST_PATH": str(dst_project),
        "V8_CONVERT_TOOL": "ibcmd",
        "V8_TEMP_AFTER_CLEAN": "0",
    }
    converter = ConfigurationConverter(env_vars, silent=True)

    calls = []

    converter.ibcmd_tool.is_available = lambda: True
    converter.edt_tool.is_available = lambda: True
    converter.v8_tool.is_available = lambda: False
    converter.v8_tool.create_infobase = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("designer create_infobase не должен вызываться"))
    converter.v8_tool.load_config_from_cf = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("designer load_config_from_cf не должен вызываться"))
    converter.v8_tool.dump_config_to_files = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("designer dump_config_to_files не должен вызываться"))

    def create_infobase_with_config(db_path, xml_path=None, cf_file=None):
        calls.append(("create_ib", db_path, xml_path, cf_file))
        return 0

    def export_config_to_files(db_path, output_dir, extension_name=None):
        calls.append(("export_xml", db_path, output_dir, extension_name))
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "Configuration.xml").write_text("<Configuration/>", encoding="utf-8")
        return 0

    def import_to_edt(xml_source_path, edt_project_path, workspace_path, entity_type):
        calls.append(("import_edt", xml_source_path, edt_project_path, workspace_path, entity_type))
        edt_project_path.mkdir(parents=True, exist_ok=True)
        (edt_project_path / ".project").write_text("stub", encoding="utf-8")
        return 0

    converter.ibcmd_tool.create_infobase_with_config = create_infobase_with_config
    converter.ibcmd_tool.import_config_from_cf = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("ibcmd import_config_from_cf не должен вызываться"))
    converter.ibcmd_tool.export_config_to_files = export_config_to_files
    converter.edt_tool.import_configuration_files_to_edt_project = import_to_edt

    exit_code = converter.convert()

    assert exit_code == 0
    assert calls[0][0] == "create_ib"
    assert calls[0][3] == src_cf
    assert calls[1][0] == "export_xml"
    assert calls[2][0] == "import_edt"
    assert calls[2][2] == dst_project

import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT_DIR / "scripts" / "validate_release_tag.py"


def test_release_tag_matching_application_version_is_accepted(tmp_path):
    constants = tmp_path / "constants.py"
    constants.write_text('VERSION = "2.3.4"\n', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "v2.3.4", "--constants", str(constants)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_release_tag_different_from_application_version_is_rejected(tmp_path):
    constants = tmp_path / "constants.py"
    constants.write_text('VERSION = "2.3.4"\n', encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "v9.9.9", "--constants", str(constants)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "v2.3.4" in result.stderr

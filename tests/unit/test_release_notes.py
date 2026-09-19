import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
EXTRACTOR = ROOT_DIR / "scripts" / "extract_release_notes.py"


def test_extracts_only_notes_for_requested_tag(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        """# Changelog

## [1.4.1] - 2026-09-19

### Первый публичный релиз

- Добавлен GUI.

## [1.4.0] - 2026-09-01

- Старое изменение.
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(EXTRACTOR), "v1.4.1", str(changelog)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "### Первый публичный релиз\n\n- Добавлен GUI.\n"


def test_rejects_tag_missing_from_changelog(tmp_path):
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        "# Changelog\n\n## [1.4.0] - 2026-09-01\n\n- Изменение.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(EXTRACTOR), "v1.4.1", str(changelog)],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "1.4.1" in result.stderr

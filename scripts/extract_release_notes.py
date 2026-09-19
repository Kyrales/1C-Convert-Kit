#!/usr/bin/env python3
"""Извлекает из changelog описание релиза для указанного Git-тега."""

import argparse
import re
import sys
from pathlib import Path


DEFAULT_CHANGELOG = Path(__file__).resolve().parents[1] / "CHANGELOG.md"


def extract_release_notes(tag: str, changelog: Path) -> str:
    if not tag.startswith("v") or len(tag) == 1:
        raise ValueError(f"Некорректный тег релиза: {tag!r}")

    version = re.escape(tag[1:])
    pattern = rf"^## \[{version}\][^\n]*\n(?P<notes>.*?)(?=^## \[|\Z)"
    match = re.search(
        pattern,
        changelog.read_text(encoding="utf-8"),
        re.MULTILINE | re.DOTALL,
    )
    if not match or not match.group("notes").strip():
        raise ValueError(f"В {changelog} не найден раздел для версии {tag[1:]}")

    return match.group("notes").strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("changelog", type=Path, nargs="?", default=DEFAULT_CHANGELOG)
    args = parser.parse_args()

    try:
        notes = extract_release_notes(args.tag, args.changelog)
    except ValueError as error:
        parser.error(str(error))

    sys.stdout.write(f"{notes}\n")


if __name__ == "__main__":
    main()

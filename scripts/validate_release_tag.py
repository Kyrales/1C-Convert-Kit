#!/usr/bin/env python3
"""Проверяет соответствие Git-тега версии приложения."""

import argparse
import ast
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONSTANTS = ROOT_DIR / "src" / "gui" / "constants.py"


def read_version(constants_path: Path) -> str:
    tree = ast.parse(constants_path.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id == "VERSION":
            if isinstance(node.value, ast.Constant) and isinstance(
                node.value.value, str
            ):
                return node.value.value
    raise ValueError(f"В {constants_path} не найдена строковая константа VERSION")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    parser.add_argument("--constants", type=Path, default=DEFAULT_CONSTANTS)
    args = parser.parse_args()

    expected_tag = f"v{read_version(args.constants)}"
    if args.tag != expected_tag:
        parser.error(
            f"тег {args.tag!r} не совпадает с версией приложения {expected_tag!r}"
        )

    print(f"Версия релиза подтверждена: {expected_tag}")


if __name__ == "__main__":
    main()

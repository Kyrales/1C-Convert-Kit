#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Сканирование и загрузка информации о проектах и группах.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Literal, TypedDict, Union

# Добавляем корневую директорию проекта в sys.path для корректных импортов
_SCRIPT_DIR = Path(__file__).parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from core.convert import load_env_file  # type: ignore
from .constants import PROJECTS_DIR

ITEM_TYPE_PROJECT = "project"
ITEM_TYPE_GROUP = "group"
MAX_GROUP_DEPTH = 4
GROUP_ICON = "📁"


class BaseTreeItem(TypedDict):
    """Общая структура элемента дерева."""

    item_type: Literal["project", "group"]
    name: str
    path: str
    relative_path: str
    depth: int


class ProjectDict(BaseTreeItem):
    """Структура данных проекта."""

    item_type: Literal["project"]
    script: str
    env_path: str
    dst_path: str
    custom_dst_path: str | None


class GroupDict(BaseTreeItem):
    """Структура данных группы."""

    item_type: Literal["group"]
    child_count: int
    project_count: int
    children: list[str]


TreeItem = Union[ProjectDict, GroupDict]
TreeIndex = dict[str, TreeItem]


class ProjectScanner:
    """Сканирование и загрузка информации о проектах."""

    GROUP_NAME_RE = re.compile(r"^(?!\.)(?!__)(?!~)[A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9 _-]*$")
    last_warnings: list[str] = []

    @staticmethod
    def scan_projects() -> list[ProjectDict]:
        """
        Возвращает плоский список всех проектов для обратной совместимости.
        """
        tree = ProjectScanner.build_tree()
        projects = [
            item
            for item in tree.values()
            if item["item_type"] == ITEM_TYPE_PROJECT
        ]
        return sorted(projects, key=lambda item: item["relative_path"].lower())

    @staticmethod
    def build_tree(base_dir: Path | None = None) -> TreeIndex:
        """
        Строит индекс дерева проектов и групп.
        """
        root = (base_dir or PROJECTS_DIR).resolve()
        tree: TreeIndex = {}
        ProjectScanner.last_warnings = []
        if not root.exists():
            return tree

        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir():
                continue
            ProjectScanner._scan_dir(child, tree)
        return tree

    @staticmethod
    def list_level(tree: TreeIndex, parent_path: Path | None = None) -> list[TreeItem]:
        """
        Возвращает элементы текущего уровня.
        """
        target_relative = ""
        if parent_path is not None:
            try:
                target_relative = str(parent_path.resolve().relative_to(PROJECTS_DIR.resolve())).replace("\\", "/")
            except ValueError:
                target_relative = ""

        items = []
        for item in tree.values():
            parent_relative = str(Path(item["relative_path"]).parent).replace("\\", "/")
            if parent_relative == ".":
                parent_relative = ""
            if parent_relative == target_relative:
                items.append(item)
        return ProjectScanner.sort_items(items)

    @staticmethod
    def get_item(tree: TreeIndex, path: str | Path) -> TreeItem | None:
        """Возвращает элемент по пути."""
        candidate = Path(path)
        try:
            relative_path = str(candidate.resolve().relative_to(PROJECTS_DIR.resolve())).replace("\\", "/")
        except ValueError:
            relative_path = str(candidate).replace("\\", "/")
        return tree.get(relative_path)

    @staticmethod
    def flatten_projects(items: list[TreeItem], tree: TreeIndex) -> list[ProjectDict]:
        """
        Разворачивает набор элементов в плоский список уникальных проектов.
        """
        result: list[ProjectDict] = []
        seen_paths: set[str] = set()

        for item in ProjectScanner.sort_items(items):
            if item["item_type"] == ITEM_TYPE_PROJECT:
                project = item
                if project["path"] not in seen_paths:
                    seen_paths.add(project["path"])
                    result.append(project)
                continue

            for project in ProjectScanner._flatten_group_projects(item, tree):
                if project["path"] not in seen_paths:
                    seen_paths.add(project["path"])
                    result.append(project)

        return result

    @staticmethod
    def get_groups(tree: TreeIndex) -> list[GroupDict]:
        """Возвращает все группы."""
        groups = [item for item in tree.values() if item["item_type"] == ITEM_TYPE_GROUP]
        return sorted(groups, key=lambda item: item["relative_path"].lower())

    @staticmethod
    def validate_group_name(name: str, existing_names: set[str] | None = None) -> None:
        """Валидирует имя группы."""
        stripped = name.strip()
        if not stripped:
            raise ValueError("Имя группы не может быть пустым")

        invalid_chars = r'/\:*?"<>|'
        for char in invalid_chars:
            if char in stripped:
                raise ValueError(f"Имя группы содержит недопустимый символ: {char}")

        if not ProjectScanner.GROUP_NAME_RE.match(stripped):
            raise ValueError(
                "Имя группы должно начинаться с буквы или цифры и может содержать буквы, цифры, пробелы, _ и -"
            )

        if existing_names and stripped in existing_names:
            raise ValueError(f"Элемент с именем '{stripped}' уже существует")

    @staticmethod
    def validate_move_target(
        source_paths: list[Path],
        target_path: Path,
        tree: TreeIndex,
    ) -> None:
        """Валидирует перемещение проектов и групп."""
        target_resolved = target_path.resolve()
        root = PROJECTS_DIR.resolve()
        if target_resolved != root and ProjectScanner.get_item(tree, target_resolved) is None:
            raise ValueError("Выберите существующую группу или корень projects")

        for source_path in source_paths:
            source_resolved = source_path.resolve()
            if source_resolved.parent == target_resolved:
                raise ValueError("Элемент уже находится в выбранной папке")

            if target_resolved == source_resolved:
                raise ValueError("Нельзя переместить элемент в самого себя")

            if ProjectScanner._is_subpath(target_resolved, source_resolved):
                raise ValueError("Нельзя переместить группу в саму себя или в ее подгруппу")

            final_depth = ProjectScanner.compute_depth(target_resolved / source_resolved.name)
            if final_depth > MAX_GROUP_DEPTH:
                raise ValueError(f"Нельзя превысить глубину вложенности {MAX_GROUP_DEPTH}")

            if (target_resolved / source_resolved.name).exists():
                raise ValueError(f"В папке назначения уже есть элемент '{source_resolved.name}'")

    @staticmethod
    def should_skip_dir(path: Path) -> bool:
        """Проверяет, нужно ли пропустить каталог."""
        name = path.name
        return name.startswith(".") or name.startswith("__") or name.startswith("~")

    @staticmethod
    def compute_depth(path: Path) -> int:
        """Считает глубину относительно PROJECTS_DIR."""
        try:
            relative = path.resolve().relative_to(PROJECTS_DIR.resolve())
        except ValueError:
            return 0
        return len(relative.parts)

    @staticmethod
    def sort_items(items: list[TreeItem]) -> list[TreeItem]:
        """Стабильно сортирует элементы: группы выше, затем по имени."""
        return sorted(items, key=lambda item: (0 if item["item_type"] == ITEM_TYPE_GROUP else 1, item["name"].lower()))

    @staticmethod
    def count_direct_children(group: GroupDict, tree: TreeIndex) -> tuple[list[GroupDict], list[ProjectDict]]:
        """Возвращает прямые подгруппы и проекты группы."""
        groups: list[GroupDict] = []
        projects: list[ProjectDict] = []
        for child_rel in group["children"]:
            item = tree.get(child_rel)
            if item is None:
                continue
            if item["item_type"] == ITEM_TYPE_GROUP:
                groups.append(item)
            else:
                projects.append(item)
        return ProjectScanner.sort_items(groups), ProjectScanner.sort_items(projects)  # type: ignore[arg-type]

    @staticmethod
    def _scan_dir(path: Path, tree: TreeIndex) -> bool:
        """
        Сканирует директорию. Возвращает True, если каталог содержит корректные элементы.
        """
        if ProjectScanner.should_skip_dir(path):
            return False

        depth = ProjectScanner.compute_depth(path)
        if depth > MAX_GROUP_DEPTH:
            ProjectScanner.last_warnings.append(
                f"Пропущен каталог глубже допустимого уровня: {path}"
            )
            return False

        env_files = sorted(path.glob("*.env"))
        project_entry = ProjectScanner._build_project(path, env_files, depth)
        if project_entry is not None:
            tree[project_entry["relative_path"]] = project_entry
            return True
        has_invalid_env = bool(env_files)

        child_items: list[TreeItem] = []
        for child in sorted(path.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir():
                continue
            if ProjectScanner._scan_dir(child, tree):
                item = ProjectScanner.get_item(tree, child)
                if item is not None:
                    child_items.append(item)

        if not child_items:
            if has_invalid_env:
                return False
            relative_path = str(path.resolve().relative_to(PROJECTS_DIR.resolve())).replace("\\", "/")
            tree[relative_path] = {
                "item_type": ITEM_TYPE_GROUP,
                "name": path.name,
                "path": str(path.resolve()),
                "relative_path": relative_path,
                "depth": depth,
                "child_count": 0,
                "project_count": 0,
                "children": [],
            }
            return True

        group_entry = ProjectScanner._build_group(path, child_items, depth)
        tree[group_entry["relative_path"]] = group_entry
        return True

    @staticmethod
    def _build_project(path: Path, env_files: list[Path], depth: int) -> ProjectDict | None:
        """Создает запись проекта, если найден валидный .env."""
        for env_file in env_files:
            script_name, dst_path = ProjectScanner._read_env_data(env_file)
            if not script_name:
                continue
            relative_path = str(path.resolve().relative_to(PROJECTS_DIR.resolve())).replace("\\", "/")
            return {
                "item_type": ITEM_TYPE_PROJECT,
                "name": path.name,
                "path": str(path.resolve()),
                "relative_path": relative_path,
                "depth": depth,
                "script": script_name,
                "env_path": str(env_file.resolve()),
                "dst_path": dst_path,
                "custom_dst_path": None,
            }
        return None

    @staticmethod
    def _build_group(path: Path, child_items: list[TreeItem], depth: int) -> GroupDict:
        """Создает запись группы."""
        relative_path = str(path.resolve().relative_to(PROJECTS_DIR.resolve())).replace("\\", "/")
        project_count = 0
        children: list[str] = []
        for item in ProjectScanner.sort_items(child_items):
            children.append(item["relative_path"])
            if item["item_type"] == ITEM_TYPE_PROJECT:
                project_count += 1
            else:
                project_count += item["project_count"]  # type: ignore[index]

        return {
            "item_type": ITEM_TYPE_GROUP,
            "name": path.name,
            "path": str(path.resolve()),
            "relative_path": relative_path,
            "depth": depth,
            "child_count": len(child_items),
            "project_count": project_count,
            "children": children,
        }

    @staticmethod
    def _flatten_group_projects(group: TreeItem, tree: TreeIndex) -> list[ProjectDict]:
        """Разворачивает группу depth-first."""
        if group["item_type"] != ITEM_TYPE_GROUP:
            return []

        projects: list[ProjectDict] = []
        for child_rel in group["children"]:
            item = tree.get(child_rel)
            if item is None:
                continue
            if item["item_type"] == ITEM_TYPE_PROJECT:
                projects.append(item)
            else:
                projects.extend(ProjectScanner._flatten_group_projects(item, tree))
        return projects

    @staticmethod
    def _is_subpath(path: Path, parent: Path) -> bool:
        """Проверяет, что path лежит внутри parent."""
        try:
            path.resolve().relative_to(parent.resolve())
            return True
        except ValueError:
            return False

    @staticmethod
    def _read_env_data(env_file: Path) -> tuple[str, str]:
        """
        Читает ScriptName и V8_DST_PATH из .env файла.
        """
        try:
            env_data = load_env_file(str(env_file), silent=True)
            if env_data is None:
                return "", ""
            script_name = env_data.get("ScriptName", "")
            dst_path = env_data.get("V8_DST_PATH", "")
            return script_name, dst_path
        except Exception:
            return "", ""

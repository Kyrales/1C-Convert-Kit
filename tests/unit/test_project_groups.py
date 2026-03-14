#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit-тесты группировки проектов и дерева каталогов.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from src.gui import project_scanner as scanner_module
from src.gui.project_scanner import MAX_GROUP_DEPTH, ProjectScanner


def _write_env(path: Path, script_name: str | None, dst: str = "F:\\out") -> None:
    lines = []
    if script_name is not None:
        lines.append(f"ScriptName={script_name}")
    lines.append(f"V8_DST_PATH={dst}")
    path.write_text("\n".join(lines), encoding="utf-8")


@pytest.fixture()
def temp_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir()
    monkeypatch.setattr(scanner_module, "PROJECTS_DIR", projects_dir)
    return projects_dir


def test_build_tree_detects_group_with_projects(temp_projects: Path) -> None:
    demo = temp_projects / "Demo"
    (demo / "ProjectA").mkdir(parents=True)
    (demo / "ProjectB").mkdir(parents=True)
    _write_env(demo / "ProjectA" / "a.env", "conf2cf")
    _write_env(demo / "ProjectB" / "b.env", "conf2xml")

    tree = ProjectScanner.build_tree(temp_projects)

    demo_group = tree["Demo"]
    assert demo_group["item_type"] == "group"
    assert demo_group["project_count"] == 2  # type: ignore[index]
    assert "Demo/ProjectA" in tree
    assert "Demo/ProjectB" in tree


def test_empty_directory_is_visible_as_group(temp_projects: Path) -> None:
    (temp_projects / "Empty").mkdir()
    tree = ProjectScanner.build_tree(temp_projects)
    assert "Empty" in tree
    assert tree["Empty"]["item_type"] == "group"


def test_directory_with_env_without_script_name_is_not_project(temp_projects: Path) -> None:
    broken = temp_projects / "Broken"
    broken.mkdir()
    _write_env(broken / "broken.env", None)

    tree = ProjectScanner.build_tree(temp_projects)

    assert "Broken" not in tree


def test_service_directories_are_skipped(temp_projects: Path) -> None:
    demo = temp_projects / "Demo"
    (demo / "~0,-1").mkdir(parents=True)
    (demo / "ProjectA").mkdir(parents=True)
    _write_env(demo / "ProjectA" / "a.env", "conf2cf")

    tree = ProjectScanner.build_tree(temp_projects)

    assert "Demo/~0,-1" not in tree
    assert "Demo" in tree


def test_flatten_projects_uses_depth_first_order(temp_projects: Path) -> None:
    root = temp_projects / "Demo"
    (root / "A" / "Project1").mkdir(parents=True)
    (root / "A" / "Project2").mkdir(parents=True)
    (root / "B" / "Project3").mkdir(parents=True)
    _write_env(root / "A" / "Project1" / "1.env", "conf2cf")
    _write_env(root / "A" / "Project2" / "2.env", "conf2cf")
    _write_env(root / "B" / "Project3" / "3.env", "conf2cf")

    tree = ProjectScanner.build_tree(temp_projects)
    demo = tree["Demo"]

    projects = ProjectScanner.flatten_projects([demo], tree)

    assert [project["relative_path"] for project in projects] == [
        "Demo/A/Project1",
        "Demo/A/Project2",
        "Demo/B/Project3",
    ]


def test_validate_group_name_rules() -> None:
    ProjectScanner.validate_group_name("Demo 2")
    ProjectScanner.validate_group_name("БП")
    ProjectScanner.validate_group_name("test-group")

    with pytest.raises(ValueError):
        ProjectScanner.validate_group_name("~demo")
    with pytest.raises(ValueError):
        ProjectScanner.validate_group_name("bad/name")


def test_validate_move_target_rejects_nested_move(temp_projects: Path) -> None:
    demo = temp_projects / "Demo"
    target = demo / "Sub"
    source = demo
    target.mkdir(parents=True)

    tree = {
        "Demo": {
            "item_type": "group",
            "name": "Demo",
            "path": str(source.resolve()),
            "relative_path": "Demo",
            "depth": 1,
            "child_count": 1,
            "project_count": 0,
            "children": ["Demo/Sub"],
        },
        "Demo/Sub": {
            "item_type": "group",
            "name": "Sub",
            "path": str(target.resolve()),
            "relative_path": "Demo/Sub",
            "depth": 2,
            "child_count": 0,
            "project_count": 0,
            "children": [],
        },
    }

    with pytest.raises(ValueError):
        ProjectScanner.validate_move_target([source], target, tree)  # type: ignore[arg-type]


def test_compute_depth_honors_limit(temp_projects: Path) -> None:
    deep = temp_projects
    for part in ["a", "b", "c", "d", "e"]:
        deep = deep / part
    assert ProjectScanner.compute_depth(deep) == MAX_GROUP_DEPTH + 1


def test_move_project_folder_preserves_env_contents(temp_projects: Path) -> None:
    source_group = temp_projects / "Source"
    target_group = temp_projects / "Target"
    project_dir = source_group / "Project1"
    project_dir.mkdir(parents=True)
    target_group.mkdir()
    env_path = project_dir / "project.env"
    _write_env(env_path, "conf2cf", ".\\relative\\out.cf")
    original_content = env_path.read_text(encoding="utf-8")

    shutil.move(str(project_dir), str(target_group / project_dir.name))

    moved_env = target_group / "Project1" / "project.env"
    assert moved_env.exists()
    assert moved_env.read_text(encoding="utf-8") == original_content

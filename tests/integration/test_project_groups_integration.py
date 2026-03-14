#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Интеграционные тесты группировки проектов на реальной структуре projects/.
"""

from __future__ import annotations

from src.gui.project_scanner import ProjectScanner


def test_demo_group_exists_in_real_projects_tree() -> None:
    tree = ProjectScanner.build_tree()

    assert "Demo" in tree
    demo = tree["Demo"]
    assert demo["item_type"] == "group"
    assert demo["project_count"] == 10  # type: ignore[index]


def test_demo_group_contains_expected_projects() -> None:
    tree = ProjectScanner.build_tree()
    projects = ProjectScanner.flatten_projects([tree["Demo"]], tree)

    project_names = [project["name"] for project in projects]
    assert len(project_names) == 10
    assert "Демо_edt_в_cf" in project_names
    assert "Демо_edt_в_cfe" in project_names
    assert "Демо_edt_в_xml" in project_names


def test_service_folder_is_hidden_in_real_tree() -> None:
    tree = ProjectScanner.build_tree()
    assert "Демо_edt_в_cf/~0,-1" not in tree

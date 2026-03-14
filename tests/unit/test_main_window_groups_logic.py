#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit-тесты логики групп в main_window без поднятия реального GUI.
"""

from __future__ import annotations

from pathlib import Path

from src.gui.main_window import CyberpunkGUI
from src.gui.project_scanner import PROJECTS_DIR


class DummyLog:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, text: str, **_: object) -> None:
        self.messages.append(text)

    def update(self, value: str = "", append: bool = False) -> None:
        if append:
            self.messages.append(value)
        else:
            self.messages = [value]


def test_set_current_group_resets_selection() -> None:
    demo_path = (PROJECTS_DIR / "Demo").resolve()
    project_path = (demo_path / "Project1").resolve()
    gui = CyberpunkGUI.__new__(CyberpunkGUI)
    gui.project_tree = {
        "Demo": {
            "item_type": "group",
            "name": "Demo",
            "path": str(demo_path),
            "relative_path": "Demo",
            "depth": 1,
            "child_count": 1,
            "project_count": 1,
            "children": ["Demo/Project1"],
        },
        "Demo/Project1": {
            "item_type": "project",
            "name": "Project1",
            "path": str(project_path),
            "relative_path": "Demo/Project1",
            "depth": 2,
            "script": "conf2cf",
            "env_path": "demo.env",
            "dst_path": "out.cf",
            "custom_dst_path": None,
        },
    }
    gui.current_group_path = None
    gui.current_items = []
    gui.selected_paths = {"x"}
    gui.selected_row = 0
    gui.update_table = lambda: None  # type: ignore[assignment]

    gui._set_current_group(Path(gui.project_tree["Demo"]["path"]))

    assert gui.current_group_path == Path(gui.project_tree["Demo"]["path"])
    assert gui.selected_paths == set()
    assert gui.selected_row is None
    assert len(gui.current_items) == 1
    assert gui.current_items[0]["name"] == "Project1"


def test_handle_table_click_toggles_selected_path() -> None:
    gui = CyberpunkGUI.__new__(CyberpunkGUI)
    gui.current_items = [
        {
            "item_type": "project",
            "name": "Project1",
            "path": "F:/demo/Project1",
            "relative_path": "Demo/Project1",
            "depth": 2,
            "script": "conf2cf",
            "env_path": "demo.env",
            "dst_path": "out.cf",
            "custom_dst_path": None,
        }
    ]
    gui.selected_paths = set()
    gui.selected_row = None
    gui.update_table = lambda: None  # type: ignore[assignment]

    gui._handle_table_click({"-TABLE-": [0]})
    assert gui.selected_paths == {"F:/demo/Project1"}
    assert gui.selected_row == 0

    gui._handle_table_click({"-TABLE-": [0]})
    assert gui.selected_paths == set()


def test_execute_conversion_with_empty_final_projects_does_not_start_runner(monkeypatch) -> None:
    popup_messages: list[str] = []

    def fake_popup(message: str, **_: object) -> None:
        popup_messages.append(message)

    monkeypatch.setattr("src.gui.main_window.sg.popup", fake_popup)

    gui = CyberpunkGUI.__new__(CyberpunkGUI)
    gui.project_tree = {
        "Demo": {
            "item_type": "group",
            "name": "Demo",
            "path": "F:/demo",
            "relative_path": "Demo",
            "depth": 1,
            "child_count": 0,
            "project_count": 0,
            "children": [],
        }
    }
    gui.selected_paths = {"F:/demo"}
    gui.current_items = []
    gui.runner = None
    gui.log_output = DummyLog()

    gui._execute_conversion()

    assert popup_messages
    assert "не найдено ни одного проекта" in popup_messages[0]
    assert gui.runner is None

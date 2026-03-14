#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Главное окно GUI приложения.
"""

from __future__ import annotations

import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from .project_scanner import GroupDict, ProjectDict, TreeIndex, TreeItem

from .sg_import import sg
from ..core.convert import load_env_file
from .constants import COLORS, PARAMS_DEPEND_FILE, PARAMS_DESC_FILE, PROJECTS_DIR, SCRIPT_DIR, VERSION
from .conversion_runner import ConversionRunner
from .project_editor import ProjectEditorDialog
from .project_scanner import GROUP_ICON, MAX_GROUP_DEPTH, ITEM_TYPE_GROUP, ITEM_TYPE_PROJECT, ProjectScanner


class CyberpunkGUI:
    """Главный класс графического интерфейса."""

    def __init__(self) -> None:
        self.project_tree: "TreeIndex" = {}
        self.current_group_path: Path | None = None
        self.current_items: "list[TreeItem]" = []
        self.selected_paths: set[str] = set()
        self.selected_row: int | None = None
        self.runner: ConversionRunner | None = None
        self.conversion_thread: threading.Thread | None = None
        self.params_descriptions: dict[str, dict[str, str]] | None = self._load_params_descriptions()
        self.params_depend: dict[str, dict[str, list[str]]] | None = self._load_params_depend()
        self.debug_mode = False

        self._setup_theme()
        self.scan_projects()

        icon_path = SCRIPT_DIR / "docs" / "images" / "icons8-cyberpunk-gradient-16.ico"
        self.window = sg.Window(  # type: ignore[attr-defined, assignment]
            f"1C-Convert-Kit - Cyberpunk Edition | Версия {VERSION}",
            self.create_layout(),
            size=(1600, 860),
            finalize=True,
            resizable=True,
            background_color=COLORS["bg"],
            return_keyboard_events=True,
            icon=str(icon_path) if icon_path.exists() else None,
        )

        self.table = self.window["-TABLE-"]  # type: ignore[index]
        self.details_table = self.window["-DETAILS_TABLE-"]  # type: ignore[index]
        self.log_output = self.window["-LOG-"]  # type: ignore[index]
        assert self.table is not None
        assert self.details_table is not None
        assert self.log_output is not None

        self._bind_double_click()
        self.update_table()

    def _load_params_descriptions(self) -> dict[str, dict[str, str]] | None:
        try:
            if PARAMS_DESC_FILE.exists():
                import json

                with open(PARAMS_DESC_FILE, "r", encoding="utf-8") as file:
                    return cast(dict[str, dict[str, str]], json.load(file))
        except Exception:
            pass
        return None

    def _load_params_depend(self) -> dict[str, dict[str, list[str]]] | None:
        try:
            if PARAMS_DEPEND_FILE.exists():
                import json

                with open(PARAMS_DEPEND_FILE, "r", encoding="utf-8") as file:
                    return cast(dict[str, dict[str, list[str]]], json.load(file))
        except Exception:
            pass
        return None

    def _setup_theme(self) -> None:
        _ = sg.theme("DarkBlack")  # type: ignore[attr-defined]

    def _bind_double_click(self) -> None:
        try:
            self.table.Widget.bind(  # type: ignore[attr-defined]
                "<Double-1>",
                lambda _event: self.window.write_event_value("-TABLE-DOUBLE-", None),  # type: ignore[attr-defined]
            )
        except Exception:
            pass

    def scan_projects(self) -> None:
        """Пересканирует дерево проектов и обновляет текущий уровень."""
        previous_group = self.current_group_path
        self.project_tree = ProjectScanner.build_tree()
        self.selected_paths &= {item["path"] for item in self.project_tree.values()}

        if previous_group is not None and ProjectScanner.get_item(self.project_tree, previous_group) is None:
            previous_group = previous_group.parent if previous_group.parent != PROJECTS_DIR else None

        self.current_group_path = previous_group if previous_group and previous_group != PROJECTS_DIR else None
        self.current_items = ProjectScanner.list_level(self.project_tree, self.current_group_path)
        if self.selected_row is not None and self.selected_row >= len(self.current_items):
            self.selected_row = None
        if hasattr(self, "log_output"):
            for warning in ProjectScanner.last_warnings:
                _ = self.log_output.print(f"⚠ {warning}\n", text_color=COLORS["warning"], end="")  # type: ignore[attr-defined, union-attr]

    def create_layout(self) -> "list[list[object]]":
        projects_tab = [
            [
                sg.Button("Добавить", key="-ADD_PROJECT-", button_color=(COLORS["bg"], COLORS["success"]), border_width=0, font=("Arial", 10, "bold")),
                sg.Button("Добавить группу", key="-ADD_GROUP-", button_color=(COLORS["bg"], COLORS["accent"]), border_width=0, font=("Arial", 10, "bold")),
                sg.Button("Изменить", key="-EDIT_PROJECT-", button_color=(COLORS["bg"], COLORS["primary"]), border_width=0, font=("Arial", 10, "bold")),
                sg.Button("Копировать", key="-COPY_PROJECT-", button_color=(COLORS["bg"], COLORS["accent"]), border_width=0, font=("Arial", 10, "bold")),
                sg.Button("Удалить", key="-DELETE_PROJECT-", button_color=(COLORS["bg"], COLORS["error"]), border_width=0, font=("Arial", 10, "bold")),
                sg.Button("Переместить в группу", key="-MOVE_TO_GROUP-", button_color=(COLORS["bg"], COLORS["warning"]), border_width=0, font=("Arial", 10, "bold")),
            ],
            [
                sg.Text("Текущий путь:", text_color=COLORS["primary"], background_color=COLORS["bg"], font=("Consolas", 10, "bold")),
                sg.Text("/projects", key="-CURRENT_PATH-", text_color=COLORS["text"], background_color=COLORS["bg"], font=("Consolas", 10)),
            ],
            [
                sg.Button("◀ К уровню выше", key="-GO_UP-", button_color=(COLORS["bg"], COLORS["primary"]), border_width=0, visible=False, font=("Arial", 10, "bold")),
            ],
            [
                sg.Table(
                    values=[],
                    headings=["✓", "Наименование", "Скрипт", "Путь выгрузки"],
                    key="-TABLE-",
                    enable_events=True,
                    select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                    auto_size_columns=False,
                    col_widths=[3, 42, 15, 88],
                    num_rows=12,
                    font=("Consolas", 13),
                    background_color=COLORS["bg_secondary"],
                    text_color=COLORS["primary"],
                    alternating_row_color=COLORS["bg"],
                    header_background_color=COLORS["bg"],
                    header_text_color=COLORS["primary"],
                    justification="left",
                    selected_row_colors=(COLORS["bg"], COLORS["accent"]),
                ),
                sg.Image(str(SCRIPT_DIR / "docs" / "images" / "icons8-cyberpunk-gradient-96.png"), background_color=COLORS["bg"]),
            ],
            [
                sg.Button("Выбрать все", key="-SELECT_ALL-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
                sg.Button("Снять все", key="-DESELECT_ALL-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
                sg.Button("Вверх ▲", key="-MOVE_UP-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
                sg.Button("Вниз ▼", key="-MOVE_DOWN-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
                sg.Button("Изменить путь...", key="-CHANGE_PATH-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
                sg.Button("Обновить проекты", key="-REFRESH-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
            ],
            [sg.HorizontalSeparator(color=COLORS["primary"])],
            [sg.Text("Детали проекта:", key="-DETAILS_LABEL-", text_color=COLORS["primary"], background_color=COLORS["bg"], font=("Consolas", 11, "bold"))],
            [
                sg.Table(
                    values=[],
                    headings=["", "Параметр", "Значение", "Описание"],
                    key="-DETAILS_TABLE-",
                    enable_events=False,
                    auto_size_columns=False,
                    col_widths=[3, 27, 60, 110],
                    num_rows=15,
                    font=("Consolas", 10),
                    background_color=COLORS["bg_secondary"],
                    text_color=COLORS["text"],
                    alternating_row_color=COLORS["bg"],
                    header_background_color=COLORS["bg"],
                    header_text_color=COLORS["accent"],
                    justification="left",
                )
            ],
        ]

        log_tab = [
            [
                sg.Multiline(
                    "",
                    key="-LOG-",
                    size=(160, 35),
                    font=("Consolas", 9),
                    background_color=COLORS["bg_secondary"],
                    text_color=COLORS["text"],
                    autoscroll=True,
                    disabled=False,
                    write_only=False,
                    no_scrollbar=False,
                    border_width=0,
                    reroute_stdout=False,
                    reroute_stderr=False,
                    reroute_cprint=False,
                    right_click_menu=["", ["Копировать", "Выделить все"]],
                )
            ],
            [
                sg.Button("Очистить лог", key="-CLEAR_LOG-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
                sg.Button("Сохранить лог", key="-SAVE_LOG-", button_color=(COLORS["text"], COLORS["bg_secondary"]), border_width=0),
            ],
        ]

        return [
            [
                sg.TabGroup(
                    [
                        [sg.Tab("Проекты", projects_tab, background_color=COLORS["bg"], border_width=0)],
                        [sg.Tab("Лог выполнения", log_tab, background_color=COLORS["bg"], border_width=0)],
                    ],
                    key="-TABS-",
                    background_color=COLORS["bg"],
                    tab_background_color=COLORS["bg_secondary"],
                    selected_background_color=COLORS["primary"],
                    selected_title_color=COLORS["bg"],
                    title_color=COLORS["text"],
                    border_width=0,
                )
            ],
            [sg.HorizontalSeparator(color=COLORS["primary"])],
            [sg.Text("Готов к запуску", key="-PROGRESS_TEXT-", text_color=COLORS["text"], background_color=COLORS["bg"], font=("Consolas", 10))],
            [sg.Text("Подготовлено к запуску: 0 проектов", key="-SELECTION_SUMMARY-", text_color=COLORS["primary"], background_color=COLORS["bg"], font=("Consolas", 10, "bold"))],
            [sg.ProgressBar(100, orientation="h", size=(140, 20), key="-PROGRESS_BAR-", bar_color=(COLORS["primary"], COLORS["bg_secondary"]))],
            [
                sg.Button("ВЫПОЛНИТЬ (F5)", key="-EXECUTE-", size=(20, 2), button_color=(COLORS["bg"], COLORS["primary"]), font=("Arial", 14, "bold"), border_width=0),
                sg.Checkbox("Отладка", key="-DEBUG-", default=False, enable_events=True, text_color=COLORS["text"], background_color=COLORS["bg"], font=("Consolas", 10)),
            ],
        ]

    def update_table(self) -> None:
        """Обновляет данные в таблице."""
        table_data: list[list[str]] = []
        for idx, item in enumerate(self.current_items):
            check = "✓" if item["path"] in self.selected_paths else ""
            marker = ">" if idx == self.selected_row else ""
            if item["item_type"] == ITEM_TYPE_GROUP:
                group = cast("GroupDict", item)
                name = f"{GROUP_ICON} {group['name']}"
                script = ""
                dst = f"Группа: {group['project_count']} проектов"
            else:
                project = cast("ProjectDict", item)
                name = project["name"]
                script = project["script"]
                dst = project["custom_dst_path"] or project["dst_path"]
            display_name = f"{marker} {name}" if marker else name
            table_data.append([check, display_name, script, dst])

        _ = self.table.update(values=table_data)  # type: ignore[attr-defined]
        _ = self.window["-CURRENT_PATH-"].update(value=self._get_current_path_label())  # type: ignore[index, attr-defined]
        _ = self.window["-GO_UP-"].update(visible=self.current_group_path is not None)  # type: ignore[index, attr-defined]
        _ = self.window["-SELECTION_SUMMARY-"].update(value=self._get_selection_summary())  # type: ignore[index, attr-defined]
        self.update_details_table()

    def _get_selection_summary(self) -> str:
        selected_items = self._get_selected_items()
        if not selected_items:
            return "Подготовлено к запуску: 0 проектов"
        selected_projects = ProjectScanner.flatten_projects(selected_items, self.project_tree)
        return f"Подготовлено к запуску: {len(selected_projects)} проектов"

    def _get_current_path_label(self) -> str:
        if self.current_group_path is None:
            return "/projects"
        relative = self.current_group_path.resolve().relative_to(PROJECTS_DIR.resolve())
        return f"/projects/{str(relative).replace(chr(92), '/')}"

    def _get_selected_item(self) -> "TreeItem | None":
        if self.selected_row is None or self.selected_row >= len(self.current_items):
            return None
        return self.current_items[self.selected_row]

    def _get_selected_project(self) -> "ProjectDict | None":
        item = self._get_selected_item()
        if item is None or item["item_type"] != ITEM_TYPE_PROJECT:
            return None
        return cast("ProjectDict", item)

    def _get_selected_group(self) -> "GroupDict | None":
        item = self._get_selected_item()
        if item is None or item["item_type"] != ITEM_TYPE_GROUP:
            return None
        return cast("GroupDict", item)

    def _get_selected_items(self) -> "list[TreeItem]":
        selected = [item for item in self.project_tree.values() if item["path"] in self.selected_paths]
        return ProjectScanner.sort_items(selected)

    def _select_path(self, item_path: str) -> None:
        if item_path in self.selected_paths:
            self.selected_paths.remove(item_path)
        else:
            self.selected_paths.add(item_path)

    def _reset_selection(self) -> None:
        self.selected_paths.clear()
        self.selected_row = None

    def _set_current_group(self, group_path: Path | None) -> None:
        self.current_group_path = None if group_path is None or group_path == PROJECTS_DIR else group_path
        self.current_items = ProjectScanner.list_level(self.project_tree, self.current_group_path)
        self._reset_selection()
        self.update_table()

    def _navigate_up(self) -> None:
        if self.current_group_path is None:
            return
        parent = self.current_group_path.parent
        self._set_current_group(None if parent == PROJECTS_DIR else parent)

    def _open_group(self, group: "GroupDict") -> None:
        self._set_current_group(Path(group["path"]))

    def _open_selected_group(self) -> None:
        group = self._get_selected_group()
        if group is not None:
            self._open_group(group)

    def _get_param_description(self, param_name: str, script_name: str) -> str:
        if not self.params_descriptions:
            return ""
        if script_name in self.params_descriptions and param_name in self.params_descriptions[script_name]:
            return self.params_descriptions[script_name][param_name]
        script_key_with_cmd = f"{script_name}.cmd"
        if script_key_with_cmd in self.params_descriptions and param_name in self.params_descriptions[script_key_with_cmd]:
            return self.params_descriptions[script_key_with_cmd][param_name]
        if "common" in self.params_descriptions and param_name in self.params_descriptions["common"]:
            return self.params_descriptions["common"][param_name]
        return ""

    def _get_param_category(self, param_name: str, script_name: str) -> str:
        if not self.params_descriptions:
            return "not_described"
        clean_param_name = param_name.split(" (")[0].strip()
        if "common" in self.params_descriptions and clean_param_name in self.params_descriptions["common"]:
            return "common"
        if script_name in self.params_descriptions and clean_param_name in self.params_descriptions[script_name]:
            return "special"
        script_key_with_cmd = f"{script_name}.cmd"
        if script_key_with_cmd in self.params_descriptions and clean_param_name in self.params_descriptions[script_key_with_cmd]:
            return "special"
        return "not_described"

    def _get_category_marker(self, category: str) -> str:
        if category == "special":
            return "S"
        if category == "not_described":
            return "N"
        return ""

    def update_details_table(self) -> None:
        item = self._get_selected_item()
        if item is None:
            _ = self.window["-DETAILS_LABEL-"].update(value="Детали проекта:")  # type: ignore[index, attr-defined]
            _ = self.details_table.update(values=[])  # type: ignore[attr-defined]
            return

        if item["item_type"] == ITEM_TYPE_GROUP:
            group = cast("GroupDict", item)
            _ = self.window["-DETAILS_LABEL-"].update(value="Детали группы:")  # type: ignore[index, attr-defined]
            child_groups, child_projects = ProjectScanner.count_direct_children(group, self.project_tree)
            details_data: list[list[str]] = [
                ["", "Имя", group["name"], ""],
                ["", "Путь", self._get_current_item_display_path(group), ""],
                ["", "Вложенных подгрупп", str(len(child_groups)), ""],
            ]
            if child_groups:
                for subgroup in child_groups:
                    details_data.append(["", "Подгруппа", subgroup["name"], ""])
            else:
                details_data.append(["", "Подгруппа", "отсутствуют", ""])
            details_data.append(["", "Вложенных проектов", str(group["project_count"]), ""])
            if child_projects:
                for project in child_projects:
                    details_data.append(["", "Проект", project["name"], project["script"]])
            else:
                details_data.append(["", "Проект", "отсутствуют", ""])
            _ = self.details_table.update(values=details_data)  # type: ignore[attr-defined]
            return

        _ = self.window["-DETAILS_LABEL-"].update(value="Детали проекта:")  # type: ignore[index, attr-defined]
        project = cast("ProjectDict", item)
        project_env_path = project["env_path"]
        script_name = project.get("script", "")
        details_data: list[list[str]] = []

        try:
            env_files = []
            base_env_name = None
            base_env_files = [file for file in PROJECTS_DIR.glob("*.env") if file.is_file()]
            if base_env_files:
                base_env_path = base_env_files[0]
                env_files.append(str(base_env_path))
                base_env_name = base_env_path.name

            env_files.append(project_env_path)
            base_params: dict[str, str] = {}
            project_params: dict[str, str] = {}

            for env_file in env_files:
                env_vars = load_env_file(env_file, silent=True)
                if env_vars:
                    source_name = Path(env_file).name
                    if source_name == base_env_name:
                        base_params = env_vars.copy()
                    else:
                        project_params = env_vars.copy()

            if "ScriptName" in project_params:
                value = project_params["ScriptName"]
                if "ScriptName" in base_params and base_params["ScriptName"] != value:
                    value = f"{value} (в {base_env_name} = {base_params['ScriptName']})"
                description = self._get_param_description("ScriptName", script_name)
                marker = self._get_category_marker(self._get_param_category("ScriptName", script_name))
                details_data.append([marker, "ScriptName", value, description])

            for param, value in sorted(project_params.items()):
                if param == "ScriptName":
                    continue
                if param in base_params and base_params[param] != value:
                    value = f"{value} (в {base_env_name} = {base_params[param]})"
                description = self._get_param_description(param, script_name)
                marker = self._get_category_marker(self._get_param_category(param, script_name))
                details_data.append([marker, param, value, description])

            if base_env_name:
                for param, value in sorted(base_params.items()):
                    if param in project_params:
                        continue
                    description = self._get_param_description(param, script_name)
                    marker = self._get_category_marker(self._get_param_category(param, script_name))
                    details_data.append([marker, f"{param} ({base_env_name})", value, description])
        except Exception as error:
            details_data.append(["", "Ошибка", f"Не удалось прочитать файлы: {error}", ""])

        _ = self.details_table.update(values=details_data)  # type: ignore[attr-defined]

    def _get_current_item_display_path(self, item: "TreeItem") -> str:
        try:
            relative = Path(item["path"]).resolve().relative_to(PROJECTS_DIR.resolve())
            return f"/projects/{str(relative).replace(chr(92), '/')}"
        except ValueError:
            return item["path"]

    def handle_events(self) -> None:
        while True:
            event, values = self.window.read()  # type: ignore[attr-defined, misc, union-attr]
            if event == sg.WIN_CLOSED:  # type: ignore[attr-defined]
                break
            if event == "F5:116":
                self._execute_conversion()
            elif event == "-DEBUG-":
                self.debug_mode = bool(values["-DEBUG-"])  # type: ignore[index]
                status = "включен" if self.debug_mode else "выключен"
                _ = self.log_output.print(f"ℹ Режим отладки {status}\n", text_color=COLORS["primary"], end="")  # type: ignore[attr-defined, union-attr]
            elif event == "-TABLE-":
                self._handle_table_click(values)
            elif event == "-TABLE-DOUBLE-":
                self._open_selected_group()
            elif event == "-GO_UP-":
                self._navigate_up()
            elif event == "-ADD_GROUP-":
                self._add_group()
            elif event == "-MOVE_TO_GROUP-":
                self._move_to_group()
            elif event == "-ADD_PROJECT-":
                self._add_project()
            elif event == "-EDIT_PROJECT-":
                self._edit_project()
            elif event == "-COPY_PROJECT-":
                self._copy_project()
            elif event == "-DELETE_PROJECT-":
                self._delete_item()
            elif event == "-SELECT_ALL-":
                self.selected_paths.update(item["path"] for item in self.current_items)
                self.update_table()
            elif event == "-DESELECT_ALL-":
                for item in self.current_items:
                    self.selected_paths.discard(item["path"])
                self.update_table()
            elif event == "-MOVE_UP-":
                self._move_row(-1)
            elif event == "-MOVE_DOWN-":
                self._move_row(1)
            elif event == "-CHANGE_PATH-":
                self._change_path()
            elif event == "-REFRESH-":
                self.scan_projects()
                self._reset_selection()
                self.update_table()
                _ = self.log_output.print("✓ Проекты обновлены\n", text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
            elif event == "-EXECUTE-":
                self._execute_conversion()
            elif event == "-CLEAR_LOG-" or event == "Очистить":
                _ = self.log_output.update(value="")  # type: ignore[attr-defined]
            elif event == "-SAVE_LOG-":
                self._save_log()
            elif event == "Копировать":
                self._copy_log_text()
            elif event == "Выделить все":
                self._select_all_log_text()
            elif event == "-UPDATE_STATUS-":
                completed, total, percent, status = values[event]  # type: ignore[misc]
                _ = self.window["-PROGRESS_TEXT-"].update(value=f"Выполнено: {completed} из {total} проектов ({percent}%)")  # type: ignore[index, attr-defined]
                _ = self.window["-PROGRESS_BAR-"].update(current_count=percent)  # type: ignore[index, attr-defined]
                _ = self.log_output.print(f"ℹ {status}\n", text_color=COLORS["primary"], end="")  # type: ignore[attr-defined, union-attr]
            elif event == "-CONVERSION_DONE-":
                completed, total, percent, total_duration_str = values[event]  # type: ignore[misc]
                _ = self.window["-PROGRESS_TEXT-"].update(value=f"Готово! Выполнено: {completed} из {total} ({percent}%). Общее время: {total_duration_str}")  # type: ignore[index, attr-defined]
                _ = self.window["-PROGRESS_BAR-"].update(current_count=100)  # type: ignore[index, attr-defined]
            elif event == "-LOG-":
                log_data = values[event]  # type: ignore[index]
                if isinstance(log_data, dict):
                    _ = self.log_output.print(log_data["text"], text_color=log_data["color"], end="")  # type: ignore[attr-defined, union-attr]
                else:
                    _ = self.log_output.update(value=log_data, append=True)  # type: ignore[attr-defined]

        if self.runner:
            self.runner.stop()
        _ = self.window.close()  # type: ignore[attr-defined]

    def _handle_table_click(self, values: object) -> None:
        if not isinstance(values, dict) or "-TABLE-" not in values or not values["-TABLE-"]:
            return
        clicked_row = values["-TABLE-"][0]  # type: ignore[index]
        if clicked_row >= len(self.current_items):
            return
        self.selected_row = clicked_row
        self._select_path(self.current_items[clicked_row]["path"])
        self.update_table()

    def _copy_log_text(self) -> None:
        try:
            selected_text = self.log_output.Widget.selection_get()  # type: ignore[attr-defined, union-attr]
            if selected_text:
                _ = self.window.TKroot.clipboard_clear()  # type: ignore[attr-defined, union-attr]
                _ = self.window.TKroot.clipboard_append(selected_text)  # type: ignore[attr-defined, union-attr]
                return
        except Exception:
            pass
        try:
            all_text = self.log_output.get()  # type: ignore[attr-defined, union-attr]
            if all_text:
                _ = self.window.TKroot.clipboard_clear()  # type: ignore[attr-defined, union-attr]
                _ = self.window.TKroot.clipboard_append(all_text)  # type: ignore[attr-defined, union-attr]
        except Exception:
            pass

    def _select_all_log_text(self) -> None:
        try:
            self.log_output.Widget.tag_add("sel", "1.0", "end")  # type: ignore[attr-defined]
        except Exception:
            pass

    def _move_row(self, direction: int) -> None:
        if self.selected_row is None:
            _ = sg.popup("Выберите элемент в таблице", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return
        new_idx = self.selected_row + direction
        if 0 <= new_idx < len(self.current_items):
            self.selected_row = new_idx
            self.update_table()

    def _change_path(self) -> None:
        project = self._get_selected_project()
        if project is None:
            _ = sg.popup("Выберите проект в таблице", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return

        script_lower = project["script"].lower()
        if "2cf" in script_lower or "2cfe" in script_lower:
            new_path = sg.popup_get_file(  # type: ignore[attr-defined]
                "Выберите файл для сохранения",
                save_as=True,
                file_types=(("CF Files", "*.cf"), ("CFE Files", "*.cfe"), ("All Files", "*.*")),
                background_color=COLORS["bg"],
                text_color=COLORS["text"],
            )
        else:
            new_path = sg.popup_get_folder(  # type: ignore[attr-defined]
                "Выберите папку для сохранения",
                background_color=COLORS["bg"],
                text_color=COLORS["text"],
            )

        if new_path:
            project["custom_dst_path"] = new_path
            tree_item = self.project_tree.get(project["relative_path"])
            if tree_item is not None and tree_item["item_type"] == ITEM_TYPE_PROJECT:
                cast("ProjectDict", tree_item)["custom_dst_path"] = new_path
            self.update_table()
            _ = self.log_output.print(f'ℹ Путь выгрузки изменен для проекта "{project["name"]}"\n', text_color=COLORS["primary"], end="")  # type: ignore[attr-defined, union-attr]

    def _execute_conversion(self) -> None:
        selected_items = self._get_selected_items()
        if not selected_items:
            _ = sg.popup("Выберите хотя бы один проект или группу", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return

        selected_projects = ProjectScanner.flatten_projects(selected_items, self.project_tree)
        if not selected_projects:
            _ = sg.popup(
                "Среди выбранных элементов не найдено ни одного проекта для выполнения.",
                background_color=COLORS["bg"],
                text_color=COLORS["warning"],
            )  # type: ignore[attr-defined]
            return

        _ = self.window["-TABS-"].Widget.select(1)  # type: ignore[index, attr-defined, union-attr]
        _ = self.log_output.update(value="")  # type: ignore[attr-defined]
        for item in selected_items:
            if item["item_type"] == ITEM_TYPE_GROUP:
                _ = self.log_output.print(f'ℹ Выбрана группа "{item["name"]}"\n', text_color=COLORS["primary"], end="")  # type: ignore[attr-defined, union-attr]
        _ = self.log_output.print(f"ℹ Найдено {len(selected_projects)} проекта(ов) для выполнения\n", text_color=COLORS["primary"], end="")  # type: ignore[attr-defined, union-attr]
        _ = self.window["-PROGRESS_BAR-"].update(current_count=0)  # type: ignore[index, attr-defined]
        _ = self.window["-PROGRESS_TEXT-"].update(value="Запуск конвертации...")  # type: ignore[index, attr-defined]

        self.runner = ConversionRunner(self.window)
        self.conversion_thread = threading.Thread(target=self.runner.run_conversions, args=(selected_projects,), daemon=True)
        self.conversion_thread.start()

    def _get_current_container(self) -> Path:
        return self.current_group_path or PROJECTS_DIR

    def _select_item_by_path(self, item_path: Path) -> None:
        self.current_items = ProjectScanner.list_level(self.project_tree, self.current_group_path)
        self.selected_paths = {str(item_path.resolve())}
        self.selected_row = None
        resolved_path = str(item_path.resolve())
        for idx, item in enumerate(self.current_items):
            if item["path"] == resolved_path:
                self.selected_row = idx
                break

    def _get_existing_names_current_level(self, exclude_path: str | None = None) -> list[str]:
        names: list[str] = []
        for item in self.current_items:
            if exclude_path and item["path"] == exclude_path:
                continue
            names.append(item["name"])
        return names

    def _create_project_pipeline(
        self,
        project_name: str,
        script_name: str,
        params: dict[str, str],
        success_message: str,
        target_dir: Path | None = None,
    ) -> bool:
        project_root = target_dir or self._get_current_container()
        project_folder = project_root / project_name
        try:
            project_folder.mkdir(parents=True, exist_ok=False)
            env_filename = f"{self._sanitize_filename(project_name)}_{script_name}.env"
            env_path = project_folder / env_filename
            self._save_env_file(env_path, params)
            self.scan_projects()
            self._select_item_by_path(project_folder)
            self.update_table()
            _ = self.log_output.print(f"✓ {success_message}\n", text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
            return True
        except Exception as error:
            _ = sg.popup_error(f"Ошибка создания проекта: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]
            return False

    def _add_project(self) -> None:
        dialog = ProjectEditorDialog(
            self.params_descriptions,
            params_depend=self.params_depend,
            mode="add",
            existing_projects=self._get_existing_names_current_level(),
            current_group_path=self._get_current_path_label(),
        )
        result = dialog.show()
        if result:
            project_name = str(result["name"])
            script_name = str(result["script"])
            params = result["params"]
            if isinstance(params, dict) and all(isinstance(key, str) and isinstance(value, str) for key, value in params.items()):
                self._create_project_pipeline(project_name, script_name, params, f'Проект "{project_name}" успешно создан')

    def _edit_project(self) -> None:
        project = self._get_selected_project()
        if project is None:
            group = self._get_selected_group()
            if group is not None:
                self._rename_group(group)
                return
            _ = sg.popup("Выберите проект или группу для изменения", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return

        dialog = ProjectEditorDialog(
            self.params_descriptions,
            params_depend=self.params_depend,
            mode="edit",
            project_data=project,
            existing_projects=self._get_existing_names_current_level(exclude_path=project["path"]),
            current_group_path=self._get_current_path_label(),
        )
        result = dialog.show()
        if not result:
            return

        try:
            original_folder = Path(project["path"])
            new_name = str(result["name"])
            new_script = str(result["script"])
            new_folder = original_folder.parent / new_name
            if original_folder != new_folder:
                _ = original_folder.rename(new_folder)
            for old_env in new_folder.glob("*.env"):
                old_env.unlink()
            params = result["params"]
            if isinstance(params, dict) and all(isinstance(key, str) and isinstance(value, str) for key, value in params.items()):
                env_filename = f"{self._sanitize_filename(new_name)}_{new_script}.env"
                self._save_env_file(new_folder / env_filename, params)
            self.scan_projects()
            self._select_item_by_path(new_folder)
            self.update_table()
            _ = self.log_output.print(f'✓ Проект "{new_name}" успешно изменен\n', text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
        except Exception as error:
            _ = sg.popup_error(f"Ошибка изменения проекта: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]

    def _copy_project(self) -> None:
        project = self._get_selected_project()
        if project is None:
            _ = sg.popup("Выберите проект для копирования", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return

        dialog = ProjectEditorDialog(
            self.params_descriptions,
            params_depend=self.params_depend,
            mode="copy",
            project_data=project,
            existing_projects=self._get_existing_names_current_level(),
            current_group_path=self._get_current_path_label(),
        )
        result = dialog.show()
        if result:
            project_name = str(result["name"])
            script_name = str(result["script"])
            params = result["params"]
            if isinstance(params, dict) and all(isinstance(key, str) and isinstance(value, str) for key, value in params.items()):
                self._create_project_pipeline(project_name, script_name, params, f'Проект "{project_name}" успешно скопирован')

    def _delete_item(self) -> None:
        item = self._get_selected_item()
        if item is None:
            _ = sg.popup("Выберите проект или группу для удаления", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return

        if item["item_type"] == ITEM_TYPE_GROUP:
            group = cast("GroupDict", item)
            response = sg.popup_yes_no(  # type: ignore[attr-defined]
                f'Удалить группу "{group["name"]}" со всем содержимым?\nВложенных проектов: {group["project_count"]}',
                title="Подтверждение удаления группы",
                background_color=COLORS["bg"],
                text_color=COLORS["warning"],
            )
        else:
            response = sg.popup_yes_no(  # type: ignore[attr-defined]
                f'Вы уверены, что хотите удалить проект "{item["name"]}"?',
                title="Подтверждение удаления",
                background_color=COLORS["bg"],
                text_color=COLORS["warning"],
            )

        if response != "Yes":
            return

        try:
            shutil.rmtree(Path(item["path"]))
            self.scan_projects()
            self._reset_selection()
            self.update_table()
            label = "Группа" if item["item_type"] == ITEM_TYPE_GROUP else "Проект"
            _ = self.log_output.print(f'✓ {label} "{item["name"]}" успешно удален(а)\n', text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
        except Exception as error:
            _ = sg.popup_error(f"Ошибка удаления: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]

    def _add_group(self) -> None:
        current_dir = self._get_current_container()
        name = self._prompt_group_name("Добавить группу", "", self._get_current_path_label())
        if not name:
            return
        try:
            ProjectScanner.validate_group_name(name, set(self._get_existing_names_current_level()))
            new_group_path = current_dir / name.strip()
            if ProjectScanner.compute_depth(new_group_path) > MAX_GROUP_DEPTH:
                raise ValueError(f"Нельзя превысить глубину вложенности {MAX_GROUP_DEPTH}")
            new_group_path.mkdir(parents=True, exist_ok=False)
            self.scan_projects()
            self._select_item_by_path(new_group_path)
            self.update_table()
            _ = self.log_output.print(f'✓ Группа "{name.strip()}" успешно создана\n', text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
        except Exception as error:
            _ = sg.popup_error(f"Ошибка создания группы: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]

    def _rename_group(self, group: "GroupDict") -> None:
        current_dir = Path(group["path"]).parent
        new_name = self._prompt_group_name("Переименовать группу", group["name"], self._get_current_item_display_path(group))
        if not new_name:
            return
        try:
            ProjectScanner.validate_group_name(
                new_name,
                set(self._get_existing_names_current_level(exclude_path=group["path"])),
            )
            new_group_path = current_dir / new_name.strip()
            if new_group_path.exists():
                raise ValueError(f"Элемент с именем '{new_name.strip()}' уже существует")
            Path(group["path"]).rename(new_group_path)
            self.scan_projects()
            if self.current_group_path is not None and Path(group["path"]).resolve() == self.current_group_path.resolve():
                self.current_group_path = new_group_path
                self.current_items = ProjectScanner.list_level(self.project_tree, self.current_group_path)
            self._select_item_by_path(new_group_path)
            self.update_table()
            _ = self.log_output.print(f'✓ Группа "{group["name"]}" переименована в "{new_name.strip()}"\n', text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
        except Exception as error:
            _ = sg.popup_error(f"Ошибка переименования группы: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]

    def _move_to_group(self) -> None:
        selected_items = self._get_selected_items()
        if not selected_items:
            _ = sg.popup("Выберите хотя бы один проект или группу", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
            return

        target = self._select_move_target(selected_items)
        if target is None:
            return

        warning = sg.popup_yes_no(  # type: ignore[attr-defined]
            "Относительные пути в .env после перемещения не пересчитываются автоматически.\nПродолжить?",
            title="Подтверждение перемещения",
            background_color=COLORS["bg"],
            text_color=COLORS["warning"],
        )
        if warning != "Yes":
            return

        try:
            ProjectScanner.validate_move_target([Path(item["path"]) for item in selected_items], target, self.project_tree)
            for item in selected_items:
                shutil.move(item["path"], str(target / Path(item["path"]).name))
            self.scan_projects()
            self._reset_selection()
            self.update_table()
            _ = self.log_output.print("✓ Элементы успешно перемещены\n", text_color=COLORS["success"], end="")  # type: ignore[attr-defined, union-attr]
        except Exception as error:
            self.scan_projects()
            self.update_table()
            _ = sg.popup_error(f"Ошибка перемещения: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]

    def _select_move_target(self, selected_items: "list[TreeItem]") -> Path | None:
        tree_data = sg.TreeData()  # type: ignore[attr-defined]
        root_key = str(PROJECTS_DIR.resolve())
        tree_data.Insert("", root_key, "/projects", values=["root"])

        selected_paths = {item["path"] for item in selected_items}
        for group in ProjectScanner.get_groups(self.project_tree):
            if group["path"] in selected_paths:
                continue
            parent_relative = str(Path(group["relative_path"]).parent).replace("\\", "/")
            parent_key = root_key if parent_relative in ("", ".") else str((PROJECTS_DIR / parent_relative).resolve())
            tree_data.Insert(parent_key, group["path"], group["name"], values=["group"])

        layout = [
            [sg.Text(f"Выбрано элементов: {len(selected_items)}", text_color=COLORS["text"], background_color=COLORS["bg"])],
            [sg.Multiline("\n".join(item["name"] for item in selected_items), size=(50, 4), disabled=True, background_color=COLORS["bg_secondary"], text_color=COLORS["text"])],
            [
                sg.Tree(
                    data=tree_data,
                    headings=["Тип"],
                    auto_size_columns=True,
                    num_rows=10,
                    col0_width=35,
                    key="-MOVE_TREE-",
                    show_expanded=True,
                    enable_events=True,
                    background_color=COLORS["bg_secondary"],
                    text_color=COLORS["text"],
                    header_background_color=COLORS["bg"],
                    header_text_color=COLORS["primary"],
                )
            ],
            [sg.Button("Переместить", key="-OK-"), sg.Button("Отмена", key="-CANCEL-")],
        ]
        window = sg.Window("Переместить в группу", layout, modal=True, finalize=True, background_color=COLORS["bg"])  # type: ignore[attr-defined]
        chosen: Path | None = None
        while True:
            event, values = window.read()  # type: ignore[attr-defined]
            if event in (sg.WIN_CLOSED, "-CANCEL-"):  # type: ignore[attr-defined]
                chosen = None
                break
            if event == "-OK-":
                selected_keys = values.get("-MOVE_TREE-", [])
                if not selected_keys:
                    _ = sg.popup("Выберите группу назначения или корень projects", background_color=COLORS["bg"], text_color=COLORS["warning"])  # type: ignore[attr-defined]
                    continue
                chosen = Path(selected_keys[0])
                break
        _ = window.close()  # type: ignore[attr-defined]
        return chosen

    def _prompt_group_name(self, title: str, default_name: str, current_path: str) -> str | None:
        layout = [
            [sg.Text("Текущая папка:", text_color=COLORS["primary"], background_color=COLORS["bg"]), sg.Text(current_path, text_color=COLORS["text"], background_color=COLORS["bg"])],
            [sg.Text("Имя группы:", text_color=COLORS["text"], background_color=COLORS["bg"]), sg.Input(default_name, key="-GROUP_NAME-", size=(40, 1), background_color=COLORS["bg_secondary"], text_color=COLORS["text"])],
            [sg.Button("Сохранить", key="-OK-"), sg.Button("Отмена", key="-CANCEL-")],
        ]
        window = sg.Window(title, layout, modal=True, finalize=True, background_color=COLORS["bg"])  # type: ignore[attr-defined]
        try:
            input_element = window["-GROUP_NAME-"]  # type: ignore[index]
            if hasattr(input_element, "set_focus"):
                _ = input_element.set_focus()  # type: ignore[attr-defined]
            if hasattr(input_element, "Widget"):
                _ = input_element.Widget.focus_set()  # type: ignore[attr-defined]
                _ = input_element.Widget.icursor("end")  # type: ignore[attr-defined]
                _ = input_element.Widget.select_range(0, "end")  # type: ignore[attr-defined]
        except Exception:
            pass

        result: str | None = None
        while True:
            event, values = window.read()  # type: ignore[attr-defined]
            if event in (sg.WIN_CLOSED, "-CANCEL-"):  # type: ignore[attr-defined]
                result = None
                break
            if event == "-OK-":
                value = str(values.get("-GROUP_NAME-", "")).strip()
                result = value or None
                break
        _ = window.close()  # type: ignore[attr-defined]
        return result

    def _save_env_file(self, env_path: Path, params: dict[str, str]) -> None:
        with open(env_path, "w", encoding="utf-8") as file:
            if "ScriptName" in params:
                _ = file.write(f'ScriptName={params["ScriptName"]}\n')
            for key in sorted(params.keys()):
                if key == "ScriptName":
                    continue
                value = params[key]
                if " " in value:
                    value = f'"{value}"'
                _ = file.write(f"{key}={value}\n")

    def _sanitize_filename(self, name: str) -> str:
        return name.replace(" ", "_")

    def _save_log(self) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"converter_log_{timestamp}.log"
        logs_dir = SCRIPT_DIR / "logs"
        default_path = str(logs_dir / default_name)
        file_path = sg.popup_get_file(  # type: ignore[attr-defined]
            "Сохранить лог",
            save_as=True,
            default_extension=".log",
            file_types=(("Log Files", "*.log"), ("All Files", "*.*")),
            default_path=default_path,
            background_color=COLORS["bg"],
            text_color=COLORS["text"],
        )
        if file_path:
            try:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as file:
                    _ = file.write(self.log_output.get())  # type: ignore[attr-defined]
                _ = sg.popup(f"Лог сохранен: {file_path}", background_color=COLORS["bg"], text_color=COLORS["success"])  # type: ignore[attr-defined]
            except Exception as error:
                _ = sg.popup(f"Ошибка сохранения: {error}", background_color=COLORS["bg"], text_color=COLORS["error"])  # type: ignore[attr-defined]

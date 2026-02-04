#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Сканирование и загрузка информации о проектах
"""

from __future__ import annotations

import sys
from typing import TypedDict
from pathlib import Path

# Добавляем корневую директорию проекта в sys.path для корректных импортов
_SCRIPT_DIR = Path(__file__).parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from core.convert import load_env_file  # type: ignore
from .constants import PROJECTS_DIR


class ProjectDict(TypedDict):
    """Структура данных проекта"""
    name: str
    script: str
    env_path: str
    dst_path: str
    custom_dst_path: str | None
    selected: bool


class ProjectScanner:
    """Сканирование и загрузка информации о проектах"""
    
    @staticmethod
    def scan_projects() -> list[ProjectDict]:
        """
        Сканирует папку projects и возвращает список проектов
        
        Returns:
            list: список словарей с информацией о проектах
        """
        projects: list[ProjectDict] = []
        
        if not PROJECTS_DIR.exists():
            return projects
        
        # Ищем все подпапки с .env файлами
        for item in PROJECTS_DIR.iterdir():
            if not item.is_dir():
                continue
            
            # Пропускаем служебные папки
            if item.name.startswith('.') or item.name.startswith('__'):
                continue
            
            # Ищем .env файлы в папке
            env_files = list(item.glob('*.env'))
            if not env_files:
                continue
            
            # Берем первый .env файл
            env_file = env_files[0]
            
            # Читаем ScriptName и V8_DST_PATH из .env
            script_name, dst_path = ProjectScanner._read_env_data(env_file)
            
            # Если ScriptName не указан, пропускаем проект
            if not script_name:
                continue
            
            # Создаем запись о проекте
            project: ProjectDict = {
                'name': item.name,
                'script': script_name,
                'env_path': str(env_file),
                'dst_path': dst_path,
                'custom_dst_path': None,
                'selected': False
            }
            
            projects.append(project)
        
        # Сортируем по имени
        projects.sort(key=lambda x: x['name'])  # type: ignore
        
        return projects
    
    @staticmethod
    def _read_env_data(env_file: Path) -> "tuple[str, str]":
        """
        Читает ScriptName и V8_DST_PATH из .env файла
        
        Использует общую функцию load_env_file из core.convert
        для единообразного парсинга с поддержкой BOM и различных кодировок.
        
        Args:
            env_file: путь к .env файлу
            
        Returns:
            tuple: (script_name, dst_path)
        """
        try:
            # Используем общую функцию парсинга с silent=True для GUI
            env_data = load_env_file(str(env_file), silent=True)
            
            if env_data is None:
                return '', ''
            
            script_name = env_data.get('ScriptName', '')
            dst_path = env_data.get('V8_DST_PATH', '')
            
            return script_name, dst_path
        except Exception:
            # Молча игнорируем ошибки в GUI
            return '', ''

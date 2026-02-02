#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Сканирование и загрузка информации о проектах
"""

from __future__ import annotations

from typing import TypedDict
from pathlib import Path

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
        
        Args:
            env_file: путь к .env файлу
            
        Returns:
            tuple: (script_name, dst_path)
        """
        script_name = ''
        dst_path = ''
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('ScriptName='):
                        value = line.split('=', 1)[1]
                        script_name = value.strip('"').strip("'")
                    elif line.startswith('V8_DST_PATH='):
                        value = line.split('=', 1)[1]
                        dst_path = value.strip('"').strip("'")
        except Exception:
            pass
        
        return script_name, dst_path

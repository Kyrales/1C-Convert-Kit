#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Вспомогательные функции для GUI
"""


def format_duration(seconds: float) -> str:
    """
    Форматирует длительность в читаемый вид
    
    Args:
        seconds: количество секунд
        
    Returns:
        str: отформатированная строка (например: "2 ч 15 мин 30 сек" или "45 сек")
    """
    if seconds < 60:
        return f"{int(seconds)} сек"
    
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    
    if minutes < 60:
        if secs > 0:
            return f"{minutes} мин {secs} сек"
        return f"{minutes} мин"
    
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    
    if mins > 0 and secs > 0:
        return f"{hours} ч {mins} мин {secs} сек"
    elif mins > 0:
        return f"{hours} ч {mins} мин"
    else:
        return f"{hours} ч"

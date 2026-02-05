#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Утилиты для работы со временем.
"""


def format_duration(seconds: float) -> str:
    """
    Форматирование длительности в читаемый вид.
    
    Args:
        seconds: Длительность в секундах
    
    Returns:
        Отформатированная строка (например: "1ч 23м 45с" или "45.2с")
    
    Examples:
        >>> format_duration(45.2)
        '45.2с'
        >>> format_duration(125)
        '2м 5с'
        >>> format_duration(3665)
        '1ч 1м 5с'
    """
    if seconds < 0:
        return "0с"
    
    if seconds < 60:
        return f"{seconds:.1f}с"
    
    minutes = int(seconds // 60)
    remaining_seconds = int(seconds % 60)
    
    if minutes < 60:
        return f"{minutes}м {remaining_seconds}с"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}ч {remaining_minutes}м {remaining_seconds}с"
    
    days = hours // 24
    remaining_hours = hours % 24
    
    return f"{days}д {remaining_hours}ч {remaining_minutes}м {remaining_seconds}с"

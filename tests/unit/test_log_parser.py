"""
Юнит-тесты для ToolOutputParser.

Проверяет корректность парсинга логов designer и определения ошибок.
"""
import pytest
from pathlib import Path
import tempfile
import sys

# Добавляем src в путь
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from converters.base.converter import ToolOutputParser


class TestToolOutputParser:
    """Тесты для ToolOutputParser."""
    
    def test_parse_warnings_about_help_links(self):
        """Предупреждения о неверных ссылках в справке не должны считаться ошибками."""
        log_content = """Файл - f:/temp/tmp_xml/Documents/Test/Ext/Help/ru.html: Возможно неверная ссылка e:\\Downloads\\image.png внутри справки.
Файл - f:/temp/tmp_xml/Catalogs/Test/Ext/Help/ru.html: Возможно неверная ссылка ../../mdpicture/id123/00000000-0000-0000-0000-000000000000 внутри справки.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_log = Path(f.name)
        
        try:
            errors, warnings = ToolOutputParser.parse_designer_log(temp_log)
            assert len(errors) == 0, f"Предупреждения о справке не должны считаться ошибками, найдено: {errors}"
        finally:
            temp_log.unlink()
    
    def test_parse_real_errors(self):
        """Реальные ошибки должны корректно определяться."""
        log_content = """Ошибка при загрузке конфигурации из файла
Не удалось выполнить операцию
Error: Failed to load configuration
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_log = Path(f.name)
        
        try:
            errors, warnings = ToolOutputParser.parse_designer_log(temp_log)
            assert len(errors) == 3, f"Должно быть найдено 3 ошибки, найдено: {len(errors)}"
            assert any('Ошибка' in e for e in errors), "Должна быть найдена ошибка на русском"
            assert any('Error' in e for e in errors), "Должна быть найдена ошибка на английском"
        finally:
            temp_log.unlink()
    
    def test_parse_success_messages(self):
        """Сообщения об успешном завершении не должны считаться ошибками."""
        log_content = """Операция успешно завершено
Конфигурация успешно выполнено
Successfully completed
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_log = Path(f.name)
        
        try:
            errors, warnings = ToolOutputParser.parse_designer_log(temp_log)
            assert len(errors) == 0, f"Сообщения об успехе не должны считаться ошибками, найдено: {errors}"
        finally:
            temp_log.unlink()
    
    def test_parse_mixed_content(self):
        """Смешанный контент: предупреждения, ошибки и успешные сообщения."""
        log_content = """Создание информационной базы
Файл - f:/temp/tmp_xml/Documents/Test/Ext/Help/ru.html: Возможно неверная ссылка image.png внутри справки.
Операция успешно завершено
Ошибка: Не найден файл конфигурации
Файл - f:/temp/tmp_xml/Catalogs/Test/Ext/Help/ru.html: Возможно неверная ссылка test.png внутри справки.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_log = Path(f.name)
        
        try:
            errors, warnings = ToolOutputParser.parse_designer_log(temp_log)
            # Должна быть найдена только одна реальная ошибка
            assert len(errors) == 1, f"Должна быть найдена 1 ошибка, найдено: {len(errors)}"
            assert 'Не найден файл' in errors[0], f"Должна быть найдена ошибка о файле, найдено: {errors}"
        finally:
            temp_log.unlink()
    
    def test_has_errors(self):
        """Проверка метода has_errors."""
        # Лог без ошибок
        log_content_no_errors = """Операция успешно завершено
Файл - f:/temp/tmp_xml/Test/Ext/Help/ru.html: Возможно неверная ссылка image.png внутри справки.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content_no_errors)
            temp_log = Path(f.name)
        
        try:
            assert not ToolOutputParser.has_errors(temp_log), "Не должно быть ошибок"
        finally:
            temp_log.unlink()
        
        # Лог с ошибками
        log_content_with_errors = """Ошибка при выполнении операции"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content_with_errors)
            temp_log = Path(f.name)
        
        try:
            assert ToolOutputParser.has_errors(temp_log), "Должны быть ошибки"
        finally:
            temp_log.unlink()
    
    def test_read_file_with_encoding(self):
        """Проверка чтения файлов с разными кодировками."""
        test_text = "Тестовый текст с кириллицей"
        
        # UTF-8
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(test_text)
            temp_log = Path(f.name)
        
        try:
            content = ToolOutputParser.read_file_with_encoding(temp_log)
            assert content is not None, "Должен быть прочитан UTF-8 файл"
            assert test_text in content, "Содержимое должно совпадать"
        finally:
            temp_log.unlink()
        
        # CP1251
        with tempfile.NamedTemporaryFile(mode='w', encoding='cp1251', delete=False, suffix='.log') as f:
            f.write(test_text)
            temp_log = Path(f.name)
        
        try:
            content = ToolOutputParser.read_file_with_encoding(temp_log)
            assert content is not None, "Должен быть прочитан CP1251 файл"
            assert test_text in content, "Содержимое должно совпадать"
        finally:
            temp_log.unlink()
    
    def test_parse_with_warnings(self):
        """Проверка метода parse_designer_log с разделением на ошибки и предупреждения."""
        log_content = """Файл - f:/temp/tmp_xml/Documents/Test/Ext/Help/ru.html: Возможно неверная ссылка image.png внутри справки.
Ошибка: Не найден файл конфигурации
Файл - f:/temp/tmp_xml/Catalogs/Test/Ext/Help/ru.html: Возможно неверная ссылка test.png внутри справки.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_log = Path(f.name)
        
        try:
            errors, warnings = ToolOutputParser.parse_designer_log(temp_log)
            # Должна быть найдена 1 ошибка и 2 предупреждения
            assert len(errors) == 1, f"Должна быть найдена 1 ошибка, найдено: {len(errors)}"
            assert len(warnings) == 2, f"Должно быть найдено 2 предупреждения, найдено: {len(warnings)}"
            assert 'Не найден файл' in errors[0], f"Должна быть найдена ошибка о файле, найдено: {errors}"
            assert all('возможно неверная ссылка' in w.lower() for w in warnings), "Все предупреждения должны быть о ссылках"
        finally:
            temp_log.unlink()
    
    def test_parse_with_warnings_and_logger(self):
        """Проверка вывода предупреждений через логгер."""
        from converters.base.converter import Logger
        
        log_content = """Файл - f:/temp/tmp_xml/Test/Ext/Help/ru.html: Возможно неверная ссылка image.png внутри справки.
"""
        
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.log') as f:
            f.write(log_content)
            temp_log = Path(f.name)
        
        try:
            # Создаем логгер (не silent, чтобы проверить вывод)
            logger = Logger(silent=False)
            errors, warnings = ToolOutputParser.parse_designer_log(temp_log, logger)
            
            assert len(errors) == 0, "Не должно быть ошибок"
            assert len(warnings) == 1, "Должно быть 1 предупреждение"
        finally:
            temp_log.unlink()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

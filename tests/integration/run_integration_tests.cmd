@echo off
chcp 65001 > nul
echo ========================================
echo Запуск интеграционных тестов конвертации
echo ========================================
echo.

REM Проверка наличия pytest
python -m pytest --version > nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] pytest не установлен
    echo Установите: pip install pytest
    pause
    exit /b 1
)

echo [INFO] Запуск интеграционных тестов...
echo.

REM Запуск тестов с подробным выводом
python -m pytest tests/integration/test_convert_integration.py -v -s

echo.
if errorlevel 1 (
    echo [ОШИБКА] Тесты завершились с ошибками
) else (
    echo [УСПЕХ] Все тесты пройдены успешно
)

pause

@echo off
chcp 65001 > nul
echo ================================================================================
echo Запуск тестов 1C Convert Kit
echo ================================================================================
echo.

cd /d "%~dp0.."

REM Проверка наличия pytest
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pytest не установлен!
    echo.
    echo Установите pytest командой:
    echo   pip install pytest
    echo.
    pause
    exit /b 1
)

echo [INFO] Запуск всех тестов...
echo.

REM Запуск тестов с подробным выводом
python -m pytest tests/ -v --tb=short --color=yes

echo.
echo ================================================================================
if errorlevel 1 (
    echo [ERROR] Некоторые тесты провалились
) else (
    echo [SUCCESS] Все тесты пройдены успешно!
)
echo ================================================================================
echo.

pause

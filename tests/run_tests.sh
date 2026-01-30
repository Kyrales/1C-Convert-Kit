#!/bin/bash

echo "================================================================================"
echo "Запуск тестов 1C Convert Kit"
echo "================================================================================"
echo ""

# Переходим в корень проекта
cd "$(dirname "$0")/.."

# Проверка наличия pytest
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "[ERROR] pytest не установлен!"
    echo ""
    echo "Установите pytest командой:"
    echo "  pip install pytest"
    echo ""
    exit 1
fi

echo "[INFO] Запуск всех тестов..."
echo ""

# Запуск тестов с подробным выводом
python -m pytest tests/ -v --tb=short --color=yes

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ $EXIT_CODE -ne 0 ]; then
    echo "[ERROR] Некоторые тесты провалились"
else
    echo "[SUCCESS] Все тесты пройдены успешно!"
fi
echo "================================================================================"
echo ""

exit $EXIT_CODE

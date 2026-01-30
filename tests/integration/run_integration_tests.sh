#!/bin/bash

echo "========================================"
echo "Запуск интеграционных тестов конвертации"
echo "========================================"
echo ""

# Проверка наличия pytest
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "[ОШИБКА] pytest не установлен"
    echo "Установите: pip install pytest"
    exit 1
fi

echo "[INFO] Запуск интеграционных тестов..."
echo ""

# Запуск тестов с подробным выводом
python -m pytest tests/integration/test_convert_integration.py -v -s

if [ $? -eq 0 ]; then
    echo ""
    echo "[УСПЕХ] Все тесты пройдены успешно"
else
    echo ""
    echo "[ОШИБКА] Тесты завершились с ошибками"
    exit 1
fi

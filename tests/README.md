# Тесты 1C Convert Kit

В каталоге `tests/` находятся unit- и интеграционные тесты, а также фикстуры для работы с реальными артефактами 1С.

## Структура

```text
tests/
├── unit/          # Быстрые тесты без внешних инструментов 1С
├── integration/   # Сценарии с 1cv8.exe, ibcmd.exe и 1cedtcli/ring
├── fixtures/      # EDT-, XML-, CF-, CFE- и EPF-фикстуры, тестовые .env
├── run_tests.cmd  # Запуск в Windows
└── run_tests.sh   # Запуск в Linux
```

Unit-тесты проверяют конвертеры, реестр, чтение `.env`, GUI-логику, группы проектов, очистку временных файлов и служебные функции. Часть GUI-тестов требует графическое окружение; подробности есть в [README_GUI_TESTS.md](unit/README_GUI_TESTS.md).

Интеграционные тесты запускают реальные конвертации. Для них нужны инструменты 1С и настроенный `tests/fixtures/base_test.env`. См. [руководство по интеграционным тестам](integration/README.md).

## Требования

Установите dev-зависимости:

```bash
pip install -r requirements-dev.txt
```

Для обычного запуска достаточно `pytest`. Для отчета о покрытии также нужен `pytest-cov`.

## Запуск

Все тесты:

```bash
pytest tests/
```

Только unit-тесты:

```bash
pytest tests/unit/
```

Только интеграционные тесты:

```bash
pytest tests/integration/
```

Конкретный файл или тест:

```bash
pytest tests/unit/test_env_file_loading.py -v
pytest tests/unit/test_env_file_loading.py::TestEnvFileLoading::test_load_cp1251_encoding -v
```

Подробный вывод и остановка после первой ошибки:

```bash
pytest tests/ -v -x
```

Запуск с отчетом о покрытии:

```bash
pytest tests/unit/ --cov=src --cov-report=html
```

## Новые тесты

- Файл с unit-тестами добавляйте в `tests/unit/` с префиксом `test_`.
- Интеграционные сценарии добавляйте в `tests/integration/`.
- Общие фикстуры храните в `tests/fixtures/`.
- Не запускайте разрушающие сценарии без явного флага. Например, тест DT-цикла требует `RUN_DESTRUCTIVE_1C_TESTS=1`.

## Полезные ссылки

- [Документация pytest](https://docs.pytest.org/)
- [Рекомендации pytest](https://docs.pytest.org/en/stable/explanation/goodpractices.html)

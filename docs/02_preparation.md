## Подготовка

Для начала подготовимся к работе с `github GraphQL API`. Во-первых, настроим наше
`python` окружение. Будем использовать [poetry](https://python-poetry.org/) и следующую начальную структуру
файлов

```
├── github_graphql_client/  <- Тут будет код нашего клиента
│   └── __init__.py
├── tests/                  <- Тут будут тесты
│   └── __init__.py
├── scripts/                <- Тут будут различные скрипты для запуска
├── pyproject.toml          <- Файл с настройками проекта
├── README.md
├── .env                    <- Тут будут всякие sensitive переменные
└── .gitignore
```

Конфиг `pyproject.toml` следующий

```toml
# `pyproject.toml` file
[tool.poetry]
name = "github_graphql_client"
version = "0.1.0"
description = "Github GraphQL client for Habr."
authors = ["FirstName SecondName <email>"]
readme = "README.md"
packages = [{include = "github_graphql_client"}]

[tool.poetry.dependencies]
python = "^3.11"


[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

Во-вторых, `Github GraphQL endpoint` находится по адресу `https://api.github.com/graphql`.
Чтобы воспользоваться `API` — нужно получить токен.
Подробности про выпуск токена описаны тут: [Github - Forming calls with GraphQL](https://docs.github.com/en/graphql/guides/forming-calls-with-graphql).
В файле `.env` перечислим следующие параметры

```dotenv
GITHUB_TOKEN=<YOUR_TOKEN>
GITHUB_GRAPHQL_ENDPOINT=https://api.github.com/graphql
```

Для работы с файлом `.env` будем использовать пакет [python-dotenv](https://pypi.org/project/python-dotenv/).
Добавим его в качестве нашей первой зависимости

```bash
$ poetry add  python-dotenv
Creating virtualenv blah-blah-py3.11 in /home/blah-blah/pypoetry/virtualenvs
Using version ^1.0.0 for python-dotenv

Updating dependencies
Resolving dependencies... (0.1s)

Package operations: 1 install, 0 updates, 0 removals

  • Installing python-dotenv (1.0.0)

Writing lock file
```

После выполнения команды `poetry add` появится файл `poetry.lock`, а так же наша зависимость
будет добавлена в `pyproject.toml`

```toml
# `pyproject.toml` file
# ...

[tool.poetry.dependencies]
python = "^3.11"
python-dotenv = "^1.0.0"

# ...
```

И, наконец, запустим `poetry install` для установки всех зависимостей.
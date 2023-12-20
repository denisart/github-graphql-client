## Первый запрос

Самое простое, что должен уметь наш клиент -- выполнять запросы.
[Обычно](https://graphql.org/learn/best-practices/) `GraphQL` работает через `HTTP/HTTPS` с некоторым `POST`,
который ожидает на входе `json` с полями `query: str` и `variables: dict[str, Any]`.
Именно так это работает в `github GraphQL API`. Схему `github GraphQL API`
можно посмотреть [тут](https://docs.github.com/en/graphql/overview/public-schema).

Для начала спроектируем класс, который будет отвечать непосредственно за соединение
с сервером и получение данных. Добавим несколько новых файлов

```bash
mkdir github_graphql_client/transport
touch github_graphql_client/transport/__init__.py github_graphql_client/transport/base.py
```

В файле `github_graphql_client/transport/base.py` определим класс `BaseTransport`

```python
# `github_graphql_client/transport/base.py` file
from typing import Any

class BaseTransport:
    """An abstract transport."""

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""
        raise NotImplementedError

    def connect(self) -> None:
        """Establish a session with the transport."""
        raise NotImplementedError

    def close(self) -> None:
        """Close a session."""
        raise NotImplementedError

```

Любой класс типа "Транспорт" далее будем реализовать наследуясь от `BaseTransport`.
Для этого необходимо будет реализовать три метода

- `connect` - метод, который открывает соединение с сервером;
- `close` - метод, который закрывает соединение с сервером;
- `execute` - метод, который получает на вход строку с `GraphQL` запросом и словарь `GraphQL` переменных, а на выходе возвращает ответ сервера;

Так, как `GraphQL` запрос есть по сути обычный `POST` запрос -- клиент
может быть реализован с помощью пакета [requests](https://pypi.org/project/requests/). Для начала добавим
зависимость

```bash
poetry add requests
```

В новый файл `github_graphql_client/transport/requests.py` добавим следующий код

```python
# `github_graphql_client/transport/requests.py` file
from typing import Any, Optional

import requests as r

from github_graphql_client.transport.base import BaseTransport

class RequestsTransport(BaseTransport):
    """The transport based on requests library."""

    session: Optional[r.Session]

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.token = token
        self.auth_header = {"Authorization": f"Bearer {self.token}"}

        self.session = None

    def connect(self) -> None:
        """Start a `requests.Session` connection."""
        if self.session is None:
            self.session = r.Session()
        else:
            raise Exception("Session already started")

    def close(self) -> None:
        """Closing `requests.Session` connection."""
        if self.session is not None:
            self.session.close()
            self.session = None

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""
        if self.session is None:
            raise Exception(f"RequestsTransport session not connected")

        post_args = {
            "headers": self.auth_header,
            "json": {"query": query, "variables": variables},
        }
        post_args["headers"]["Content-Type"] = "application/json"

        response = self.session.request("POST", self.endpoint, **post_args)

        result = response.json()
        return result.get("data")

```

В данном примере

- `connect` создает объект `requests.Session` (если он не был создан ранее);
- `close` закрывает соединение для объекта `requests.Session`;
- `execute` отправляет с помощью объекта `requests.Session` обычный `POST` запрос;

Давайте проверим, что с помощью этого класса уже можно получить данные. 
Отправим `query`, который вернет несколько завершенных `issues` 
из выбранного `github` репозитория. Для примера,
рассмотрим новый проект автора `pydantic` -- [FastUI](https://github.com/pydantic/FastUI).
Создадим для хранения запросов отдельную папку

```bash
mkdir github_graphql_client/queries
touch github_graphql_client/queries/__init__.py github_graphql_client/queries/repository.py
```

```python
# `github_graphql_client/queries/repository.py` file
repository_issues_query = """
query {
  repository(owner:"pydantic", name:"FastUI") {
    issues(last:2, states:CLOSED) {
      edges {
        node {
          title
          url
        }
      }
    }
  }
}
"""
```

Для удобства добавим скрипт `scripts/run.py`

```python
# `scripts/run.py` file
import os
import time
from typing import Any

from dotenv import load_dotenv

from github_graphql_client.client.requests_client import RequestsClient
from github_graphql_client.queries.repository import repository_issues_query

load_dotenv()  # take environment variables from .env

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GRAPHQL_ENDPOINT = os.environ.get("GITHUB_GRAPHQL_ENDPOINT")

def main():
    transport = RequestsTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )
    transport.connect()

    data = transport.execute(
        query=repository_issues_query, variables={},
    )
    print(data)
    
    transport.close()

if __name__ == "__main__":
    main()

```

После запуска скрипта мы получим примерно следующее

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
```

Мы получили несколько issues. Проект активно живет, так что вы должны получить другие issues :)

### Таймаут

Хорошо, если вы понимаете, сколько должен выполняться ваш запрос. Процитируем
одну хорошо известную [статью](https://habr.com/ru/companies/oleg-bunin/articles/433476/)

> Не ставить таймаут на задачу — это зло. Это значит, что вы не понимаете, что происходит
> в задаче, как должна работать бизнес-логика.

Добавим таймаут в `RequestsTransport`

```python
# `github_graphql_client/transport/requests.py` file
...

class RequestsTransport(BaseTransport):
    """The transport based on requests library."""

    DEFAULT_TIMEOUT: int = 1
    session: Optional[r.Session]

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        ...

        self.timeout = kwargs.get("timeout", RequestsTransport.DEFAULT_TIMEOUT)

    ...

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        ...

        post_args = {
            "headers": self.auth_header,
            "json": {"query": query, "variables": variables},
            "timeout": self.timeout,
        }
        ...

```

Проверим наш код указав очень маленький (для `github GraphQL API`) таймаут

```python
# `scripts/run.py` file
...

def main():
    transport = RequestsTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
        timeout=0.0001,
    )
    ...

...

```

Запустим `scripts/run.py`, мы получим следующее

```bash
$ python3 scripts/run.py
...
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='api.github.com', port=443): Max retries exceeded with url: /graphql (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x7f5510137d50>, 'Connection to api.github.com timed out. (connect timeout=0.0001)'))
```

По аналогии вы можете добавить свои настройки для `requests`, а мы пойдем дальше.

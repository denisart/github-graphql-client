## Первый запрос

Самое простое, что должен уметь наш клиент -- выполнять запросы. Создадим
для этого абстрактный класс. Добавим несколько новых файлов

```bash
mkdir github_graphql_client/client
touch github_graphql_client/client/__init__.py github_graphql_client/client/base.py
```

В файле `github_graphql_client/client/base.py` и определим наш абстрактный класс.

```python
# Файл `github_graphql_client/client/base.py`
from typing import Any, Protocol


class BaseGraphQLClientProtocol(Protocol):
    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        ...


class BaseGraphQLClient:
    """An abstract class for GraphQL client."""

    endpoint: str
    token: str

    def __init__(
        self, endpoint: str, token: str, *args: Any, **kwargs: Any
    ) -> None:
        self.endpoint = endpoint
        self.token = token

    def _get_header(self) -> dict[str, Any]:
        return {"Authorization": f"Bearer {self.token}"}

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        raise NotImplementedError

```

Далее любую реализацию клиента будем наследовать от `BaseGraphQLClient`.

Так, как `GraphQL` запрос есть по сути обычный `POST` запрос -- первый клиент
будет реализован с помощью пакета [requests](https://pypi.org/project/requests/). Для начала добавим
его в проект

```bash
poetry add requests
```

В новый файл `github_graphql_client/client/requests_client.py` добавим следующий код

```python
# Файл `github_graphql_client/client/requests_client.py`
from typing import Any

import requests as r

from .base import BaseGraphQLClient


class RequestsClient(BaseGraphQLClient):
    """GraphQL client based on `requests` library."""

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        response = r.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
        )
        response = response.json()
        return response["data"]

```

[Обычно](https://graphql.org/learn/best-practices/) `GraphQL` работает через `HTTP/HTTPS` с некоторым `POST`,
который ожидает на входе `json` с полями `query: str` и `variables: dict[str, Any]`.
Именно так это работает у `github GraphQL API`, именно это и реализовали выше.

Добавим `runner`, который будет запускать наши клиенты. Для этого создадим новый файл
`github_graphql_client/runner.py`.

```python
# Файл `github_graphql_client/runner.py`
import time
from typing import Any

from github_graphql_client.client.base import BaseGraphQLClientProtocol


def check_execute(fn):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration is {toc - tic:0.4f} seconds")
        return result

    return wrapper


class GraphQLClientRunner:
    client: BaseGraphQLClientProtocol

    def __init__(
        self, client: BaseGraphQLClientProtocol, *args: Any, **kwargs: Any
    ) -> None:
        self.client = client

    @check_execute
    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        return self.client.execute(query, variables, *args, **kwargs)

```

Для отслеживания запуска будем использовать декоратор `check_execute`. Пока он будет
выводить время выполнения метода `client.execute`.
В итоге, типичный пример запуска будет следующим

```python
client = RequestsClient(endpoint="...", token="...")
runner = GraphQLClientRunner(client=client)

runner.execute(query="...", variables={})
# Duration is ... seconds
```

Давайте же совершим первый осмысленный запрос. Схему `github GraphQL API`
можно посмотреть [тут](https://docs.github.com/en/graphql/overview/public-schema). Напишем
простой запрос, который вернет несколько issues из заданного репозитория.

Создадим для хранения запросов отдельную папку

```bash
mkdir github_graphql_client/queries
touch github_graphql_client/queries/__init__.py github_graphql_client/queries/repository.py
```

```python
# Файл `github_graphql_client/queries/repository.py`
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

Для примера, получим две последних закрытых issues из нового проекта
автора `pydantic` -- [FastUI](https://github.com/pydantic/FastUI).
Для этого создадим скрипт `scripts/run.py`

```python
# Файл `scripts/run.py`
import os

from dotenv import load_dotenv

from github_graphql_client.client.requests_client import RequestsClient
from github_graphql_client.runner import GraphQLClientRunner
from github_graphql_client.queries.repository import repository_issues_query

load_dotenv()  # take environment variables from .env

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GRAPHQL_ENDPOINT = os.environ.get("GITHUB_GRAPHQL_ENDPOINT")


def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )
    r_runner = GraphQLClientRunner(client=client)

    data = r_runner.execute(repository_issues_query, {})
    print(data)


if __name__ == "__main__":
    main()

# Duration is 0.4384 seconds
# {'repository': {'issues': {'edges': [{'node': {'title': 'Proposal: New Syntax for components declaration', 'url': 'https://github.com/pydantic/FastUI/issues/84'}}, {'node': {'title': 'fastui requires fastapi', 'url': 'https://github.com/pydantic/FastUI/issues/85'}}]}}}
```

Проект активно живет, так что вы получите другие issues :)

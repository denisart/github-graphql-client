## Первый запрос

Самое простое, что должен уметь наш клиент -- выполнять запросы. Опишем это требование
через абстрактный класс. Добавим несколько новых файлов

```bash
mkdir github_graphql_client/client
touch github_graphql_client/client/__init__.py github_graphql_client/client/base.py
```

В файле `github_graphql_client/client/base.py` определим класс `BaseGraphQLClient`

```python
# Файл `github_graphql_client/client/base.py`
from typing import Any


class BaseGraphQLClient:
    """An abstract class for GraphQL client."""

    endpoint: str
    token: str

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.token = token

    def _get_header(self) -> dict[str, Any]:
        return {"Authorization": f"Bearer {self.token}"}

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        raise NotImplementedError

```

В базовом классе мы сразу реализовали метод, который формирует 
header нашего запроса. Далее любую реализацию клиента будем наследовать от `BaseGraphQLClient`.

Так, как `GraphQL` запрос есть по сути обычный `POST` запрос -- клиент
может быть реализован с помощью пакета [requests](https://pypi.org/project/requests/). Для начала добавим
зависимость

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
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        response = r.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
        )
        response = response.json()
        return response["data"]

```

Давайте же совершим первый осмысленный запрос. 
[Обычно](https://graphql.org/learn/best-practices/) `GraphQL` работает через `HTTP/HTTPS` с некоторым `POST`,
который ожидает на входе `json` с полями `query: str` и `variables: dict[str, Any]`.
Именно так это работает в `github GraphQL API`. Схему `github GraphQL API`
можно посмотреть [тут](https://docs.github.com/en/graphql/overview/public-schema).

Напишем `query`, который вернет несколько `issues` из выбранного репозитория.
Для примера, рассмотрим новый проект автора `pydantic` -- [FastUI](https://github.com/pydantic/FastUI).
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

Для удобства добавим скрипт `scripts/run.py`. Для отслеживания запуска будем использовать декоратор `check_execute`. 

```python
# Файл `scripts/run.py`
import os
import time
from typing import Any

from dotenv import load_dotenv

from github_graphql_client.client.base import BaseGraphQLClient
from github_graphql_client.client.requests_client import RequestsClient
from github_graphql_client.queries.repository import repository_issues_query

load_dotenv()  # take environment variables from .env

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GRAPHQL_ENDPOINT = os.environ.get("GITHUB_GRAPHQL_ENDPOINT")


def check_execute(fn):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration is {toc - tic:0.4f} seconds")
        return result

    return wrapper


@check_execute
def execute_client(client: BaseGraphQLClient, **kwargs) -> Any:
    return client.execute(**kwargs)


def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )

    data = execute_client(client, query=repository_issues_query, variables={})
    print(data)


if __name__ == "__main__":
    main()

# Duration is 0.5096 seconds
# {'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
```

Мы получили несколько issues. Проект активно живет, так что вы должны получить другие issues :)

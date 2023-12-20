## Настройка клиента

Давайте немного улучшим наш клиент, добавив ему больше настроек и возможностей.

### Таймаут

Хорошо, если вы понимаете, сколько должен выполняться ваш запрос. Процитируем
одну хорошо известную [статью](https://habr.com/ru/companies/oleg-bunin/articles/433476/)

> Не ставить таймаут на задачу — это зло. Это значит, что вы не понимаете, что происходит
> в задаче, как должна работать бизнес-логика.

Добавить таймаут для нашего клиента очень просто

```python
# Файл `github_graphql_client/client/requests_client.py`
from typing import Any

import requests as r

from .base import BaseGraphQLClient


class RequestsClient(BaseGraphQLClient):
    """GraphQL client based on `requests` library."""

    DEFAULT_TIMEOUT = 1

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        super().__init__(endpoint, token, **kwargs)

        self.timeout = kwargs.get("timeout", RequestsClient.DEFAULT_TIMEOUT)

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        response = r.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
            timeout=self.timeout,
        )
        response = response.json()
        return response["data"]

```

Мы сделали таймаут необязательным параметром конструктора. Дефолтное значение
сохранено в `DEFAULT_TIMEOUT`. Для простоты мы указали это значение явно как 1 секунда.
Хорошо сконфигурировать это через настройки деплоя вашего проекта 
(например, конфиг приложения).

Посмотрим, что будет, если мы укажем очень маленький таймаут

```python
# Файл `scripts/run.py`
...

def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
        timeout=0.0001,
    )

    data = execute_client(client, query=repository_issues_query, variables={})
    print(data)


if __name__ == "__main__":
    main()

# requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='api.github.com', port=443): Max retries exceeded with url: /graphql (Caused by ConnectTimeoutError(<urllib3.connection.HTTPSConnection object at 0x7f16d16eb790>, 'Connection to api.github.com timed out. (connect timeout=0.0001)'))
```

### Сессия

Про использование сессий в `requests` можно прочитать в официальной документации [тут](https://requests.readthedocs.io/en/latest/user/advanced.html).
Давайте немного подправим наш клиент

```python
# Файл `github_graphql_client/client/requests_client.py`
from typing import Any, Optional
...

class RequestsClient(BaseGraphQLClient):
    ...
    
    session: Optional[r.Session]
    
    def __init__(
        self, endpoint: str, token: str, *args: Any, **kwargs: Any
    ) -> None:
        ...
        
        self.session = None

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        if self.session is None:
            self.session = r.Session()

        response = self.session.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
            timeout=self.timeout,
        )
        ...

    def close_session(self) -> None:
        self.session.close()
        self.session = None

```

Теперь немного исправим наш запрос, чтобы иметь возможность указать
название желаемого репозитория

```python
# Файл `github_graphql_client/queries/repository.py`
def get_repository_issues_query(owner: str, name: str) -> str:
    return """query {
  repository(owner:"%s", name:"%s") {
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
""" % (
        owner,
        name,
    )

```

Давайте совершим несколько запросов подряд и не забудем в конце закрыть соединение с сервером

```python
# Файл `scripts/run.py`
...


def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )

    data = execute_client(
        client,
        query=get_repository_issues_query("pydantic", "FastUI"),
        variables={},
    )
    print(data)

    data = execute_client(
        client,
        query=get_repository_issues_query("pydantic", "pydantic"),
        variables={},
    )
    print(data)

    data = execute_client(
        client,
        query=get_repository_issues_query("pydantic", "pydantic-core"),
        variables={},
    )
    print(data)

    client.close_session()


if __name__ == "__main__":
    main()

# Duration is 0.6439 seconds
# {'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
# Duration is 0.3064 seconds
# {'repository': {'issues': {'edges': [{'node': {'title': "__init__.cpython-311-darwin.so  is an incompatible architecture (have 'x86_64', need 'arm64') in M1 mac mini", 'url': 'https://github.com/pydantic/pydantic/issues/8396'}}, {'node': {'title': 'Override class used in annotations', 'url': 'https://github.com/pydantic/pydantic/issues/8408'}}]}}}
# Duration is 0.3078 seconds
# {'repository': {'issues': {'edges': [{'node': {'title': '2.14.4 release upload failed', 'url': 'https://github.com/pydantic/pydantic-core/issues/1082'}}, {'node': {'title': "(🐞) `ValidationError` can't be instantiated", 'url': 'https://github.com/pydantic/pydantic-core/issues/1115'}}]}}}
```

### Сессии в контекстном менеджере

Чтобы каждый раз не думать о закрытии соединения, добавим возможность использовать сессии внутри
контекстного менеджера. Для этого мы используем методы `__enter__` и `__exit__`.

```python
# Файл `github_graphql_client/client/requests_client.py`
...


class RequestsClient(BaseGraphQLClient):
    """GraphQL client based on `requests` library."""

    ...

    def __enter__(self) -> None:
        self.session = r.Session()

    def __exit__(self, *args):
        self.close_session()

    ...

```

Теперь запустим клиент в контекстном менеджере и в конце посмотрим значение `client.session`.

```python
# Файл `scripts/run.py`
...

def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )

    with client:
        execute_client(
            client,
            query=get_repository_issues_query("pydantic", "FastUI"),
            variables={},
        )

        execute_client(
            client,
            query=get_repository_issues_query("pydantic", "pydantic"),
            variables={},
        )

        execute_client(
            client,
            query=get_repository_issues_query("pydantic", "pydantic-core"),
            variables={},
        )

    print(f'client.session = {client.session}')


if __name__ == "__main__":
    main()

# Duration is 0.7450 seconds
# Duration is 0.3069 seconds
# Duration is 0.3070 seconds
# client.session = None
```

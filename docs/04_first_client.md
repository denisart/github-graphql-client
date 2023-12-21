## Синхронный клиент

Создадим клиент, который научим работать с `BaseTransport`.
После выполнения команд

```bash
mkdir github_graphql_client/client
touch github_graphql_client/client/__init__.py github_graphql_client/client/sync_client.py
```

в файл `github_graphql_client/client/sync_client.py` добавим следующий код

```python
# `github_graphql_client/client/sync_client.py` file
from typing import Any

from github_graphql_client.transport.base import BaseTransport

class SyncGraphQLClient:
    """Sync GraphQL client based on `BaseTransport` transport."""

    transport: BaseTransport

    def __init__(self, transport: BaseTransport) -> None:
        self.transport = transport

    def __enter__(self):
        self.connect_sync()
        return self

    def __exit__(self, *args):
        self.close_sync()

    def connect_sync(self) -> None:
        """Connect to `self.transport`."""
        self.transport.connect()

    def close_sync(self) -> None:
        """Close `self.transport` connection."""
        self.transport.close()

    def execute_sync(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        return self.transport.execute(query, variables, **kwargs)

```

Класс `SyncGraphQLClient` умеет запускать сессию для произвольного класса
`BaseTransport` и получать результаты запросов опуская детали реализации самого запроса.

- метод `connect_sync` создает соединение в `self.transport`;
- метод `close_sync` закрывает соединение в `self.transport`;
- метод `execute_sync` получает данные с сервера с помощью `self.transport`;
- методы `__enter__` и `__exit__` предназначены для того, чтобы запускать клиент в контекстном менеджере и не забывать закрывать соединение;

Проверим, что это работает

```python
# `scripts/run.py` file
...

from github_graphql_client.client.sync_client import SyncGraphQLClient

...

def main():
    transport = RequestsTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )

    with SyncGraphQLClient(transport=transport) as client:
        data = client.execute_sync(
            query=repository_issues_query, variables={},
        )
        print(data)

...

```

Запустив `scripts/run.py`, получим тот же результат

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
```

> Слово `sync` в названии `SyncGraphQLClient` не случайно. Немного позже у нас появится
> `AsyncGraphQLClient`, и мы объединим их в один `GraphQLClient`.

### Несколько запросов

Давайте внутри одной сессии выполним несколько `GraphQL` запросов. Для этого изменим
наш запрос так, чтобы иметь возможность указать название желаемого репозитория.

```python
# `github_graphql_client/queries/repository.py` file
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

Наш скрипт `scripts/run.py` будет выглядеть следующим образом

```python
# `scripts/run.py` file
...

def main():
    transport = RequestsTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )

    with SyncGraphQLClient(transport=transport) as client:
        data = client.execute_sync(
            query=get_repository_issues_query("pydantic", "FastUI"),
            variables={},
        )
        print(data)
        
        data = client.execute_sync(
            query=get_repository_issues_query("pydantic", "pydantic"),
            variables={},
        )
        print(data)
        
        data = client.execute_sync(
            query=get_repository_issues_query("pydantic", "pydantic-core"),
            variables={},
        )
        print(data)

...
```

После запуска получим примерно следующее

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
{'repository': {'issues': {'edges': [{'node': {'title': "__init__.cpython-311-darwin.so  is an incompatible architecture (have 'x86_64', need 'arm64') in M1 mac mini", 'url': 'https://github.com/pydantic/pydantic/issues/8396'}}, {'node': {'title': 'Override class used in annotations', 'url': 'https://github.com/pydantic/pydantic/issues/8408'}}]}}}
{'repository': {'issues': {'edges': [{'node': {'title': '2.14.4 release upload failed', 'url': 'https://github.com/pydantic/pydantic-core/issues/1082'}}, {'node': {'title': "(🐞) `ValidationError` can't be instantiated", 'url': 'https://github.com/pydantic/pydantic-core/issues/1115'}}]}}}
```

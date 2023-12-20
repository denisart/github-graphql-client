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

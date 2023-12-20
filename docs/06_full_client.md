## Создаем клиент

Теперь объединим `SyncGraphQLClient` и `AsyncGraphQLClient`, чтобы
использовать один интерфейс. Создадим файл `github_graphql_client/client/client.py`.

```python
# `github_graphql_client/client/client.py` file
import asyncio
from typing import Any, Union

from github_graphql_client.transport.base import (
    BaseAsyncTransport,
    BaseTransport,
)

from .async_client import AsyncGraphQLClient
from .sync_client import SyncGraphQLClient

class GraphQLClient(SyncGraphQLClient, AsyncGraphQLClient):
    """GraphQL client."""

    transport: Union[BaseTransport, BaseAsyncTransport]

    def __init__(
        self, transport: Union[BaseTransport, BaseAsyncTransport]
    ) -> None:
        super().__init__(transport)

    async def _execute_async(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        async with self as client:
            data = await client.execute_async(
                query,
                variables,
                **kwargs,
            )
        return data

    async def _execute_batch_async(
        self,
        queries: list[str],
        variables: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        tasks = []

        async with self as client:
            for i in range(len(queries)):
                query = queries[i]
                vars = variables[i]

                tasks.append(client.execute_async(query, vars, **kwargs))

            result_data = await asyncio.gather(*tasks)

        return list(result_data)

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""

        if isinstance(self.transport, BaseAsyncTransport):
            return asyncio.run(self._execute_async(query, variables, **kwargs))
        else:
            with self as client:
                return client.execute_sync(query, variables, **kwargs)

    def execute_batch(
        self,
        queries: list[str],
        variables: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Execute a batch of GraphQL queries."""

        if isinstance(self.transport, BaseAsyncTransport):
            return asyncio.run(
                self._execute_batch_async(queries, variables, **kwargs)
            )
        else:
            results = []
            with self as client:
                for i in range(len(queries)):
                    query = queries[i]
                    vars = variables[i]

                    res = client.execute_sync(query, vars, **kwargs)

                    results.append(res)

            return results

```

Два основных метода для использования: `execute` и `execute_batch`. Внутри
эти методы определяют какой тип у "Транспорта", а после вызывают код запуска из
наших прошлых примеров. Попробовать можно с помощью следующего кода

```python
# `scripts/run.py` file
...

def main():
    transport_r = RequestsTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )
    transport_a = AIOHTTPTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )

    client_r = GraphQLClient(transport=transport_r)
    client_a = GraphQLClient(transport=transport_r)

    q_1 = get_repository_issues_query(
        "pydantic",
        "FastUI",
    )
    q_2 = get_repository_issues_query(
        "pydantic",
        "pydantic",
    )
    q_3 = get_repository_issues_query(
        "pydantic",
        "pydantic-core",
    )

    data_11 = client_r.execute(q_1, {})
    data_21 = client_a.execute(q_1, {})

    data_12 = client_r.execute_batch([q_1, q_2, q_3], [{}, {}, {}])
    data_22 = client_a.execute_batch([q_1, q_2, q_3], [{}, {}, {}])

if __name__ == "__main__":
    main()

```

Поздравляю, мы только что написали свою упрощенную версию библиотеки [gql](https://gql.readthedocs.io/en/stable/index.html).
`gql` основана на той же идее, что мы реализовали, но имеет поверх много дополнительного кода:
различные реализации backend (включая веб-сокеты), проверки проблем с соединениями, проверки корректности
результата от сервера.

### Пробуем gql

Мы не будем изучать всю документацию `gql`, попробуем только с помощью нее выполнить наш запрос.
Установим пакет следующим образом

```bash
poetry add "gql[all]"
```

И запустим пример из документации для нашего запроса

```bash
# `scripts/run.py` file
...

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

...

def check_execute(fn):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration for {fn.__name__} is {toc - tic:0.4f} seconds")
        return result

    return wrapper

@check_execute
def main():
    transport = AIOHTTPTransport(
        url=GITHUB_GRAPHQL_ENDPOINT,
        headers={"Authorization": f"Bearer {GITHUB_TOKEN}"},
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Provide a GraphQL query
    query = gql(get_repository_issues_query("pydantic", "FastUI", last=2))

    result = client.execute(query)
    print(result)


if __name__ == "__main__":
    main()

```

Результат будет примерно следующим

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
Duration for main is 8.5059 seconds
```

Ого, 8 секунд! Запрос тот же самый, а значит
время уходит на накладные расходы самой библиотеки. Это связано
с параметром `fetch_schema_from_transport`, который можно указать во время инициализации клиента.
Пакет `gql` базируется на библиотеке [graphql-core](https://github.com/graphql-python/graphql-core),
которая является `python` реализацией проекта [GraphQL.js](https://github.com/graphql/graphql-js).
И если параметр `fetch_schema_from_transport` имеет значение `True`, то во время первого запроса
клиент фетчит схему и билдит ее в формат `graphql_core.GraphQLSchema`. На момент написания
статьи схема `github GraphQL API` содержит `61602` строки. Т.е. все это время уходит именно
на анализ схемы, которая, конечно, довольно большая.

Теперь у нас есть клиент. Далее мы поговорим о том,
как управлять запросами и как хранить результаты запросов.

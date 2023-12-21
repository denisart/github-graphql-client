## Асинхронный клиент

В предыдущем примере мы ожидаем ответ первого запроса и только после этого
отправляем второй запрос. Зачем нам тратить столько времени? Давайте создадим
асинхронный транспорт.

В файле `github_graphql_client/transport/base.py` определим класс `BaseTransport`

```python
# `github_graphql_client/transport/base.py` file
...

class BaseAsyncTransport:
    """An abstract async transport."""

    async def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""
        raise NotImplementedError

    async def connect(self) -> None:
        """Establish a session with the transport."""
        raise NotImplementedError

    async def close(self) -> None:
        """Close a session."""
        raise NotImplementedError

```

Для примера реализуем асинхронный backend на `aiohttp`. Добавим этот пакет в проект

```bash
poetry add aiohttp
```

В новом файле `github_graphql_client/transport/aiohttp.py` определим класс `AIOHTTPTransport`

```python
# `github_graphql_client/transport/aiohttp.py` file
from typing import Any, Optional

import aiohttp

from github_graphql_client.transport.base import BaseAsyncTransport

class AIOHTTPTransport(BaseAsyncTransport):
    """The transport based on aiohttp library."""

    DEFAULT_TIMEOUT = 1
    session: Optional[aiohttp.ClientSession]

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.token = token
        self.auth_header = {"Authorization": f"Bearer {self.token}"}
        self.timeout = kwargs.get("timeout", AIOHTTPTransport.DEFAULT_TIMEOUT)

        self.session = None

    async def connect(self) -> None:
        """Coroutine which will create an aiohttp ClientSession() as self.session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.auth_header,
            )
        else:
            raise Exception(f"AIOHTTPTransport is already connected")

    async def close(self) -> None:
        """Coroutine which will close the aiohttp session."""
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query with aiohttp."""
        if self.session is None:
            raise Exception(f"AIOHTTPTransport session not connected")

        async with self.session.post(
            self.endpoint,
            json={"query": query, "variables": variables},
        ) as response:
            data = await response.json()

        return data.get("data")

```

Тут все очень похоже на `RequestsTransport`

- `connect` - это корутина, которая создает сессию с помощью `aiohttp`;
- `close` - корутина, которая закрывает `aiohttp` сессию;
- `execute` - корутина, которая с помощью открытой `aiohttp` сессии получает данные с сервера;

Попробуем

```python
# `scripts/run.py` file
import asyncio
...

async def run_aiohttp_transport():
    transport = AIOHTTPTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )
    await transport.connect()

    data = await transport.execute(
        query=get_repository_issues_query("pydantic", "FastUI"),
        variables={},
    )
    print(data)

    await transport.close()

def amain():
    asyncio.run(run_aiohttp_transport())

if __name__ == "__main__":
    amain()

```

Мы получим тот же результат

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
```

Теперь создадим асинхронный клиент для работы с `BaseAsyncTransport`.

```python
# `github_graphql_client/client/async_client.py` file`
from typing import Any

from github_graphql_client.transport.base import BaseAsyncTransport

class AsyncGraphQLClient:
    """Async GraphQL client based on `BaseAsyncTransport` transport."""

    transport: BaseAsyncTransport

    def __init__(self, transport: BaseAsyncTransport) -> None:
        self.transport = transport

    async def __aenter__(self):
        await self.connect_async()
        return self

    async def __aexit__(self, *args):
        await self.close_async()

    async def connect_async(self) -> None:
        """Connect to `self.transport`."""
        await self.transport.connect()

    async def close_async(self) -> None:
        """Close `self.transport` connection."""
        await self.transport.close()

    async def execute_async(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        return await self.transport.execute(query, variables, **kwargs)

```

Тут все так же, как в `SyncGraphQLClient`, но в асинхронной версии.
Проверим

```python
# `scripts/run.py` file
...

async def amain():
    transport = AIOHTTPTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )

    async with AsyncGraphQLClient(transport=transport) as client:
        data = await client.execute_async(
            query=get_repository_issues_query("pydantic", "FastUI", last=2),
            variables={},
        )
        print(data)

def main():
    asyncio.run(amain())

if __name__ == "__main__":
    main()

```

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
```

Теперь перепишем последний пример предыдущего раздела с помощью нового асинхронного клиента

```python
# `scripts/run.py` file
...

def check_execute(fn):
    async def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = await fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration for {fn.__name__} is {toc - tic:0.4f} seconds")
        return result

    return wrapper

@check_execute
async def execute(client, query: str, variables: dict[str, Any]) -> None:
    data = await client.execute_async(query, variables)
    print(data)

@check_execute
async def amain():
    transport = AIOHTTPTransport(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
    )

    async with AsyncGraphQLClient(transport=transport) as client:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                execute(
                    client,
                    query=get_repository_issues_query(
                        "pydantic", "FastUI",
                    ),
                    variables={},
                )
            )

            tg.create_task(
                execute(
                    client,
                    query=get_repository_issues_query(
                        "pydantic", "pydantic",
                    ),
                    variables={},
                )
            )
            
            tg.create_task(
                execute(
                    client,
                    query=get_repository_issues_query(
                        "pydantic", "pydantic-core",
                    ),
                    variables={},
                )
            )

def main():
    asyncio.run(amain())

...
```

В контекстном менеджере клиента `AsyncGraphQLClient` мы запускаем несколько задач
`execute`. Для удобства добавим декоратор `check_execute`, который будет выводить
время выполнения

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': 'More PageEvent Triggers', 'url': 'https://github.com/pydantic/FastUI/issues/104'}}, {'node': {'title': 'TypeError: Interval() takes no arguments', 'url': 'https://github.com/pydantic/FastUI/issues/105'}}]}}}
Duration for execute is 0.5999 seconds
{'repository': {'issues': {'edges': [{'node': {'title': '2.14.4 release upload failed', 'url': 'https://github.com/pydantic/pydantic-core/issues/1082'}}, {'node': {'title': "(🐞) `ValidationError` can't be instantiated", 'url': 'https://github.com/pydantic/pydantic-core/issues/1115'}}]}}}
Duration for execute is 0.5987 seconds
{'repository': {'issues': {'edges': [{'node': {'title': "__init__.cpython-311-darwin.so  is an incompatible architecture (have 'x86_64', need 'arm64') in M1 mac mini", 'url': 'https://github.com/pydantic/pydantic/issues/8396'}}, {'node': {'title': 'Override class used in annotations', 'url': 'https://github.com/pydantic/pydantic/issues/8408'}}]}}}
Duration for execute is 0.5991 seconds
Duration for amain is 0.6005 seconds
```

Теперь мы видим, что клиент не тратит время на ожидание ответа с сервера.

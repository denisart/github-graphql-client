# Готовый клиент

В реальном проекте написанный нами клиент будет мало полезен. Хочется уметь добавлять
туда параметры (тайм-аут), добавить cookie, использовать асинхронные запросы.

На официальном сайте `graphql org` [представлены](https://graphql.org/code/) различные инструменты
для разных языков программирования. Во вкладке `python/client` первым указан клиент [gql](https://gql.readthedocs.io/en/stable/).

Давайте напишем еще один клиент, которые будет базироваться на библиотеке `gql`. Для этого установим
`gql`

```bash
poetry add "gql[all]"
```

Для начала просто используем `Basic usage` из документации `gql`

```python
# Файл `github_graphql_client/client/gql_client.py`
from typing import Any

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .base import BaseGraphQLClient


class GqlClient(BaseGraphQLClient):
    """GraphQL client based on `gql` lib."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        transport = AIOHTTPTransport(
            url=self.endpoint, headers=self._get_header()
        )
        self.client = Client(
            transport=transport, fetch_schema_from_transport=True
        )

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        gql_query = gql(query)
        return self.client.execute(
            gql_query, variable_values=variables, *args, **kwargs
        )

```

И запустим наш скрипт `scripts/run.py` с этим клиентом. Мы увидим примерно следующее

```bash
Duration is 8.0584 seconds
{'repository': {'issues': {'edges': [{'node': {'title': 'Proposal: New Syntax for components declaration', 'url': 'https://github.com/pydantic/FastUI/issues/84'}}, {'node': {'title': 'fastui requires fastapi', 'url': 'https://github.com/pydantic/FastUI/issues/85'}}]}}}
```

Вот и первая проблема -- длительность выполнения метода. Запрос тот же самый, а значит
время уходит на накладные расходы самой библиотеки. Давайте после инициализации клиента
сделаем два запроса подряд

```python
# Файл `scripts/run.py`
...

def main():
    client = GqlClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )
    r_runner = GraphQLClientRunner(client=client)

    data = r_runner.execute(repository_issues_query, {})
    data = r_runner.execute(repository_issues_query, {})
    print(data)

...
```

Итог будет примерно следующим

```bash
Duration is 9.0009 seconds
Duration is 0.4522 seconds
{'repository': {'issues': {'edges': [{'node': {'title': 'Proposal: New Syntax for components declaration', 'url': 'https://github.com/pydantic/FastUI/issues/84'}}, {'node': {'title': 'fastui requires fastapi', 'url': 'https://github.com/pydantic/FastUI/issues/85'}}]}}}
```

Т.е. второй раз метод `execute` выполнялся примерно в 20 раз быстрее. Это связано
с параметром `fetch_schema_from_transport`, который можно указать во время инициализации клиента.
Пакет `gql` базируется на библиотеке [graphql-core](https://github.com/graphql-python/graphql-core),
которая является `python` реализацией проекта [GraphQL.js](https://github.com/graphql/graphql-js).
И есть параметр `fetch_schema_from_transport` имеет значение `True`, то во время первого запроса
клиент фетчит схему и билдит ее в формат `graphql_core.GraphQLSchema`. На момент написания
статьи схема `github GraphQL API` содержит `61602` строки. Т.е. все это время уходит именно
на анализ схемы, которая, конечно, довольно большая.

Не используя параметр `fetch_schema_from_transport`, мы лишаемся валидации запроса на стороне клиента,
т.е. нашей стороне. Это можно перенести на уровень тестов.

В микро-сервисной архитектуре можно версионировать схему путем версионирования сервера.
Давайте зафиксируем версию схемы и напишем тест, который будет проверять корректность наших
запросов.

Установим `pytest`

```bash
poetry add pytest --group test
```

Для просты схему будем хранить в файле `tests/data/schema.docs.graphql`. Напишем тест для валидации

```python
# Файл `tests/test_queries_validation.py`
from pathlib import Path

from gql import Client
from graphql import Source, parse

from github_graphql_client.queries.repository import repository_issues_query

SCHEMA_FILENAME = Path(__file__).parent / Path("data/schema.docs.graphql")

with SCHEMA_FILENAME.open("r", encoding="utf8") as f:
    schema_str = f.read()


client = Client(schema=schema_str)


def test_repository_issues_query():
    source = Source(repository_issues_query)
    client.validate(parse(source))

```

Тут происходит следующее: клиент `gql` можно инициализировать, указав явно схему. Далее мы 
пользуемся тем, что клиент, которые имеет схему, предоставляет метод `client.validate`.

Для примера, совершим ошибку в нашем запросе и запустим тест:

```python
# Файл `github_graphql_client/queries/repository.py`
repository_issues_query = """
...
  repository(owner:"pydantic", name:"FastUI") {
    issuess(last:2, states:CLOSED) {
...
"""

```

Запуск теста скажет нам примерно следующее

```bash
document = DocumentNode at 0:183

    def validate(self, document: DocumentNode):
        """:meta private:"""
        assert (
            self.schema
        ), "Cannot validate the document locally, you need to pass a schema."
    
        validation_errors = validate(self.schema, document)
        if validation_errors:
>           raise validation_errors[0]
E           graphql.error.graphql_error.GraphQLError: Cannot query field 'issuess' on type 'Repository'. Did you mean 'issues' or 'issue'?
E           
E           GraphQL request:4:5
E           3 |   repository(owner:"pydantic", name:"FastUI") {
E           4 |     issuess(last:2, states:CLOSED) {
E             |     ^
E           5 |       edges {
```

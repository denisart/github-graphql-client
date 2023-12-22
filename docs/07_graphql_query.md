## Работа с запросами

Только что мы увидели проблему фетчинга большой схемы. Фетчинг происходит для того, 
чтобы произвести валидацию запросов на клиенте. Если зафиксировать схему, с которой
мы работаем, то валидацию можно перенести на уровень тестов.

### Валидация запросов

Установим `pytest`

```bash
poetry add pytest --group test
```

Сохраним `GrpahQL` схему локально
в файле `tests/data/schema.docs.graphql`. Тест для валидации
нашего запроса `repository` будет следующим

```python
# `tests/test_queries_validation.py` file
from pathlib import Path

from graphql import Source, parse, build_schema, validate, GraphQLSchema

from github_graphql_client.queries.repository import get_repository_issues_query

SCHEMA_FILENAME = Path(__file__).parent / Path("data/schema.docs.graphql")

def get_schema() -> GraphQLSchema:
    with SCHEMA_FILENAME.open("r", encoding="utf8") as f:
        schema_str = f.read()

    return build_schema(schema_str)

schema = get_schema()

def test_repository_issues_query():
    query = get_repository_issues_query("pydantic", "FastUI")
    document = parse(Source(query))

    validation_errors = validate(schema, document)
    if validation_errors:
        raise validation_errors[0]

```

Что происходит

- с помощью библиотеки `graphql-core` создаем объект `graphql.GraphQLSchema` используя схему в формате строки;
- парсим запрос с помощью метода `graphql.parse`;
- используем метод `graphql.validate(schema, document)` для валидации запроса;

> Если использовать `gql`, то `gql.Client` предоставляет готовый метод валидации
> `gql.Client.validate`.

Для примера, допустим ошибку в названии поля `issues` внутри нашего запроса и запустим тест:

```python
# Файл `github_graphql_client/queries/repository.py`
repository_issues_query = """
...
  repository(owner:"pydantic", name:"FastUI") {
    issuess(last:2, states:CLOSED) {
...
"""

```

Тест скажет нам примерно следующее

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

### GraphQL variables

Мы еще ни разу не использовали `GraphQL variables`. Рассмотрим следующий запрос `marketplaceCategories`
к `github GraphQL API`

```graphql
"""
Get alphabetically sorted list of Marketplace categories
"""
marketplaceCategories(
  """
  Exclude categories with no listings.
  """
  excludeEmpty: Boolean

  """
  Returns top level categories only, excluding any subcategories.
  """
  excludeSubcategories: Boolean

  """
  Return only the specified categories.
  """
  includeCategories: [String!]
): [MarketplaceCategory!]!
```

Добавим его в `github_graphql_client/queries/`

```python
# `github_graphql_client/queries/marketplaceCategories.py` file
def get_marketplace_categories(
    exclude_empty: bool,
    exclude_subcategories: bool,
    include_categories: list[str],
) -> str:
    return """query {
  marketplaceCategories(excludeEmpty: %s, excludeSubcategories: %s, includeCategories: %s) {
    id
    description
  } 
}""" % (
        str(exclude_empty).lower(),
        str(exclude_subcategories).lower(),
        str(include_categories).replace("'", '"'),
    )
```

Чтобы создать корректную строку с `GraphQL` запросом с помощью форматирования строк,
нам необходимо

- преобразовать булево значение `True/False` в строку `true/false`;
- преобразовать массив строк `['1', '2', '3']` в строку `'["1", "2", "3"]'`;

Бывают и более сложные кейсы, когда нам нужен массив `enum` значений. Т.е.
массив `["A", "B"]` необходимо преобразовать в строку `'[A, B]'`;

Чтобы этого избежать эти преобразования и нужны `GraphQL variables`:

```python
# `github_graphql_client/queries/marketplaceCategories.py` file
from typing import Any

def get_marketplace_categories(
    exclude_empty: bool,
    exclude_subcategories: bool,
    include_categories: list[str],
) -> tuple[str, dict[str, Any]]:
    variables = {
        "excludeEmpty": exclude_empty,
        "excludeSubcategories": exclude_subcategories,
        "includeCategories": include_categories,
    }

    query = """query(
  $excludeEmpty: Boolean
  $excludeSubcategories: Boolean
  $includeCategories: [String!]
) {
  marketplaceCategories(
    excludeEmpty: $excludeEmpty,
    excludeSubcategories: $excludeSubcategories,
    includeCategories: $includeCategories
  ) {
    id
    description
  } 
}"""

    return query, variables
```

Теперь наша функция `get_marketplace_categories` возвращает строку с запросов
и словарь `variables`. Не забудем добавить тест

```python
# `tests/test_queries_validation.py` file
...

from github_graphql_client.queries.marketplaceCategories import \
    get_marketplace_categories

...

def test_get_marketplace_categories():
    query, _ = get_marketplace_categories(True, False, ["1", "2", "3"])
    document = parse(Source(query))

    validation_errors = validate(schema, document)
    if validation_errors:
        raise validation_errors[0]
```

### Пакет graphql-query

Какие еще могут возникнуть проблему при управлении `GraphQL` запросами

- шарить повторяющиеся куски запроса между разными запросами;
- использовать фрагменты и инлайн-фрагменты;
- использовать несколько `GraphQL` запросов внутри одного;
- использовать алиасы для имени запроса;

Чем больше становится объем запросов в нашем проекте, тем сложнее
всем этим управлять. По этим причинам была разработана библиотека `graphql-query`.
Она предоставляет возможность генерации валидных строк с `GraphQL` запросами
используя `python` классы. Генерация основана на библиотеке [jinja2](https://).

Документацию `graphql-query` можно посмотреть тут: https://denisart.github.io/graphql-query/.
Так же есть [статья](https://habr.com/ru/articles/707374/) на `habr` с пересказом документации на русском языке.

Для демонстрации перепишем наши текущие запросы используя `graphql-query`

```bash
poetry add graphql-query
```

Структура того, как устроен запрос

- Создаем объект `graphql_query.Operation`, который есть наш запрос;
- Указываем тип для `graphql_query.Operation`: `query`, `mutation`, `subscription`.
- Указываем имя `graphql_query.Operation`. Это шаг не обязательный, но является хорошей практикой. Сервер сможет по названию отслеживать метрики этого запроса именно от вашего сервиса;
- Добавляем в `graphql_query.Operation` все необходимые `variables` в формате `graphql_query.Variable`;
- Сами запросы создаем через `graphql_query.Query`;
- У `graphql_query.Query` указываем имя, список аргументов через `graphql_query.Argument` и список желаемых полей.

Поля, переменные, аргументы задаются специальными классами. А значит их легко шарить между
разными запросами. Если у вас в проекте всего один запрос, то такой подход может усложнить разработку,
потому что кода становится больше.

Пример запроса `marketplaceCategories` в формате `graphql-query`

```python
# `github_graphql_client/queries/marketplaceCategories.py` file
from typing import Any

from graphql_query import Operation, Argument, Variable, Field, Query

var_exclude_empty = Variable(name="excludeEmpty", type="Boolean")
var_exclude_subcategories = Variable(
    name="excludeSubcategories", type="Boolean"
)
var_include_categories = Variable(name="includeCategories", type="[String!]")

def get_marketplace_categories(
    exclude_empty: bool,
    exclude_subcategories: bool,
    include_categories: list[str],
) -> tuple[str, dict[str, Any]]:
    marketplace_categories_query = Query(
        name="marketplaceCategories",
        arguments=[
            Argument(name="excludeEmpty", value=var_exclude_empty),
            Argument(
                name="excludeSubcategories",
                value=var_exclude_subcategories,
            ),
            Argument(name="includeCategories", value=var_include_categories),
        ],
        fields=["id", "description"],
    )

    operation = Operation(
        type="query",
        name="getMarketplaceCategories",
        variables=[
            var_exclude_empty,
            var_exclude_subcategories,
            var_include_categories,
        ],
        queries=[marketplace_categories_query],
    )

    variables = {
        var_exclude_empty.name: exclude_empty,
        var_exclude_subcategories.name: exclude_subcategories,
        var_include_categories.name: include_categories,
    }

    return operation.render(), variables
```

Вызов `operation.render()` вернет нам следующий результат

```graphql
query getMarketplaceCategories(
  $excludeEmpty: Boolean
  $excludeSubcategories: Boolean
  $includeCategories: [String!]
) {
  marketplaceCategories(
    excludeEmpty: $excludeEmpty
    excludeSubcategories: $excludeSubcategories
    includeCategories: $includeCategories
  ) {
    id
    description
  }
}
```

Не забываем убедиться, что тест `test_get_marketplace_categories` все так же
завершается успешно. Остальные примеры использования (включая `graphql_query.Fragment` и `graphql_query.InlineFragment`)
можно посмотреть в документации.

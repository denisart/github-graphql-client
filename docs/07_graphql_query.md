## Работа с запросами

Только что мы увидели проблему, когда при использовании `gql` мы фетчим очень большую схему -
первый запрос может быть долгим. Фетчинг схемы происходит для того, чтобы производить
дальнейшую валидацию запросов на клиенте. Чтобы не лишаться валидации запросов на стороне
клиента мы можем перенести ее на уровень тестов.

### Валидация запросов

Установим `pytest`

```bash
poetry add pytest --group test
```

Для валидации нам нужна локальная схема. Сохраним ее
в файле `tests/data/schema.docs.graphql`. Напишем тест для валидации

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

Что происходит в этом тесте

- с помощью библиотеки `graphql-core` создаем объект `graphql.GraphQLSchema` используя схему, представленную в строке;
- парсим запрос с помощью метода `graphql.parse`;
- используем метод `graphql.validate(schema, document)` для валидации запроса;

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

### GraphQL variables

Предположим, что мы рассматриваем следующий запрос к `github GraphQL API`:

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

Давайте его добавим к нам в проект

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

Преобразования переменных к строке в `python` не полностью подходят для `GraphQL`,
поэтому необходимо делать преобразования входных параметров. Чтобы этого избежать, давайте
используем `GraphQL variables`:

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

Не забудем добавить тест

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

Какие задачи при управлении `GraphQL` запросами у нас могут возникнуть

- использовать `GraphQL variables`;
- шарить повторяющиеся куски между разными запросами;
- использовать фрагменты;
- использовать несколько `GraphQL` запросов внутри одного;
- что-то еще...

И чем быстрее растет объем запросов в вашем проекте, тем сложнее становится
всем этим управлять. Для упрощения была разработана библиотека graphql-query.
Это возможность генерации валидных `GraphQL` строк используя `python` классы.
Документацию можно посмотреть тут: https://denisart.github.io/graphql-query/, 
так же есть статья на habr: https://habr.com/ru/articles/707374/.

Не демонстрировать все возможности - большое кол-во примером можно посмотреть в
документации. Перепишем наши текущие запросы используя `graphql-query`

```bash
poetry add graphql-query
```

Структура того, как устроен запрос

- Создаем объект `graphql_query.Operation`, который есть наш запрос;
- Указываем тип `graphql_query.Operation`: `query`, `mutation`, `subscription`.
- Указываем имя `graphql_query.Operation`. Это не обязательно, но является хорошей практикой. Сервер сможет по названию отслеживать метрики ваших запросов;
- Добавляем в `graphql_query.Operation` все необходимые `variables` в формате `graphql_query.Variable`;
- Создаем все необходимые запросы через `graphql_query.Query`;
- У `graphql_query.Query` указываем имя, список аргументов через `graphql_query.Argument`, список полей.

Поля, переменные, аргументы задаются специальными классами. А значит их легко шарить между
разными запросами.

Пример запроса `marketplaceCategories`

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

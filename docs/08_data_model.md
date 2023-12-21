## Модель данных

Давайте запросим 20 последних открытых `issues` библиотеки `pydantic`. Немного
обновим наш запрос `repository`

```python
# `github_graphql_client/queries/repository.py` file
...
var_issue_state = Variable(name="IssueState", type="[IssueState!]")

...

def get_repository_issues_query(
    owner: str,
    name: str,
    last: int,
    state: str,
) -> tuple[str, dict[str, Any]]:
    ...
    
    operation = Operation(
        ...
        variables=[var_owner, var_name, var_last, var_issue_state],
        ...
    )

    return operation.render(), {
        var_owner.name: owner,
        var_name.name: name,
        var_last.name: last,
        var_issue_state.name: state,
    }
```

Результат запроса `get_repository_issues_query("pydantic", "pydantic", 20, "OPEN")`
будет примерно следующим

```bash
$ python3 scripts/run.py
{'repository': {'issues': {'edges': [{'node': {'title': "Can't use config keyword argument with TypeAdapter.__init__ on stdlib dataclass", 'url': 'https://github.com/pydantic/pydantic/issues/8326'}}, {'node': {'title': 'Constructor for model with `Json[list[int]]` field should accept `list[int]`, like mypy already expects', 'url': 'https://github.com/pydantic/pydantic/issues/8336'}}, {'node': {'title': 'JSON serialization issue with ipaddress classes as alternative', 'url': 'https://github.com/pydantic/pydantic/issues/8343'}}, {'node': {'title': 'Indeterminate: LookupError when generating custom schema output', 'url': 'https://github.com/pydantic/pydantic/issues/8359'}}, {'node': {'title': 'Implement more clear warning/error when using constraints on compound types', 'url': 'https://github.com/pydantic/pydantic/issues/8362'}}, {'node': {'title': 'Magic validation methods needs to be documented for version 2', 'url': 'https://github.com/pydantic/pydantic/issues/8374'}}, {'node': {'title': 'More consistent and intuitive `alias` behavior for validation and serialization', 'url': 'https://github.com/pydantic/pydantic/issues/8379'}}, {'node': {'title': 'Common mistakes docs section', 'url': 'https://github.com/pydantic/pydantic/issues/8380'}}, {'node': {'title': 'Deprecate `update_json_schema` function', 'url': 'https://github.com/pydantic/pydantic/issues/8381'}}, {'node': {'title': 'coerce_numbers_to_str needs a per-field variant', 'url': 'https://github.com/pydantic/pydantic/issues/8383'}}, {'node': {'title': 'Bus error when using custom type impl with SQLAlchemy ', 'url': 'https://github.com/pydantic/pydantic/issues/8385'}}, {'node': {'title': 'Allow optional properties to be truely optional', 'url': 'https://github.com/pydantic/pydantic/issues/8394'}}, {'node': {'title': '`@property` changes behavior when using dataclass-ish classes', 'url': 'https://github.com/pydantic/pydantic/issues/8401'}}, {'node': {'title': "Regex's pattern is not serialized when creating a model's JSON schema", 'url': 'https://github.com/pydantic/pydantic/issues/8405'}}, {'node': {'title': 'cached_property is not ignored when a model is copied and updated', 'url': 'https://github.com/pydantic/pydantic/issues/8406'}}, {'node': {'title': 'BaseModel causes information loss with Generic classes', 'url': 'https://github.com/pydantic/pydantic/issues/8410'}}, {'node': {'title': "JSON Schema is wrong when `mode='serialization'` and fields have a default", 'url': 'https://github.com/pydantic/pydantic/issues/8413'}}, {'node': {'title': 'Bytes and Bits Conversion Type', 'url': 'https://github.com/pydantic/pydantic/issues/8415'}}, {'node': {'title': 'Debian/ubuntu packages for v2', 'url': 'https://github.com/pydantic/pydantic/issues/8416'}}, {'node': {'title': "Union discriminator tag fails if '_' is in the literal value", 'url': 'https://github.com/pydantic/pydantic/issues/8417'}}]}}}
```

Давайте пробежимся по `issues` и принтанем все `title`. Код будет примерно таким

```python
for issue in result["repository"]["issues"]["edges"]:
    print(issue["node"]["title"])
```

Не очень удобно. Хотелось бы иметь подсказки от IDE и писать что-то типа

```python
for issue in repository.issues.edges:
    print(issue.node.title)
```

Для этого можно создать классы, повторяющие типа из `GraphQL` схемы. Тут есть две проблемы
как создавать классы? Какой использовать базовый класс?

### Базовый класс

Первый вариант - `dataclasses.dataclass`. Это хорошо, но возникает проблема
для вложенных типов. Альтернативный вариант [dataclasses-json](https://github.com/lidatong/dataclasses-json).
Это обычные дата-классы дополненные методами `from_json`, `from_dict`, которые
умеют преобразовывать вложенные типы. Проблемы

- необходы свои сериализаторы/десеарилазоты для типа `union` (в новых версиях проблема может быть решена);
- преобразование объекта с глубокой вложенность может занимать много времени;

Современный подход - `pydantic`. Рассмотрим наш пример (не забыл добавить `pydantic` в проект)

```python
from pydantic import BaseModel

class Issue(BaseModel):
    title: str
    url: str

class IssueEdge(BaseModel):
    node: Issue

class IssueConnection(BaseModel):
    edges: list[IssueEdge]

class Repository(BaseModel):
    issues: IssueConnection

repository = Repository.model_validate(result["repository"])

for issue in repository.issues.edges:
    print(issue.node.title)
```

## Поддержка классов

Представим, сколько нужно создать классов, чтобы полностью описать всю схему
`github GraphQL API`. Так же, если эта схема часто изменяется - нужно выполнять
много рутинной работы по актуализации дата-модели. Хочется создавать классы автоматически
по имеющейся схеме.
 
Эта необходимость привела к созданию библиотеки [graphql2python](https://denisart.github.io/graphql2python/).
Сейчас эти наработки перенесены в библиотеку [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator) -
известную библиотеку для генерации модели данных по `Open API` схеме.

Запустим `datamodel-code-generator` для нашей схемы

```bash
$ datamodel-codegen --input tests/data/schema.docs.graphql --input-file-type graphql --output github_graphql_client/model.py
```

Примеры классов выше, но в формате, сгенерированном `datamodel-code-generator` (без настроек)

```python
# `github_graphql_client/mode.py` file
...

class Issue(
    Assignable,
    Closable,
    Comment,
    Deletable,
    Labelable,
    Lockable,
    Node,
    ProjectV2Owner,
    Reactable,
    RepositoryNode,
    Subscribable,
    SubscribableThread,
    UniformResourceLocatable,
    Updatable,
    UpdatableComment,
):
    """
    An Issue is a place to discuss ideas, enhancements, tasks, and bugs for a project.
    """

    ...

...

class IssueEdge(BaseModel):
    """
    An edge in a connection.
    """

    cursor: String
    node: Optional[Issue] = None
    typename__: Optional[Literal['IssueEdge']] = Field(
        'IssueEdge', alias='__typename'
    )

...

class IssueConnection(BaseModel):
    """
    The connection type for Issue.
    """

    edges: Optional[List[Optional[IssueEdge]]] = Field(default_factory=list)
    nodes: Optional[List[Optional[Issue]]] = Field(default_factory=list)
    pageInfo: PageInfo
    totalCount: Int
    typename__: Optional[Literal['IssueConnection']] = Field(
        'IssueConnection', alias='__typename'
    )

...

class Repository(
    Node,
    PackageOwner,
    ProjectOwner,
    ProjectV2Recent,
    RepositoryInfo,
    Starrable,
    Subscribable,
    UniformResourceLocatable,
):
    """
    A repository contains the content for a project.
    """
    
    ...

...
```

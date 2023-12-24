## Заключение

Мы написали клиент, который уже может приносить пользу при решении
некоторых практических задач.
Но все равно остался ряд тем, которые вышли за рамками данной статьи.
Например,

- сервер отклоняет запрос из-за большого количества токенов в нем;
- поддержка кастомных скаляров;
- работа клиента через websockets;
- что делать, если нужно одновременно совершить несколько сотен/тысяч однотипных мутаций?

Индустрия так же не стоит на месте. Наиболее актуальные инструменты для
GraphQL клиентов можно посмотреть тут: [https://graphql.org/code/#python-client](https://graphql.org/code/#python-client).
Например, стоит обратить внимание на молодой инструмент [ariadne-codegen](https://github.com/mirumee/ariadne-codegen)
для генерации типизированного GraphQL клиента по вашим схемам и запросам.

Буду рад услышать ваш опыт работы с GraphQL клиентами на python
в комментариях. Возможно, вы решали проблему, которая не упоминается в
данной статье и можете о ней рассказать.

Спасибо за внимание!
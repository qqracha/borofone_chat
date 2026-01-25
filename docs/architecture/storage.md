# Storage

## Storage

### Postgres

В Postgres храним комнаты и сообщения.&#x20;

Текущая модель в репозитории включает:

* `rooms(id, title)`
* `messages(id, room_id, author, body, created_at, client_msg_id)`&#x20;

После перехода на Discord-подобную схему план/факт решения: заменить `client_msg_id` на `nonce` (и хранить `nonce` в `messages` для отладки/трассировки), а дедуп делать через Redis TTL, а не через уникальность в БД.

### Redis

Redis используется для:

* Healthcheck (`PING`).&#x20;
* Дедупликации по `nonce` в пределах TTL-окна (ключи вида `nonce:{author}:{nonce}`).&#x20;

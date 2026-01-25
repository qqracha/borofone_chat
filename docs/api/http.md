# HTTP

## HTTP API

### Health

`GET /health` возвращает `ok` и флаг доступности Redis.&#x20;

Пример ответа:

```json
{"ok": true, "redis": true}
```

### Rooms <a href="#rooms" id="rooms"></a>

### Создать комнату

`POST /rooms` с payload `{ "title": "room" }`.&#x20;

### Получить сообщения комнаты

`GET /rooms/{room_id}/messages?limit=50` возвращает список сообщений.&#x20;

### Messages (создание) <a href="#messages" id="messages"></a>

`POST /rooms/{room_id}/messages` создаёт сообщение.&#x20;

Переход на Discord-подобный контракт: вместо `client_msg_id` используется `nonce + enforce_nonce`, при `enforce_nonce=true` повторы с тем же `nonce` “в пределах нескольких минут” должны вернуть уже созданное сообщение.

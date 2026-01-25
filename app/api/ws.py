from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[int, set[WebSocket]] = {}

    async def connect(self, ws: WebSocket, room_id: int) -> None:
        await ws.accept()  # accept обязателен до send/receive [web:1]
        self._rooms.setdefault(room_id, set()).add(ws)

    def disconnect(self, ws: WebSocket, room_id: int) -> None:
        room = self._rooms.get(room_id)
        if not room:
            return
        room.discard(ws)
        if not room:
            self._rooms.pop(room_id, None)

    async def broadcast(self, room_id: int, payload: dict) -> None:
        room = self._rooms.get(room_id, set())
        dead: list[WebSocket] = []
        for ws in room:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room_id)


manager = ConnectionManager()


@router.websocket("/ws/rooms/{room_id}")
async def ws_room(ws: WebSocket, room_id: int):
    await manager.connect(ws, room_id)
    try:
        while True:
            data = await ws.receive_json()
            # Каркас: просто эхо в комнату. Ты заменишь на запись в БД/Redis и доменные события.
            await manager.broadcast(room_id, {"type": "message", "room_id": room_id, "data": data})
    except WebSocketDisconnect:
        manager.disconnect(ws, room_id)

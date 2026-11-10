from fastapi import WebSocket


class ConnectionManager:
    def __init__(self, max_connections: int = 100) -> None:
        self.active: list[WebSocket] = []
        self.max_connections = max_connections

    async def connect(self, websocket: WebSocket) -> None:
        if len(self.active) >= self.max_connections:
            await websocket.close(code=1013, reason="Connection limit reached")
            return
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        for websocket in list(self.active):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(websocket)


manager = ConnectionManager()

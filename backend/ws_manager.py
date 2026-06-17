from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Store one active websocket per submission id so judge updates can be routed directly.
        self.connection: dict[int, WebSocket] = {}

    async def connect(self, submission_id:int, websocket: WebSocket):
        await websocket.accept()

        self.connection[submission_id]= websocket

    def disconnect(self, submission_id:int):
        self.connection.pop(submission_id, None)


    async def send(self, submission_id:int, payload:dict):
        websocket= self.connection.get(submission_id)

        if websocket:
            await websocket.send_json(
                payload
            )

manager= ConnectionManager()

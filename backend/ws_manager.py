from fastapi import WebSocket

class ConnectionManager:
    def __int__(self):
        self.connection={}

    async def connect(self, submission_id:int, websocket: WebSocket):
        await websocket.accept()

        self.connection[submission_id]= websocket

    def disconnect(self, submission_id:id):
        self.connection.pop(submission_id, None)


    async def send(self, submission_id:int, payload:dict):
        websocket= self.connection.get(submission_id)

        if websocket:
            await websocket.send_json(
                payload
            )

manager= ConnectionManager()
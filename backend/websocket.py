from fastapi import APIRouter, WebSocket
from ws_manager import manager

router= APIRouter()

@router.websocket("/ws/{submission_id}")
async def websocket_endpoint(websocket:WebSocket, submission_id:int):   
    await manager.connect(submission_id,websocket)

    try:
        while True:
            await websocket.receive_text()
    except Exception:
        manager.disconnect(submission_id)
        
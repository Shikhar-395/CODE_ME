from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from .auth import COOKIE_NAME, verify_token
from .database import SessionLocal
from .model import Submission
from .ws_manager import manager

router = APIRouter()


@router.websocket("/ws/{submission_id}")
async def websocket_endpoint(websocket: WebSocket, submission_id: int):
    token = websocket.cookies.get(COOKIE_NAME)
    if not token:
        await websocket.close(code=4401, reason="Not authenticated")
        return

    try:
        user_id = verify_token(token)
    except HTTPException:
        await websocket.close(code=4401, reason="Invalid session")
        return

    async with SessionLocal() as db:
        submission = await db.get(Submission, submission_id)
        if submission is None:
            await websocket.close(code=4404, reason="Submission not found")
            return
        if submission.user_id != user_id:
            await websocket.close(code=4403, reason="Forbidden")
            return
        persisted_status = submission.status.value

    await manager.connect(submission_id, websocket)
    await websocket.send_json({
        "submission_id": submission_id,
        "status": persisted_status,
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(submission_id)
    except Exception:
        manager.disconnect(submission_id)

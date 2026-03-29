from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import json
from jose import jwt
from datetime import datetime

from app.websocket.connection_manager import manager
from app.utils.security import SECRET_KEY, ALGORITHM
from app.core.database import SessionLocal
from app.models.user import User

async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    client_type: str = "general"
):
    user = None
    user_id = None
    
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
            if user_id:
                db = SessionLocal()
                user = db.query(User).filter(User.id == user_id).first()
                db.close()
        except:
            pass
    
    await manager.connect(websocket, client_type, user_id)
    
    await websocket.send_json({
        "type": "connection",
        "status": "connected",
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "client_type": client_type
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")
            
            if message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
            elif message_type == "subscribe_room":
                room_id = message.get("room_id")
                if room_id:
                    await manager.subscribe_to_room(websocket, room_id)
                    await websocket.send_json({"type": "subscribed", "room_id": room_id, "timestamp": datetime.now().isoformat()})
            elif message_type == "unsubscribe_room":
                room_id = message.get("room_id")
                if room_id:
                    await manager.unsubscribe_from_room(websocket, room_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_type, user_id)

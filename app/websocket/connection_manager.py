import asyncio
from typing import Dict, Set, List, Optional
import json
from datetime import datetime
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[int, WebSocket] = {}
        self.room_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_type: str = "general", client_id: int = None):
        await websocket.accept()
        if client_type not in self.active_connections:
            self.active_connections[client_type] = set()
        self.active_connections[client_type].add(websocket)
        if client_id:
            self.user_connections[client_id] = websocket
        return True
    
    def disconnect(self, websocket: WebSocket, client_type: str = "general", client_id: int = None):
        if client_type in self.active_connections:
            self.active_connections[client_type].discard(websocket)
        if client_id and client_id in self.user_connections:
            del self.user_connections[client_id]
    
    async def broadcast_to_type(self, message: dict, client_type: str):
        if client_type in self.active_connections:
            disconnected = []
            for connection in self.active_connections[client_type]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            for connection in disconnected:
                self.active_connections[client_type].discard(connection)
    
    async def broadcast_to_room(self, message: dict, room_id: int):
        if room_id in self.room_connections:
            disconnected = []
            for connection in self.room_connections[room_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)
            for connection in disconnected:
                self.room_connections[room_id].discard(connection)
    
    async def send_to_user(self, user_id: int, message: dict):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
                return True
            except:
                del self.user_connections[user_id]
        return False
    
    async def subscribe_to_room(self, websocket: WebSocket, room_id: int):
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(websocket)
    
    async def unsubscribe_from_room(self, websocket: WebSocket, room_id: int):
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(websocket)

manager = ConnectionManager()

from datetime import datetime
from app.websocket.connection_manager import manager

async def emit_room_status_changed(room_id: int, room_number: str, old_status: str, new_status: str):
    message = {"type": "room_status_changed", "data": {"room_id": room_id, "room_number": room_number, "old_status": old_status, "new_status": new_status, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "front_desk")
    await manager.broadcast_to_type(message, "housekeeping")
    await manager.broadcast_to_room(message, room_id)

async def emit_task_created(task_id: int, task_number: str, room_id: int, room_number: str):
    message = {"type": "task_created", "data": {"task_id": task_id, "task_number": task_number, "room_id": room_id, "room_number": room_number, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "housekeeping")
    await manager.broadcast_to_type(message, "front_desk")

async def emit_task_assigned(task_id: int, task_number: str, assigned_to_id: int, assigned_to_name: str):
    message = {"type": "task_assigned", "data": {"task_id": task_id, "task_number": task_number, "assigned_to_id": assigned_to_id, "assigned_to_name": assigned_to_name, "timestamp": datetime.now().isoformat()}}
    await manager.send_to_user(assigned_to_id, message)
    await manager.broadcast_to_type(message, "housekeeping")

async def emit_task_completed(task_id: int, task_number: str, room_id: int, room_number: str):
    message = {"type": "task_completed", "data": {"task_id": task_id, "task_number": task_number, "room_id": room_id, "room_number": room_number, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "front_desk")
    await manager.broadcast_to_type(message, "housekeeping")

async def emit_reservation_created(reservation_id: int, reservation_number: str, guest_name: str):
    message = {"type": "reservation_created", "data": {"reservation_id": reservation_id, "reservation_number": reservation_number, "guest_name": guest_name, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "front_desk")

async def emit_check_in(reservation_id: int, reservation_number: str, guest_name: str, room_number: str):
    message = {"type": "check_in", "data": {"reservation_id": reservation_id, "reservation_number": reservation_number, "guest_name": guest_name, "room_number": room_number, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "front_desk")
    await manager.broadcast_to_type(message, "housekeeping")

async def emit_check_out(reservation_id: int, reservation_number: str, guest_name: str, room_number: str):
    message = {"type": "check_out", "data": {"reservation_id": reservation_id, "reservation_number": reservation_number, "guest_name": guest_name, "room_number": room_number, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "front_desk")
    await manager.broadcast_to_type(message, "housekeeping")

async def emit_payment_processed(folio_id: int, folio_number: str, amount: float, new_balance: float):
    message = {"type": "payment_processed", "data": {"folio_id": folio_id, "folio_number": folio_number, "amount": amount, "new_balance": new_balance, "timestamp": datetime.now().isoformat()}}
    await manager.broadcast_to_type(message, "front_desk")
    await manager.broadcast_to_type(message, "accounting")

async def emit_notification(user_id: int, title: str, message_text: str, notification_type: str = "info"):
    message = {"type": "notification", "data": {"title": title, "message": message_text, "type": notification_type, "timestamp": datetime.now().isoformat()}}
    await manager.send_to_user(user_id, message)

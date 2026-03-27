# test_websocket.py
import asyncio
import websockets
import json
import requests

async def test_websocket():
    print("\n🔌 WebSocket Test")
    print("="*40)
    
    # Login to get token
    print("Logging in as front desk...")
    login = requests.post("http://localhost:8000/api/v1/auth/login", json={
        "username": "frontdesk",
        "password": "Front123!"
    })
    
    if login.status_code != 200:
        print("❌ Login failed!")
        return
    
    token = login.json()["access_token"]
    print(f"✅ Login successful!")
    print(f"Token: {token[:50]}...")
    
    # Connect to WebSocket
    ws_url = f"ws://localhost:8000/ws?token={token}&client_type=front_desk"
    print(f"\nConnecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as ws:
            print("✅ Connected to WebSocket!")
            
            # Receive welcome message
            welcome = await ws.recv()
            print(f"\n📨 Welcome: {json.loads(welcome)}")
            
            # Send ping
            print("\n📤 Sending ping...")
            await ws.send(json.dumps({"type": "ping"}))
            pong = await ws.recv()
            print(f"📨 Pong: {json.loads(pong)}")
            
            # Subscribe to room
            print("\n📤 Subscribing to room 1...")
            await ws.send(json.dumps({"type": "subscribe_room", "room_id": 1}))
            sub = await ws.recv()
            print(f"📨 Subscribed: {json.loads(sub)}")
            
            # Listen for events
            print("\n🎧 Listening for events (10 seconds)...")
            print("   Try updating room status in another terminal!")
            print()
            
            for i in range(10):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(msg)
                    print(f"\n🔥 EVENT: {data['type']}")
                    print(f"   Data: {data['data']}")
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
            
            print("\n\n✅ Test completed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
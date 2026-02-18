import asyncio
import json
import websockets
import threading

CONNECTED_CLIENTS = set()

async def register_client(websocket):
    """Adds a new client to the set of connected clients."""
    CONNECTED_CLIENTS.add(websocket)
    print(f"🎀 New client connected: {websocket.remote_address}. Total: {len(CONNECTED_CLIENTS)}")

async def unregister_client(websocket):
    """Removes a client from the set of connected clients."""
    CONNECTED_CLIENTS.remove(websocket)
    print(f"👋 Client disconnected: {websocket.remote_address}. Total: {len(CONNECTED_CLIENTS)}")

async def handler(websocket, path):
    """Handles WebSocket connections, registering and unregistering clients."""
    await register_client(websocket)
    try:
        async for message in websocket:
            print(f"📨 Received from {websocket.remote_address}: {message}")
    except websockets.exceptions.ConnectionClosedError:
        pass
    finally:
        await unregister_client(websocket)

async def broadcast_update(data):
    """Sends a JSON data payload to all connected clients."""
    if CONNECTED_CLIENTS:
        message = json.dumps(data)
        tasks = [client.send(message) for client in CONNECTED_CLIENTS.copy()]
        await asyncio.gather(*tasks, return_exceptions=True)

async def push_achievement_unlocked(achievement_data):
    """Prepares and broadcasts an achievement unlock event."""
    payload = {
        "type": "ACHIEVEMENT_UNLOCKED",
        "data": achievement_data
    }
    await broadcast_update(payload)

async def push_game_change(game_data):
    """Broadcasts when a new game is detected."""
    payload = {
        "type": "GAME_CHANGED",
        "data": game_data
    }
    await broadcast_update(payload)

async def start_websocket_server(host='localhost', port=8765):
    """Starts the WebSocket server."""
    print(f"🌐 WebSocket server starting on ws://{host}:{port}...")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()

def run_server_in_thread(host='localhost', port=8765):
    """Runs the WebSocket server in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server(host, port))

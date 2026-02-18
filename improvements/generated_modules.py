===websocket_server.py===
import asyncio
import json
import websockets
import threading

CONNECTED_CLIENTS = set()

async def register_client(websocket):
    """Adds a new client to the set of connected clients."""
    CONNECTED_CLIENTS.add(websocket)
    print(f"New client connected: {websocket.remote_address}. Total clients: {len(CONNECTED_CLIENTS)}")

async def unregister_client(websocket):
    """Removes a client from the set of connected clients."""
    CONNECTED_CLIENTS.remove(websocket)
    print(f"Client disconnected: {websocket.remote_address}. Total clients: {len(CONNECTED_CLIENTS)}")

async def handler(websocket, path):
    """Handles WebSocket connections, registering and unregistering clients."""
    await register_client(websocket)
    try:
        # Keep the connection alive, listening for messages (if any)
        async for message in websocket:
            # For now, we just print any message received.
            print(f"Received message from {websocket.remote_address}: {message}")
    except websockets.exceptions.ConnectionClosedError:
        pass  # Handle client disconnection gracefully
    finally:
        await unregister_client(websocket)

async def broadcast_update(data):
    """Sends a JSON data payload to all connected clients."""
    if CONNECTED_CLIENTS:
        message = json.dumps(data)
        # The copy is needed because the set can be modified during iteration
        tasks = [client.send(message) for client in CONNECTED_CLIENTS]
        await asyncio.gather(*tasks, return_exceptions=True)

async def push_achievement_unlocked(achievement_data):
    """Prepares and broadcasts an achievement unlock event."""
    payload = {
        "type": "ACHIEVEMENT_UNLOCKED",
        "data": achievement_data
    }
    await broadcast_update(payload)

async def start_websocket_server(host='localhost', port=8765):
    """Starts the WebSocket server."""
    print(f"Starting WebSocket server on ws://{host}:{port}...")
    async with websockets.serve(handler, host, port):
        await asyncio.Future()  # Run forever

def run_server_in_thread(host='localhost', port=8765):
    """Runs the WebSocket server in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_websocket_server(host, port))
    loop.close()

def main():
    """Main function to start the server thread."""
    # This function is for standalone testing.
    # In the Flask app, you would import and call run_server_in_thread.
    server_thread = threading.Thread(target=run_server_in_thread, daemon=True)
    server_thread.start()
    print("WebSocket server thread started.")
    # Keep the main thread alive to see logs
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("Shutting down.")

if __name__ == "__main__":
    main()

===streamerbot_handler.py===
from flask import Blueprint, request, jsonify

# Assume these functions exist in the main app and provide necessary data
# You would need to import them from your application's modules
def get_current_game_progress():
    # Placeholder: returns dict with game progress
    return {"game": "Cyberpunk 2077", "completed": 50, "total": 77}

def get_pinned_achievement():
    # Placeholder: returns dict of the currently hunted achievement
    return {"name": "V for Vendetta", "description": "Find all of V's graffiti.", "global_percent": 2.1}

def get_recent_achievements(count=3):
    # Placeholder: returns a list of the last few achievements
    return [
        {"name": "The Fool", "description": "Finish the tutorial.", "global_percent": 95.2},
        {"name": "The Lovers", "description": "Complete a romance.", "global_percent": 45.8},
        {"name": "The Hermit", "description": "Find the secret location.", "global_percent": 8.3},
    ]


streamerbot_bp = Blueprint('streamerbot_handler', __name__)

def format_chat_message(message):
    """Formats a message payload for a Streamer.bot 'Send Message to Channel' action."""
    return jsonify({
        "actions": [{
            "name": "Send Message to Channel",
            "args": {
                "message": message
            }
        }]
    })

@streamerbot_bp.route('/webhook/streamerbot', methods=['POST'])
def handle_webhook():
    """Receives and processes events from Streamer.bot."""
    payload = request.json
    event_type = payload.get('event', {}).get('type')
    
    if event_type == 'ChatMessage':
        message = payload['data'].get('message', {}).get('message', '').lower().strip()
        
        if message == '!progress':
            progress = get_current_game_progress()
            response_msg = f"Current game: {progress['game']}. We've unlocked {progress['completed']} of {progress['total']} achievements!"
            return format_chat_message(response_msg)

        elif message == '!hunter':
            pinned = get_pinned_achievement()
            response_msg = f"Achievement Hunt: '{pinned['name']}' ({pinned['global_percent']}%). Description: {pinned['description']}"
            return format_chat_message(response_msg)

        elif message == '!recent':
            recents = get_recent_achievements(3)
            response_msg = "Last 3 unlocks: " + " | ".join([f"'{ach['name']}' ({ach['global_percent']}%)" for ach in recents])
            return format_chat_message(response_msg)

    elif event_type == 'AchievementUnlocked': # A custom event you would trigger
        achievement = payload.get('data', {})
        global_percent = achievement.get('global_percent', 100)
        
        if 0 < global_percent < 5:
            response_msg = f"🎉 RARE UNLOCK! 🎉 We just got '{achievement['name']}' which only {global_percent}% of players have! LFG!"
            return format_chat_message(response_msg)

    # Return a 204 No Content if the event is not handled
    return '', 204

# Example of how you might trigger the achievement event from your main app
# This function would be called when your Steam poller finds a new achievement
def trigger_rare_achievement_announcement(achievement_data):
    """
    This is a conceptual function. In your real app, you would make an
    HTTP POST request to your Streamer.bot instance to trigger a custom event.
    The payload would look like:
    {
      "event": { "type": "AchievementUnlocked" },
      "data": achievement_data
    }
    This function is a placeholder for that logic.
    """
    print(f"Logic to trigger Streamer.bot event for achievement: {achievement_data['name']}")
    # Here you'd use requests.post(streamerbot_url, json=payload)

===sound_manager.py===
class SoundManager:
    """Manages sound playback based on achievement rarity."""

    def __init__(self):
        """Initializes the rarity tiers and their sound configurations."""
        self.tiers = [
            {
                "name": "legendary",
                "threshold": 1.0,
                "sound_url": "https://example.com/sounds/legendary_unlock.mp3",
                "volume_multiplier": 1.2
            },
            {
                "name": "ultra_rare",
                "threshold": 5.0,
                "sound_url": "https://example.com/sounds/ultra_rare_unlock.mp3",
                "volume_multiplier": 1.1
            },
            {
                "name": "rare",
                "threshold": 20.0,
                "sound_url": "https://example.com/sounds/rare_unlock.mp3",
                "volume_multiplier": 1.0
            },
            {
                "name": "uncommon",
                "threshold": 50.0,
                "sound_url": "https://example.com/sounds/uncommon_unlock.mp3",
                "volume_multiplier": 0.9
            },
            {
                "name": "common",
                "threshold": 100.0,
                "sound_url": "https://example.com/sounds/common_unlock.mp3",
                "volume_multiplier": 0.8
            }
        ]

    def get_sound_for_rarity(self, percent):
        """
        Determines the appropriate sound configuration for a given rarity percentage.

        Args:
            percent (float): The global unlock percentage of the achievement.

        Returns:
            dict: A dictionary containing the 'url' and 'volume' for the sound.
        """
        if percent < 0:
            percent = 100.0 # Default to common if data is invalid

        for tier in self.tiers:
            if percent <= tier["threshold"]:
                return {
                    "url": tier["sound_url"],
                    "volume": tier["volume_multiplier"]
                }
        
        # Fallback to the last tier (common) if something goes wrong
        return {
            "url": self.tiers[-1]["sound_url"],
            "volume": self.tiers[-1]["volume_multiplier"]
        }

    def play_achievement_sound(self, achievement_data):
        """
        Selects a sound based on achievement data and returns its configuration.

        In a real app, this might trigger a browser source event or an OBS action.
        Here, it simply returns the configuration data.

        Args:
            achievement_data (dict): A dictionary representing the unlocked achievement.
                                     Must contain a 'global_percent' key.

        Returns:
            dict: The sound configuration (url, volume) for the achievement's rarity.
        """
        global_percent = achievement_data.get("global_percent", 100.0)
        sound_config = self.get_sound_for_rarity(global_percent)
        
        print(f"Playing sound for '{achievement_data.get('name', 'Unknown')}' "
              f"({global_percent}% rarity). Sound: {sound_config['url']}, "
              f"Volume: {sound_config['volume']}")
              
        return sound_config

# Example Usage:
if __name__ == "__main__":
    sound_manager = SoundManager()

    common_ach = {"name": "First Step", "global_percent": 75.5}
    uncommon_ach = {"name": "Explorer", "global_percent": 42.1}
    rare_ach = {"name": "Collector", "global_percent": 15.8}
    ultra_rare_ach = {"name": "Perfectionist", "global_percent": 3.2}
    legendary_ach = {"name": "Completionist", "global_percent": 0.9}
    no_percent_ach = {"name": "Glitched Achievement"}

    print("--- Testing Sound Manager ---")
    sound_manager.play_achievement_sound(common_ach)
    sound_manager.play_achievement_sound(uncommon_ach)
    sound_manager.play_achievement_sound(rare_ach)
    sound_manager.play_achievement_sound(ultra_rare_ach)
    sound_manager.play_achievement_sound(legendary_ach)
    sound_manager.play_achievement_sound(no_percent_ach)
    print("--------------------------")

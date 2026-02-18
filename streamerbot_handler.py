from flask import Blueprint, request, jsonify
from functools import wraps

streamerbot_bp = Blueprint('streamerbot_handler', __name__)

# Global reference to app state - set during initialization
_app_state = None
_app_config = None

def init_streamerbot(state, config):
    """Initialize with references to app state and config."""
    global _app_state, _app_config
    _app_state = state
    _app_config = config

def format_chat_message(message):
    """Formats a message for Streamer.bot 'Send Message to Channel' action."""
    return jsonify({
        "actions": [{
            "name": "Send Message to Channel",
            "args": {
                "message": message
            }
        }]
    })

def get_current_game_progress():
    """Gets current game progress from app state."""
    if not _app_state or not _app_config:
        return {"game": "No Game", "completed": 0, "total": 0}
    
    cached = _app_state.get('cached_response')
    if cached and cached.get('status') == 'active':
        return {
            "game": cached.get('game', 'Unknown'),
            "completed": int(cached.get('stats', '0 / 0').split(' / ')[0]),
            "total": int(cached.get('stats', '0 / 0').split(' / ')[1]) if ' / ' in cached.get('stats', '') else 0
        }
    return {"game": "No Game", "completed": 0, "total": 0}

def get_pinned_achievement():
    """Gets the currently pinned/hunter achievement."""
    if not _app_config:
        return None
    
    cfg = _app_config()
    cached = _app_state.get('cached_response') if _app_state else None
    if cached and cached.get('hunter_target'):
        target = cached['hunter_target']
        return {
            "name": target.get('name', 'Unknown'),
            "description": target.get('desc', 'No description'),
            "global_percent": target.get('rarity', 0)
        }
    return None

def get_recent_achievements(count=3):
    """Gets recent achievements from app state."""
    if not _app_state:
        return []
    
    cached = _app_state.get('cached_response')
    if cached and cached.get('recent'):
        recent = cached['recent'][-count:]
        return [
            {
                "name": a.get('name', 'Unknown'),
                "global_percent": a.get('rarity', 100)
            }
            for a in recent
        ]
    return []

@streamerbot_bp.route('/webhook/streamerbot', methods=['POST'])
def handle_webhook():
    """Receives and processes events from Streamer.bot."""
    payload = request.json or {}
    event_type = payload.get('event', {}).get('type') if payload.get('event') else None
    
    # Chat commands
    if event_type == 'ChatMessage':
        message = payload.get('data', {}).get('message', {}).get('message', '').lower().strip()
        username = payload.get('data', {}).get('message', {}).get('displayName', 'Viewer')
        
        if message == '!progress':
            progress = get_current_game_progress()
            if progress['game'] != "No Game":
                response_msg = f"📊 Current Game: {progress['game']} | Progress: {progress['completed']}/{progress['total']} achievements"
            else:
                response_msg = "📊 No game is currently running!"
            return format_chat_message(response_msg)

        elif message == '!hunter':
            pinned = get_pinned_achievement()
            if pinned:
                response_msg = f"🎯 Hunter Target: '{pinned['name']}' ({pinned['global_percent']}% of players) | {pinned['description'][:50]}..."
            else:
                response_msg = "🎯 No achievement is currently pinned! Use the control dock to set a target."
            return format_chat_message(response_msg)

        elif message == '!recent':
            recents = get_recent_achievements(3)
            if recents:
                ach_list = " | ".join([f"'{a['name']}' ({a['global_percent']}%)" for a in recents])
                response_msg = f"🏆 Recent Unlocks: {ach_list}"
            else:
                response_msg = "🏆 No recent achievements!"
            return format_chat_message(response_msg)

    # Return 204 for unhandled events
    return '', 204

def check_and_announce_rare(achievement_data, rarity_percent):
    """
    Call this when a new achievement is unlocked.
    Returns a formatted message for rare achievements, or None for common ones.
    """
    if rarity_percent < 5.0:
        return f"🎉 RARE ACHIEVEMENT! '{achievement_data.get('name', 'Unknown')}' - Only {rarity_percent}% of players have this!"
    elif rarity_percent < 1.0:
        return f"👑 LEGENDARY! '{achievement_data.get('name', 'Unknown')}' - Only {rarity_percent}% of players! INSANE!"
    return None

import requests
import psutil
import time
import os
import sys
import json
import webbrowser
import winreg
import colorsys
import threading
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

# --- NEW IMPROVEMENTS IMPORTS ---
from websocket_server import run_server_in_thread, push_achievement_unlocked, push_game_change
from streamerbot_handler import streamerbot_bp, init_streamerbot, check_and_announce_rare
from sound_manager import SoundManager

# Start WebSocket server in background thread
ws_thread = threading.Thread(target=run_server_in_thread, args=('localhost', 8765), daemon=True)
ws_thread.start()

# Initialize sound manager
sound_mgr = SoundManager(base_volume=0.5)

try:
    from PIL import Image
    import io
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

app = Flask(__name__)
CORS(app)

# Register Streamer.bot blueprint
app.register_blueprint(streamerbot_bp)

# Initialize Streamer.bot handler with app state
init_streamerbot(state, load_config)

# --- ROBUST PATH FINDER ---
def get_resource_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, filename)

CONFIG_FILE = get_resource_path('config.json')

# --- HELPERS ---
def load_config():
    defaults = {
        "api_key": "", 
        "steam_id": "", 
        "show_standby": True, 
        "play_sound": True, 
        "volume": 50, 
        "manual_id": "", 
        "theme_mode": "dynamic", 
        "custom_color": "#66c0f4",
        "overrides": {}, 
        "pins": {}
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            try: 
                saved = json.load(f)
                # Only keep relevant keys, filter out old Xbox junk
                return {k: saved.get(k, v) for k, v in defaults.items()}
            except: pass
    return defaults

def save_config(cfg):
    current = load_config()
    current.update(cfg)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(current, f)

def enforce_brightness(hex_color, min_brightness=0.6):
    hex_color = str(hex_color).lstrip('#')
    if len(hex_color) != 6: return "#66c0f4"
    try:
        r, g, b = int(hex_color[0:2], 16)/255.0, int(hex_color[2:4], 16)/255.0, int(hex_color[4:6], 16)/255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if l < min_brightness: l = min_brightness
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))
    except: return "#66c0f4"

def get_theme_color(appid):
    if not HAS_PILLOW: return "#66c0f4"
    try:
        img_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
        response = requests.get(img_url, timeout=2)
        img = Image.open(io.BytesIO(response.content)).resize((50, 50)).convert('RGB')
        pixels = list(img.getdata())
        r, g, b = 0, 0, 0
        for pix in pixels: r += pix[0]; g += pix[1]; b += pix[2]
        return enforce_brightness("#{:02x}{:02x}{:02x}".format(int(r/len(pixels)), int(g/len(pixels)), int(b/len(pixels))))
    except: return "#66c0f4"

def get_active_steam_appid(api_key, steam_id):
    # 1. Registry (Fastest Local Check)
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam\ActiveProcess")
        appid, _ = winreg.QueryValueEx(key, "ActiveProcessId")
        if appid != 0: return str(appid)
    except: pass
    
    # 2. Web API (Fallback)
    try:
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
        res = requests.get(url, timeout=2).json()
        players = res.get('response', {}).get('players', [])
        if players and 'gameid' in players[0]: return str(players[0]['gameid'])
    except: pass
    return None

def format_duration(seconds):
    if seconds < 60: return "Just Started"
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"

# --- ROUTES ---
state = {
    "last_api_update": 0, 
    "cached_response": None, 
    "current_appid": None, 
    "session_start": 0,
    "test_trigger_time": 0,
    "start_count": -1 
}

@app.route('/')
def home(): return send_file(get_resource_path('index.html'))

@app.route('/dock')
def dock(): return send_file(get_resource_path('dock.html'))

@app.route('/reset', methods=['POST'])
def reset_settings():
    if os.path.exists(CONFIG_FILE): os.remove(CONFIG_FILE)
    return jsonify({"status": "success"})

@app.route('/restart_session', methods=['POST'])
def restart_session():
    global state
    state['session_start'] = time.time()
    state['start_count'] = -1
    state['cached_response'] = None
    return jsonify({"status": "success"})

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Terminates the application immediately."""
    os._exit(0)
    return jsonify({"status": "shutdown"})

@app.route('/trigger_test', methods=['POST'])
def trigger_test():
    global state
    state['test_trigger_time'] = time.time()
    return jsonify({"status": "success"})

@app.route('/set_name_override', methods=['POST'])
def set_name_override():
    data = request.json
    appid = data.get('appid')
    custom_name = data.get('name')
    cfg = load_config()
    if 'overrides' not in cfg: cfg['overrides'] = {}
    if custom_name: cfg['overrides'][str(appid)] = custom_name
    elif str(appid) in cfg['overrides']: del cfg['overrides'][str(appid)]
    save_config(cfg)
    global state
    state['cached_response'] = None
    return jsonify({"status": "success"})

@app.route('/set_pin', methods=['POST'])
def set_pin():
    data = request.json
    appid = str(data.get('appid'))
    ach_id = data.get('ach_id')
    cfg = load_config()
    if 'pins' not in cfg: cfg['pins'] = {}
    if ach_id: cfg['pins'][appid] = ach_id
    elif appid in cfg['pins']: del cfg['pins'][appid]
    save_config(cfg)
    global state
    state['cached_response'] = None
    return jsonify({"status": "success"})

@app.route('/test_connection', methods=['POST'])
def test_connection():
    data = request.json
    try:
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={data['api_key']}&steamids={data['steam_id']}"
        res = requests.get(url, timeout=5).json()
        players = res.get('response', {}).get('players', [])
        if players: return jsonify({"status": "success", "persona": players[0]['personaname']})
        return jsonify({"status": "error", "message": "Check API Key or ID"})
    except: return jsonify({"status": "error", "message": "Connection Failed"})

@app.route('/settings', methods=['POST'])
def update_settings():
    save_config(request.json)
    global state
    state['cached_response'] = None
    return jsonify({"status": "success"})

@app.route('/data')
def get_data():
    global state
    cfg = load_config()
    now = time.time()

    # TEST MODE
    if now - state['test_trigger_time'] < 5:
        return jsonify({
            "status": "active",
            "game": "Test Alert Mode",
            "progress": 50,
            "stats": "TEST / TEST",
            "recent": [{"icon": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/apps/440/e3f595b9255502d6861543c74a38237932d84d72.jpg", "name": "Test Achievement", "desc": "This is a test of the alert system."}],
            "duration": "00:00",
            "session_unlocks": 3,
            "theme": "#66c0f4",
            "play_sound": True,
            "volume": cfg.get('volume', 50)
        })

    if not cfg['api_key'] or not cfg['steam_id']: 
        return jsonify({"status": "setup_required"})

    # Detection Logic
    if cfg.get('manual_id'): active_appid = str(cfg['manual_id'])
    else: active_appid = get_active_steam_appid(cfg['api_key'], cfg['steam_id'])

    # Session Timer Management
    if active_appid:
        if state['current_appid'] != active_appid:
            state['current_appid'] = active_appid
            state['session_start'] = now
            state['start_count'] = -1
            state['cached_response'] = None
    else:
        state['current_appid'] = None
        state['session_start'] = 0

    # Cache Check (3s)
    if state['cached_response'] and (now - state['last_api_update'] < 3):
        if state['cached_response']['status'] == "active":
            state['cached_response']['duration'] = format_duration(now - state['session_start'])
            state['cached_response']['play_sound'] = cfg.get('play_sound', True)
            state['cached_response']['volume'] = cfg.get('volume', 50)
            
            # Hot update custom theme
            if cfg.get('theme_mode') == 'custom':
                state['cached_response']['theme'] = cfg.get('custom_color') or '#66c0f4'
            elif 'steam_theme_cache' in state and active_appid:
                 state['cached_response']['theme'] = state['steam_theme_cache']
        return jsonify(state['cached_response'])

    try:
        final_res = None

        if active_appid:
            u_url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={active_appid}&key={cfg['api_key']}&steamid={cfg['steam_id']}"
            s_url = f"https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?appid={active_appid}&key={cfg['api_key']}"
            r_url = f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid={active_appid}"

            u_data = requests.get(u_url, timeout=4).json()
            s_data = requests.get(s_url, timeout=4).json()
            try:
                r_data = requests.get(r_url, timeout=4).json()
                rarity_map = {a['name']: float(a['percent']) for a in r_data['achievementpercentages']['achievements']}
            except: rarity_map = {}

            original_name = s_data.get('game', {}).get('gameName', "Steam Game")
            game_name = cfg.get('overrides', {}).get(str(active_appid), original_name)

            schema_ach = s_data.get('game', {}).get('availableGameStats', {}).get('achievements', [])
            icon_map = {a['name']: a['icon'] for a in schema_ach}
            gray_icon_map = {a['name']: a.get('icongray', a['icon']) for a in schema_ach}
            desc_map = {a['name']: a.get('description', 'No description available.') for a in schema_ach}
            name_map = {a['name']: a.get('displayName', a['name']) for a in schema_ach}

            player_ach = u_data.get('playerstats', {}).get('achievements', [])
            unlocked = []
            locked_list = []
            pinned_id = cfg.get('pins', {}).get(str(active_appid))
            hunter_target = None

            for a in player_ach:
                apiname = a['apiname']
                rarity = round(rarity_map.get(apiname, 0), 1)

                if a.get('achieved') == 1:
                    unlock_time = a.get('unlocktime', 0)
                    if apiname in icon_map: 
                        unlocked.append({
                            "icon": icon_map[apiname],
                            "name": name_map.get(apiname, "Unknown"),
                            "desc": desc_map.get(apiname, ""),
                            "timestamp": unlock_time,
                            "rarity": rarity
                        })
                else:
                    if apiname in name_map:
                        locked_list.append({"id": apiname, "name": name_map[apiname]})
                    if pinned_id and apiname == pinned_id:
                        hunter_target = {
                            "name": name_map.get(apiname, "Unknown"),
                            "desc": desc_map.get(apiname, ""),
                            "icon": gray_icon_map.get(apiname, ""),
                            "rarity": rarity
                        }

            # Sort: Newest Last
            unlocked.sort(key=lambda x: x['timestamp'])

            total = len(player_ach)
            count = len(unlocked)
            percent = int((count / total) * 100) if total > 0 else 0
            
            # SESSION LOGIC
            if state['start_count'] == -1: state['start_count'] = count
            session_unlocks = max(0, count - state['start_count'])
            
            # --- NEW ACHIEVEMENT DETECTION & WEBSOCKET BROADCAST ---
            # Check for newly unlocked achievements since last update
            prev_unlocked_ids = set()
            if state.get('cached_response') and state['cached_response'].get('recent'):
                prev_unlocked_ids = {a['name'] for a in state['cached_response']['recent']}
            
            current_unlocked_ids = {a['name'] for a in unlocked}
            new_achievements = [a for a in unlocked if a['name'] not in prev_unlocked_ids]
            
            # Broadcast new achievements via WebSocket
            for ach in new_achievements:
                # Push to WebSocket clients
                push_achievement_unlocked(ach)
                
                # Check for rare achievement announcement
                rare_msg = check_and_announce_rare(ach, ach.get('rarity', 100))
                if rare_msg:
                    print(f"🎉 RARE UNLOCK: {rare_msg}")
                    # Note: To actually send to chat, you'd POST to Streamer.bot
                    # This prints to console for now - Streamer.bot can monitor logs
            
            # --- GAME CHANGE DETECTION ---
            if state.get('cached_response') and state['cached_response'].get('appid') != active_appid:
                # Game changed - broadcast
                push_game_change({
                    "appid": active_appid,
                    "name": game_name,
                    "art": f"https://cdn.akamai.steamstatic.com/steam/apps/{active_appid}/header.jpg"
                })
            # --------------------------------------------------------
            
            # --- SOUND CONFIG BASED ON RARITY ---
            # Add sound config for most recent achievement
            sound_config = None
            if unlocked:
                sound_config = sound_mgr.play_achievement_sound(unlocked[-1])
            # ------------------------------------
            
            dynamic_theme = get_theme_color(active_appid)
            state['steam_theme_cache'] = dynamic_theme 

            final_res = {
                "status": "active",
                "appid": active_appid,
                "game": game_name,
                "progress": percent,
                "stats": f"{count} / {total}",
                "session_unlocks": session_unlocks,
                "recent": unlocked[-5:], 
                "locked_list": sorted(locked_list, key=lambda x: x['name']),
                "hunter_target": hunter_target,
                "duration": format_duration(now - state['session_start']),
                "theme": dynamic_theme, 
                "game_art": f"https://cdn.akamai.steamstatic.com/steam/apps/{active_appid}/header.jpg",
                "is_100": percent == 100,
                "play_sound": cfg.get('play_sound', True),
                "volume": cfg.get('volume', 50),
                "platform": "steam",
                "sound_config": sound_config  # New: rarity-based sound config
            }

        if final_res and final_res['status'] == 'active':
            if cfg.get('theme_mode') == 'custom':
                final_res['theme'] = cfg.get('custom_color') or '#66c0f4'

        if not final_res:
            if not cfg.get('show_standby', True): final_res = {"status": "hidden"}
            else:
                summary_url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={cfg['api_key']}&steamids={cfg['steam_id']}"
                summary = requests.get(summary_url, timeout=4).json()['response']['players'][0]
                standby_theme = cfg.get('custom_color') or '#66c0f4' if cfg.get('theme_mode') == 'custom' else "#66c0f4"
                final_res = {
                    "status": "standby",
                    "persona": summary.get('personaname', 'Player'),
                    "avatar": summary.get('avatarfull', ''),
                    "theme": standby_theme
                }
        
        state['cached_response'] = final_res
        state['last_api_update'] = now
        return jsonify(final_res)

    except Exception as e:
        print(f"Error in main loop: {e}")
        if state['cached_response']: return jsonify(state['cached_response'])
        return jsonify({"status": "error", "message": "Connecting..."})

if __name__ == '__main__':
    # Launch browser only if config is missing (First Run)
    if not os.path.exists(CONFIG_FILE):
         print("First run detected. Opening setup...")
         webbrowser.open("http://localhost:5000")
         
    app.run(port=5000, debug=False, use_reloader=False)
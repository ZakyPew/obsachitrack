import requests
from typing import Dict, List, Optional
from datetime import datetime
import os
import sys

sys.path.append('/opt/streamtracker/backend')

STEAM_API_KEY = os.getenv("STEAM_API_KEY", "")

def get_steam_user_info(steam_id: str) -> dict:
    """Get user profile from Steam API"""
    if not STEAM_API_KEY:
        return {"personaname": f"user_{steam_id}", "avatarfull": ""}
    
    try:
        url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        resp = requests.get(url, params={"key": STEAM_API_KEY, "steamids": steam_id}, timeout=10)
        data = resp.json()
        players = data.get("response", {}).get("players", [])
        return players[0] if players else {}
    except Exception as e:
        print(f"Steam API error: {e}")
        return {"personaname": f"user_{steam_id}", "avatarfull": ""}

def get_active_steam_game(api_key: str, steam_id: str) -> Optional[str]:
    """Get currently playing game appid"""
    try:
        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        resp = requests.get(url, params={"key": api_key, "steamids": steam_id}, timeout=5)
        data = resp.json()
        players = data.get('response', {}).get('players', [])
        if players and 'gameid' in players[0]:
            return str(players[0]['gameid'])
    except Exception as e:
        print(f"Error getting active game: {e}")
    return None

def get_steam_store_data(app_id: str) -> dict:
    """Fetch game data from Steam Store API including artwork"""
    try:
        url = f"https://store.steampowered.com/api/appdetails"
        resp = requests.get(url, params={"appids": app_id}, timeout=5)
        data = resp.json()
        
        if data and str(app_id) in data:
            app_data = data[str(app_id)]
            if app_data.get('success'):
                return {
                    'name': app_data['data'].get('name', f"Game {app_id}"),
                    'header_image': app_data['data'].get('header_image', ''),
                    'background': app_data['data'].get('background', ''),
                }
    except Exception as e:
        print(f"Error fetching Steam store data: {e}")
    
    return {'name': f"Game {app_id}", 'header_image': '', 'background': ''}

def get_game_name_with_overrides(app_id: str, user_id: int = None, db = None) -> str:
    """
    Get game name with support for user and global overrides.
    Priority: User override > Global override > Steam API name
    """
    from database import SessionLocal, GlobalGameName, UserGameName
    
    # Get Steam API name first (as fallback)
    steam_name = get_steam_game_name_from_api(app_id)
    
    if db is None:
        db = SessionLocal()
        close_db = True
    else:
        close_db = False
    
    try:
        # 1. Check user override first
        if user_id:
            user_override = db.query(UserGameName).filter_by(
                user_id=user_id, app_id=app_id
            ).first()
            if user_override:
                return user_override.custom_name
        
        # 2. Check global override
        global_override = db.query(GlobalGameName).filter_by(app_id=app_id).first()
        if global_override:
            return global_override.proper_name
        
        # 3. Return Steam API name
        return steam_name
    finally:
        if close_db:
            db.close()

def get_steam_game_name_from_api(app_id: str) -> str:
    """Fetch game name from Steam API (for fallback)"""
    try:
        # Try to get from store API
        url = f"https://store.steampowered.com/api/appdetails"
        resp = requests.get(url, params={"appids": app_id}, timeout=5)
        data = resp.json()
        
        if data and str(app_id) in data:
            app_data = data[str(app_id)]
            if app_data.get('success'):
                return app_data['data'].get('name', f"Game {app_id}")
    except Exception as e:
        print(f"Error fetching game name from store: {e}")
    
    return f"Game {app_id}"

def set_user_game_name_override(user_id: int, app_id: str, custom_name: str) -> dict:
    """Set a custom game name for a user"""
    from database import SessionLocal, UserGameName
    
    db = SessionLocal()
    try:
        # Check if override already exists
        override = db.query(UserGameName).filter_by(
            user_id=user_id, app_id=app_id
        ).first()
        
        if override:
            override.custom_name = custom_name
            override.updated_at = datetime.utcnow()
        else:
            override = UserGameName(
                user_id=user_id,
                app_id=app_id,
                custom_name=custom_name
            )
            db.add(override)
        
        db.commit()
        return {"status": "success", "message": "Custom name saved"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def delete_user_game_name_override(user_id: int, app_id: str) -> dict:
    """Delete a user's custom game name override"""
    from database import SessionLocal, UserGameName
    
    db = SessionLocal()
    try:
        override = db.query(UserGameName).filter_by(
            user_id=user_id, app_id=app_id
        ).first()
        
        if override:
            db.delete(override)
            db.commit()
            return {"status": "success", "message": "Custom name removed"}
        else:
            return {"status": "error", "message": "No custom name found"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def get_user_game_name_override(user_id: int, app_id: str) -> Optional[str]:
    """Get a user's custom game name if it exists"""
    from database import SessionLocal, UserGameName
    
    db = SessionLocal()
    try:
        override = db.query(UserGameName).filter_by(
            user_id=user_id, app_id=app_id
        ).first()
        return override.custom_name if override else None
    finally:
        db.close()

def fetch_achievements(api_key: str, steam_id: str, app_id: str, user_id: int = None) -> dict:
    """
    Fetch achievements for a game.
    Returns dict with game info, achievements list, progress.
    """
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get user achievements
        user_url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
        user_resp = requests.get(user_url, params={
            "appid": app_id,
            "key": api_key,
            "steamid": steam_id
        }, timeout=10)
        user_data = user_resp.json()
        
        # Get schema (names, icons, descriptions)
        schema_url = f"https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/"
        schema_resp = requests.get(schema_url, params={
            "appid": app_id,
            "key": api_key
        }, timeout=10)
        schema_data = schema_resp.json()
        
        # Get rarity data
        try:
            rarity_url = f"https://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/"
            rarity_resp = requests.get(rarity_url, params={"gameid": app_id}, timeout=10)
            rarity_data = rarity_resp.json()
            rarity_map = {
                a['name']: float(a['percent']) 
                for a in rarity_data.get('achievementpercentages', {}).get('achievements', [])
            }
        except:
            rarity_map = {}
        
        # Get Steam Store data for artwork
        store_data = get_steam_store_data(app_id)
        
        # Parse game info - USE OVERRIDES
        steam_api_name = schema_data.get('game', {}).get('gameName', store_data.get('name', 'Unknown Game'))
        game_name = get_game_name_with_overrides(app_id, user_id, db)
        
        schema_achievements = schema_data.get('game', {}).get('availableGameStats', {}).get('achievements', [])
        
        # Build icon/name maps
        icon_map = {a['name']: a['icon'] for a in schema_achievements}
        name_map = {a['name']: a.get('displayName', a['name']) for a in schema_achievements}
        desc_map = {a['name']: a.get('description', '') for a in schema_achievements}
        
        # Parse user achievements
        player_achievements = user_data.get('playerstats', {}).get('achievements', [])
        
        unlocked = []
        locked = []
        
        for ach in player_achievements:
            apiname = ach['apiname']
            ach_data = {
                'id': apiname,
                'name': name_map.get(apiname, apiname),
                'description': desc_map.get(apiname, ''),
                'icon': icon_map.get(apiname, ''),
                'unlocked': ach['achieved'] == 1,
                'unlock_time': ach.get('unlocktime'),
                'rarity': round(rarity_map.get(apiname, 0), 1)
            }
            
            if ach['achieved'] == 1:
                unlocked.append(ach_data)
            else:
                locked.append(ach_data)
        
        # Sort unlocked by time (most recent first)
        unlocked.sort(key=lambda x: x.get('unlock_time', 0), reverse=True)
        
        total = len(player_achievements)
        completed = len(unlocked)
        
        return {
            'game_id': app_id,
            'game_name': game_name,
            'steam_api_name': steam_api_name,
            'header_image': store_data.get('header_image', ''),
            'background': store_data.get('background', ''),
            'total': total,
            'unlocked': completed,
            'locked': len(locked),
            'completion': round((completed / total * 100), 1) if total > 0 else 0,
            'achievements': unlocked + locked,
            'recent': unlocked[:5],
            'rarity_map': rarity_map,
            'has_custom_name': game_name != steam_api_name
        }
        
    except Exception as e:
        print(f"Error fetching achievements: {e}")
        # Fallback with store data
        store_data = get_steam_store_data(app_id)
        return {
            'game_id': app_id,
            'game_name': get_game_name_with_overrides(app_id, user_id, db),
            'steam_api_name': store_data.get('name', 'Unknown Game'),
            'header_image': store_data.get('header_image', ''),
            'background': store_data.get('background', ''),
            'total': 0,
            'unlocked': 0,
            'locked': 0,
            'completion': 0,
            'achievements': [],
            'recent': [],
            'error': str(e)
        }
    finally:
        db.close()

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import secrets
from datetime import datetime
import requests

import sys
sys.path.append('/opt/streamtracker/backend')

from database import SessionLocal, User, ApiKey
from auth.steam import get_current_user
from services.steam_api import (
    set_user_game_name_override, 
    delete_user_game_name_override,
    get_user_game_name_override
)

api_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SteamApiKey(BaseModel):
    api_key: str

class GameNameOverride(BaseModel):
    app_id: str
    custom_name: str

@api_router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": user.id,
        "steam_id": user.steam_id,
        "username": user.username,
        "avatar": user.avatar,
        "is_premium": user.is_premium,
        "has_steam_api_key": bool(user.steam_api_key)
    }

@api_router.post("/steam-api-key")
def save_steam_api_key(data: SteamApiKey, user: User = Depends(get_current_user)):
    """Save user's Steam API key - Steam ID already known from OAuth"""
    # Use a fresh session to update the user
    db = SessionLocal()
    try:
        # Re-fetch the user in this session
        db_user = db.query(User).filter(User.id == user.id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Test the credentials
        try:
            test_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
            resp = requests.get(test_url, params={
                "key": data.api_key,
                "steamids": db_user.steam_id
            }, timeout=10)
            result = resp.json()
            players = result.get("response", {}).get("players", [])
            if not players:
                raise HTTPException(status_code=400, detail="Invalid API key - couldn't fetch user data")
            
            # Verify it matches the logged-in user
            if str(players[0].get("steamid")) != str(db_user.steam_id):
                raise HTTPException(status_code=400, detail="API key doesn't match your Steam account")
                
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=400, detail=f"Failed to verify API key: {str(e)}")
        
        # Save to user
        db_user.steam_api_key = data.api_key
        db.commit()
        
        return {
            "status": "success", 
            "message": "Steam API key saved",
            "steam_id": db_user.steam_id,
            "username": db_user.username
        }
    finally:
        db.close()

@api_router.get("/api-key")
def get_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's StreamTracker API key"""
    api_key = db.query(ApiKey).filter(ApiKey.user_id == user.id, ApiKey.is_active == True).first()
    if not api_key:
        # Create new key
        api_key = ApiKey(
            user_id=user.id,
            key=f"st_{secrets.token_urlsafe(32)}",
            name="Default"
        )
        db.add(api_key)
        db.commit()
    
    return {
        "api_key": api_key.key,
        "name": api_key.name,
        "created_at": api_key.created_at,
        "last_used": api_key.last_used
    }

@api_router.post("/api-key/regenerate")
def regenerate_api_key(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate new API key"""
    # Deactivate old keys
    db.query(ApiKey).filter(ApiKey.user_id == user.id).update({"is_active": False})
    
    # Create new key
    new_key = ApiKey(
        user_id=user.id,
        key=f"st_{secrets.token_urlsafe(32)}",
        name="Default"
    )
    db.add(new_key)
    db.commit()
    
    return {"api_key": new_key.key}

@api_router.get("/overlay-url")
def get_overlay_url(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get OBS overlay URL for user"""
    api_key = db.query(ApiKey).filter(ApiKey.user_id == user.id, ApiKey.is_active == True).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="No API key found")
    
    import os
    base_url = os.getenv("BASE_URL", "http://74.208.147.236:8001")
    
    return {
        "overlay_url": f"{base_url}/overlay/{user.username}?key={api_key.key}",
        "vertical_url": f"{base_url}/overlay/{user.username}/vertical?key={api_key.key}",
        "has_steam_api_key": bool(user.steam_api_key)
    }

@api_router.post("/test-steam-api")
def test_steam_api(data: SteamApiKey, user: User = Depends(get_current_user)):
    """Test Steam API key without saving"""
    try:
        # Get player summaries
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        resp = requests.get(url, params={
            "key": data.api_key,
            "steamids": user.steam_id
        }, timeout=10)
        result = resp.json()
        players = result.get("response", {}).get("players", [])
        
        if not players:
            return {"status": "error", "message": "Invalid API key"}
        
        player = players[0]
        
        # Try to get owned games (tests API key permissions)
        games_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
        games_resp = requests.get(games_url, params={
            "key": data.api_key,
            "steamid": user.steam_id,
            "include_appinfo": 1,
            "include_played_free_games": 1
        }, timeout=10)
        games_data = games_resp.json()
        game_count = games_data.get("response", {}).get("game_count", 0)
        
        return {
            "status": "success",
            "persona": player.get("personaname"),
            "avatar": player.get("avatarfull"),
            "games_count": game_count,
            "message": f"API key valid! Found {game_count} games."
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

# === GAME NAME OVERRIDE ENDPOINTS ===

@api_router.post("/game-name-override")
def create_game_name_override(
    data: GameNameOverride, 
    user: User = Depends(get_current_user)
):
    """Set a custom game name for the current user"""
    result = set_user_game_name_override(user.id, data.app_id, data.custom_name)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@api_router.delete("/game-name-override/{app_id}")
def remove_game_name_override(
    app_id: str,
    user: User = Depends(get_current_user)
):
    """Remove a custom game name override"""
    result = delete_user_game_name_override(user.id, app_id)
    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@api_router.get("/game-name-override/{app_id}")
def get_game_name_override(
    app_id: str,
    user: User = Depends(get_current_user)
):
    """Get custom game name for a specific game"""
    custom_name = get_user_game_name_override(user.id, app_id)
    return {
        "app_id": app_id,
        "custom_name": custom_name,
        "has_override": custom_name is not None
    }

@api_router.get("/game-name-overrides")
def list_game_name_overrides(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all game name overrides for the current user"""
    from database import UserGameName
    overrides = db.query(UserGameName).filter_by(user_id=user.id).all()
    return {
        "overrides": [
            {
                "app_id": o.app_id,
                "custom_name": o.custom_name,
                "updated_at": o.updated_at.isoformat() if o.updated_at else None
            }
            for o in overrides
        ]
    }

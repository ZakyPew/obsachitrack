from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
import requests
import secrets
import urllib.parse
from sqlalchemy.orm import Session

from ..database import SessionLocal, User, ApiKey

steam_router = APIRouter()

STEAM_API_KEY = "YOUR_STEAM_API_KEY"  # Set via env var
STEAM_OPENID_URL = "https://steamcommunity.com/openid"

# For production, use environment variables
BASE_URL = "http://localhost:8000"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_api_key():
    return secrets.token_urlsafe(32)

@steam_router.get("/steam/login")
def steam_login():
    """Redirect user to Steam OpenID login"""
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": f"{BASE_URL}/auth/steam/callback",
        "openid.realm": BASE_URL,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select"
    }
    
    auth_url = f"{STEAM_OPENID_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=auth_url)

@steam_router.get("/steam/callback")
def steam_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Steam OpenID callback"""
    params = dict(request.query_params)
    
    # Verify Steam OpenID response
    validation_params = {
        "openid.assoc_handle": params.get("openid.assoc_handle"),
        "openid.signed": params.get("openid.signed"),
        "openid.sig": params.get("openid.sig"),
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "check_authentication"
    }
    
    # Add signed params
    signed = params.get("openid.signed", "").split(",")
    for param in signed:
        if param:
            validation_params[f"openid.{param}"] = params.get(f"openid.{param}")
    
    # Verify with Steam
    response = requests.post(STEAM_OPENID_URL, data=validation_params)
    
    if "is_valid:true" not in response.text:
        raise HTTPException(status_code=401, detail="Steam authentication failed")
    
    # Extract Steam ID from claimed_id
    claimed_id = params.get("openid.claimed_id", "")
    steam_id = claimed_id.split("/")[-1]
    
    if not steam_id or not steam_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Steam ID")
    
    # Get user info from Steam API
    user_info = get_steam_user_info(steam_id)
    
    # Check if user exists
    user = db.query(User).filter(User.steam_id == steam_id).first()
    
    if not user:
        # Create new user
        user = User(
            steam_id=steam_id,
            username=user_info.get("personaname", f"user_{steam_id}"),
            avatar=user_info.get("avatarfull", "")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Generate API key for new user
        api_key = ApiKey(
            user_id=user.id,
            key=generate_api_key(),
            name="Default Key"
        )
        db.add(api_key)
        db.commit()
    
    # TODO: Create session/JWT token
    # For now, redirect to frontend with user info
    return {
        "message": "Login successful",
        "user_id": user.id,
        "username": user.username,
        "steam_id": user.steam_id
    }

def get_steam_user_info(steam_id: str):
    """Fetch user info from Steam Web API"""
    url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
    params = {
        "key": STEAM_API_KEY,
        "steamids": steam_id
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        players = data.get("response", {}).get("players", [])
        return players[0] if players else {}
    except Exception as e:
        print(f"Error fetching Steam user info: {e}")
        return {}
